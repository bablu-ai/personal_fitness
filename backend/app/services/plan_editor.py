"""
Plan editor service — the ONLY writer of Plan.plan_json outside of ingest.

All mutations:
  1. Load Plan → 404 if missing
  2. Version-guard check → 409 if stale
  3. Parse plan_json → mutate dict → write plan_json back
  4. Call reproject_plan_from_json (except flag ops — see note below)
  5. Return typed response model

**json_version invariant**
``reproject_plan_from_json`` bumps ``plan.json_version`` after every reproject.
Flag operations (apply/dismiss) skip reproject and must bump the version manually.

**Dismissed-flag persistence**
``review_workbook_json`` regenerates Tier-B flags deterministically on every call,
so a flag dismissed in one session would reappear on the next GET /review unless
we record it.  We store dismissed flag IDs in
``plan_json["review"]["dismissed_flag_ids"]`` and filter them out in
``get_plan_review``.

**origin tracking**
``_plan_to_json`` does not emit the ``origin`` column, and ``_apply_scalars``
in plan_reproject.py does not copy it either.  After reproject we patch the DB
row directly so the column stays in sync.

TODO[SECURITY]: In Phase 2, add user_id ownership check on every plan load
(plan.user_id == current_user.id) instead of the DEFAULT_USER_ID shortcut.
"""
from __future__ import annotations

import json
import uuid
from collections import defaultdict
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.constants import DEFAULT_USER_ID
from app.db.models import Plan, RotationDay, Screening, TaskTemplate
from app.schemas.plan_edit import (
    ActivateOut,
    FlagActionOut,
    PlanReviewOut,
    ReviewEnvelope,
    ReviewFlag,
    RotationDayOut,
    RotationDayUpsert,
    ScreeningOut,
    ScreeningUpsert,
    TaskOut,
    TaskUpsert,
)
from app.services.plan_reproject import reproject_plan_from_json
from app.services.plan_reviewer import review_workbook_json


# ── Internal helpers ──────────────────────────────────────────────────────────


def _load_plan(plan_id: str, db: Session) -> Plan:
    """Load a Plan by id; raise 404 if absent."""
    plan = db.query(Plan).filter(Plan.id == plan_id).one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found")
    return plan


def _version_guard(plan: Plan, base_version: int) -> None:
    """Raise 409 if the caller's base version is stale."""
    if plan.json_version != base_version:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "stale_version",
                "current": plan.json_version,
            },
        )


def _parse_plan_json(plan: Plan) -> dict[str, Any]:
    """Parse plan_json; return {} for null / empty / invalid JSON."""
    raw = plan.plan_json
    if not raw or not raw.strip() or raw.strip() in ("{}", ""):
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _task_out_from_row(tmpl: TaskTemplate) -> TaskOut:
    """Build a TaskOut from a DB row."""
    return TaskOut(
        task_id=tmpl.id,
        plan_id=tmpl.plan_id,
        pillar=tmpl.pillar,
        name=tmpl.name,
        description=tmpl.description,
        schedule=tmpl.schedule,
        timing=tmpl.timing,
        target_value=tmpl.target_value,
        unit=tmpl.unit,
        benefit_tags=tmpl.benefit_tags,
        source_key=tmpl.source_key,
        link=tmpl.link,
        video_link=tmpl.video_link,
        safety_notes=tmpl.safety_notes,
        how_to=tmpl.how_to,
        why_mechanism=tmpl.why_mechanism,
        is_reference=bool(tmpl.is_reference),
        origin=tmpl.origin or "ingest",
    )


def _rotation_out_from_row(rd: RotationDay) -> RotationDayOut:
    """Build a RotationDayOut from a DB row."""
    return RotationDayOut(
        id=rd.id,
        plan_id=rd.plan_id,
        day_number=rd.day_number,
        week_number=rd.week_number,
        block_name=rd.block_name,
        morning_time=rd.morning_time,
        warm_up_min=rd.warm_up_min,
        upper_back_core_min=rd.upper_back_core_min,
        secondary_min=rd.secondary_min,
        cool_down_min=rd.cool_down_min,
        total_min=rd.total_min,
        fits_60=rd.fits_60,
        priority_exercises=rd.priority_exercises,
        secondary_exercises=rd.secondary_exercises,
        week_rule=rd.week_rule,
        notes=rd.notes,
    )


def _screening_out_from_row(sc: Screening) -> ScreeningOut:
    """Build a ScreeningOut from a DB row."""
    return ScreeningOut(
        id=sc.id,
        plan_id=sc.plan_id,
        pillar=sc.pillar,
        name=sc.name,
        description=sc.description,
        frequency_months=sc.frequency_months,
        target_value=sc.target_value,
    )


def _build_review_envelope(
    reviewed: dict[str, Any],
    dismissed_flag_ids: set[str],
) -> ReviewEnvelope:
    """Convert the raw review dict from plan_reviewer into a ReviewEnvelope.

    Filters out any flags whose flag_id is in dismissed_flag_ids so dismissed
    flags do not reappear after the next GET /review.
    """
    review_raw = reviewed.get("review", {})
    raw_flags: list[dict] = review_raw.get("flags", [])

    flags: list[ReviewFlag] = []
    for f in raw_flags:
        fid = f.get("flag_id", "")
        if fid in dismissed_flag_ids:
            continue
        flags.append(ReviewFlag(
            flag_id=fid,
            task_id=f.get("task_id"),
            code=f.get("code", ""),
            message=f.get("message", ""),
            suggestion=f.get("suggestion"),
            blocking=bool(f.get("blocking", False)),
        ))

    return ReviewEnvelope(
        auto_removed=review_raw.get("auto_removed", []),
        agent_fixed=review_raw.get("agent_fixed", []),
        flags=flags,
        advisor_notes=review_raw.get("advisor_notes", []),
    )


def _get_dismissed_ids(workbook_json: dict[str, Any]) -> set[str]:
    """Read the persisted dismissed_flag_ids list from plan_json."""
    review = workbook_json.get("review", {})
    if not isinstance(review, dict):
        return set()
    dismissed = review.get("dismissed_flag_ids", [])
    if not isinstance(dismissed, list):
        return set()
    return set(dismissed)


def _apply_task_upsert_to_json(
    task_dict: dict[str, Any],
    payload: TaskUpsert,
    *,
    origin: str,
) -> dict[str, Any]:
    """Merge a TaskUpsert payload into a task dict (in-place, returns same dict)."""
    task_dict["name"] = payload.name
    task_dict["pillar"] = payload.pillar
    task_dict["description"] = payload.description
    task_dict["schedule"] = payload.schedule
    task_dict["timing"] = payload.timing
    task_dict["target_value"] = payload.target_value
    task_dict["unit"] = payload.unit
    task_dict["benefit_tags"] = payload.benefit_tags
    task_dict["source_key"] = payload.source_key
    task_dict["link"] = payload.link
    task_dict["video_link"] = payload.video_link
    task_dict["safety_notes"] = payload.safety_notes
    task_dict["how_to"] = payload.how_to
    task_dict["why_mechanism"] = payload.why_mechanism
    task_dict["is_reference"] = payload.is_reference
    task_dict["origin"] = origin
    return task_dict


# ── Public service functions ──────────────────────────────────────────────────


def get_plan_review(plan_id: str, db: Session) -> PlanReviewOut:
    """Return the full plan review for the editor UI.

    Steps:
    1. Load Plan → 404 if missing
    2. Parse plan_json (empty dict if null/empty/invalid)
    3. Run review_workbook_json to get live flags
    4. Filter dismissed flags
    5. Group tasks by pillar
    6. Load rotation_days and screenings from DB (source of truth post-reproject)
    7. Build PlanReviewOut
    """
    plan = _load_plan(plan_id, db)
    workbook_json = _parse_plan_json(plan)
    dismissed_ids = _get_dismissed_ids(workbook_json)

    reviewed = review_workbook_json(workbook_json)

    # Group tasks from reviewed JSON by pillar
    tasks_by_pillar: dict[str, list[TaskOut]] = defaultdict(list)
    for task in reviewed.get("tasks", []):
        task_id = task.get("task_id")
        if not task_id:
            continue
        tmpl = db.query(TaskTemplate).filter(TaskTemplate.id == task_id).one_or_none()
        if tmpl is None:
            continue
        tasks_by_pillar[tmpl.pillar].append(_task_out_from_row(tmpl))

    # Load rotation_days and screenings from DB
    rotation_rows = (
        db.query(RotationDay)
        .filter(RotationDay.plan_id == plan_id)
        .order_by(RotationDay.day_number, RotationDay.id)
        .all()
    )
    screening_rows = (
        db.query(Screening)
        .filter(Screening.plan_id == plan_id)
        .order_by(Screening.id)
        .all()
    )

    review_envelope = _build_review_envelope(reviewed, dismissed_ids)

    return PlanReviewOut(
        plan_id=plan_id,
        status=plan.status,
        json_version=plan.json_version,
        tasks_by_pillar=dict(tasks_by_pillar),
        rotation_days=[_rotation_out_from_row(rd) for rd in rotation_rows],
        screenings=[_screening_out_from_row(sc) for sc in screening_rows],
        review=review_envelope,
    )


def add_task(
    plan_id: str,
    payload: TaskUpsert,
    base_version: int,
    db: Session,
) -> TaskOut:
    """Add a new task to the plan and reproject.

    Steps:
    1. Version guard → 409 if stale
    2. Parse plan_json
    3. Mint new task_id = str(uuid4())
    4. Append task dict to tasks[]
    5. Write plan_json back
    6. Reproject (bumps json_version, syncs DB rows)
    7. Patch origin on the newly created DB row
    8. Return TaskOut built from DB row
    """
    plan = _load_plan(plan_id, db)
    _version_guard(plan, base_version)

    workbook_json = _parse_plan_json(plan)
    tasks = workbook_json.setdefault("tasks", [])

    new_id = str(uuid.uuid4())
    task_dict: dict[str, Any] = {"task_id": new_id}
    _apply_task_upsert_to_json(task_dict, payload, origin="user_added")
    tasks.append(task_dict)

    plan.plan_json = json.dumps(workbook_json)
    db.flush()

    reproject_plan_from_json(plan_id, workbook_json, db, DEFAULT_USER_ID)

    # Patch origin — _plan_to_json does not emit origin, _apply_scalars doesn't copy it
    db.query(TaskTemplate).filter(TaskTemplate.id == new_id).update({"origin": "user_added"})
    db.commit()

    tmpl = db.query(TaskTemplate).filter(TaskTemplate.id == new_id).one_or_none()
    if tmpl is None:
        raise HTTPException(status_code=500, detail="Task was not persisted after reproject")
    return _task_out_from_row(tmpl)


def update_task(
    plan_id: str,
    task_id: str,
    payload: TaskUpsert,
    base_version: int,
    db: Session,
) -> TaskOut:
    """Update an existing task in the plan and reproject.

    Steps:
    1. Version guard → 409 if stale
    2. Find task by task_id in plan_json["tasks"] → 404 if absent
    3. Merge fields (origin → "user_edited")
    4. Write plan_json back
    5. Reproject
    6. Patch origin on the DB row
    7. Return TaskOut from DB row
    """
    plan = _load_plan(plan_id, db)
    _version_guard(plan, base_version)

    workbook_json = _parse_plan_json(plan)
    tasks = workbook_json.get("tasks", [])

    task_dict: dict[str, Any] | None = None
    for t in tasks:
        if t.get("task_id") == task_id:
            task_dict = t
            break

    if task_dict is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found in plan '{plan_id}'")

    _apply_task_upsert_to_json(task_dict, payload, origin="user_edited")

    plan.plan_json = json.dumps(workbook_json)
    db.flush()

    reproject_plan_from_json(plan_id, workbook_json, db, DEFAULT_USER_ID)

    # Patch origin
    db.query(TaskTemplate).filter(TaskTemplate.id == task_id).update({"origin": "user_edited"})
    db.commit()

    tmpl = db.query(TaskTemplate).filter(TaskTemplate.id == task_id).one_or_none()
    if tmpl is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found after reproject")
    return _task_out_from_row(tmpl)


def delete_task(
    plan_id: str,
    task_id: str,
    base_version: int,
    db: Session,
) -> None:
    """Remove a task from the plan and reproject.

    Past DailyTodo rows are preserved (tombstone invariant in plan_reproject).
    """
    plan = _load_plan(plan_id, db)
    _version_guard(plan, base_version)

    workbook_json = _parse_plan_json(plan)
    tasks = workbook_json.get("tasks", [])

    original_count = len(tasks)
    workbook_json["tasks"] = [t for t in tasks if t.get("task_id") != task_id]

    if len(workbook_json["tasks"]) == original_count:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found in plan '{plan_id}'")

    plan.plan_json = json.dumps(workbook_json)
    db.flush()

    reproject_plan_from_json(plan_id, workbook_json, db, DEFAULT_USER_ID)


def update_rotation_day(
    plan_id: str,
    day_number: int,
    payload: RotationDayUpsert,
    base_version: int,
    db: Session,
) -> RotationDayOut:
    """Upsert a rotation day in the plan's JSON then reproject."""
    plan = _load_plan(plan_id, db)
    _version_guard(plan, base_version)

    workbook_json = _parse_plan_json(plan)
    rotation_days: list[dict] = workbook_json.setdefault("rotation_days", [])

    # Find existing day or build a new dict
    day_dict: dict[str, Any] | None = None
    for rd in rotation_days:
        if rd.get("day_number") == day_number:
            day_dict = rd
            break

    if day_dict is None:
        day_dict = {"day_number": day_number}
        rotation_days.append(day_dict)

    # Merge payload (exclude day_number which is the PK)
    day_dict["day_number"] = day_number
    if payload.block_name is not None:
        day_dict["block_name"] = payload.block_name
    if payload.week_number is not None:
        day_dict["week_number"] = payload.week_number
    if payload.morning_time is not None:
        day_dict["morning_time"] = payload.morning_time
    if payload.warm_up_min is not None:
        day_dict["warm_up_min"] = payload.warm_up_min
    if payload.upper_back_core_min is not None:
        day_dict["upper_back_core_min"] = payload.upper_back_core_min
    if payload.secondary_min is not None:
        day_dict["secondary_min"] = payload.secondary_min
    if payload.cool_down_min is not None:
        day_dict["cool_down_min"] = payload.cool_down_min
    if payload.total_min is not None:
        day_dict["total_min"] = payload.total_min
    if payload.fits_60 is not None:
        day_dict["fits_60"] = payload.fits_60
    if payload.priority_exercises is not None:
        day_dict["priority_exercises"] = payload.priority_exercises
    if payload.secondary_exercises is not None:
        day_dict["secondary_exercises"] = payload.secondary_exercises
    if payload.week_rule is not None:
        day_dict["week_rule"] = payload.week_rule
    if payload.notes is not None:
        day_dict["notes"] = payload.notes

    plan.plan_json = json.dumps(workbook_json)
    db.flush()

    reproject_plan_from_json(plan_id, workbook_json, db, DEFAULT_USER_ID)

    # Load the newly-projected row from DB
    rd_row = (
        db.query(RotationDay)
        .filter(RotationDay.plan_id == plan_id, RotationDay.day_number == day_number)
        .first()
    )
    if rd_row is None:
        raise HTTPException(status_code=500, detail="Rotation day not persisted after reproject")
    return _rotation_out_from_row(rd_row)


def update_screening(
    plan_id: str,
    screening_id: str,
    payload: ScreeningUpsert,
    base_version: int,
    db: Session,
) -> ScreeningOut:
    """Upsert a screening in the plan's JSON then reproject.

    Screenings in plan_json are keyed by ``id`` field (set by the reviewer
    during plan_to_json serialization via Screening.id in DB).
    """
    plan = _load_plan(plan_id, db)
    _version_guard(plan, base_version)

    # Verify screening belongs to this plan
    sc_row = (
        db.query(Screening)
        .filter(Screening.id == screening_id, Screening.plan_id == plan_id)
        .one_or_none()
    )
    if sc_row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Screening '{screening_id}' not found in plan '{plan_id}'",
        )

    workbook_json = _parse_plan_json(plan)
    screenings: list[dict] = workbook_json.setdefault("screenings", [])

    # Find existing screening by id field in JSON (if present), else match by name+pillar
    sc_dict: dict[str, Any] | None = None
    for sc in screenings:
        if sc.get("id") == screening_id:
            sc_dict = sc
            break

    if sc_dict is None:
        # Fallback: match by original name/pillar or append new
        sc_dict = {
            "id": screening_id,
            "pillar": sc_row.pillar,
            "name": sc_row.name,
        }
        screenings.append(sc_dict)

    # Merge payload
    sc_dict["name"] = payload.name
    sc_dict["pillar"] = payload.pillar
    if payload.description is not None:
        sc_dict["description"] = payload.description
    if payload.frequency_months is not None:
        sc_dict["frequency_months"] = payload.frequency_months
    if payload.target_value is not None:
        sc_dict["target_value"] = payload.target_value

    plan.plan_json = json.dumps(workbook_json)
    db.flush()

    reproject_plan_from_json(plan_id, workbook_json, db, DEFAULT_USER_ID)

    # After reproject, find the screening by (pillar, name) since id may regenerate
    updated = (
        db.query(Screening)
        .filter(
            Screening.plan_id == plan_id,
            Screening.name == payload.name,
            Screening.pillar == payload.pillar,
        )
        .first()
    )
    if updated is None:
        updated = (
            db.query(Screening)
            .filter(Screening.plan_id == plan_id)
            .first()
        )
    if updated is None:
        raise HTTPException(status_code=500, detail="Screening not found after reproject")
    return _screening_out_from_row(updated)


def apply_flag(
    plan_id: str,
    flag_id: str,
    base_version: int,
    db: Session,
) -> FlagActionOut:
    """Apply a reviewer flag's suggestion to plan_json.

    Actionable codes (mutate plan_json):
    - name_is_dosage: set task["name"] = flag["suggestion"]
    - pillar_mismatch: set task["pillar"] = flag["suggestion"]
    - suspicious_reference: toggle task["is_reference"] to flag["suggestion"]

    All other codes are advisory (no mutation). All codes add the flag_id to
    dismissed_flag_ids so it doesn't reappear on GET /review.

    Bumps json_version manually (no reproject for advisory codes, but we
    reproject for codes that mutate task DB columns so the DB stays in sync).
    """
    plan = _load_plan(plan_id, db)
    _version_guard(plan, base_version)

    workbook_json = _parse_plan_json(plan)

    # Run reviewer to find the live flag (needed for its suggestion value)
    reviewed = review_workbook_json(workbook_json)
    flags_raw: list[dict] = reviewed.get("review", {}).get("flags", [])

    matching_flag: dict[str, Any] | None = None
    for f in flags_raw:
        if f.get("flag_id") == flag_id:
            matching_flag = f
            break

    # Persist dismissed_flag_ids regardless of whether flag currently exists
    review = workbook_json.setdefault("review", {})
    if not isinstance(review, dict):
        review = {}
        workbook_json["review"] = review
    dismissed: list[str] = review.setdefault("dismissed_flag_ids", [])
    if not isinstance(dismissed, list):
        dismissed = []
        review["dismissed_flag_ids"] = dismissed
    if flag_id not in dismissed:
        dismissed.append(flag_id)

    needs_reproject = False

    if matching_flag is not None:
        code = matching_flag.get("code", "")
        suggestion = matching_flag.get("suggestion")
        task_id = matching_flag.get("task_id")

        tasks: list[dict] = workbook_json.get("tasks", [])

        if code == "name_is_dosage" and suggestion and task_id:
            for t in tasks:
                if t.get("task_id") == task_id:
                    t["name"] = str(suggestion)
                    needs_reproject = True
                    break

        elif code == "pillar_mismatch" and suggestion and task_id:
            for t in tasks:
                if t.get("task_id") == task_id:
                    t["pillar"] = str(suggestion)
                    needs_reproject = True
                    break

        elif code == "suspicious_reference" and task_id:
            for t in tasks:
                if t.get("task_id") == task_id:
                    t["is_reference"] = bool(suggestion)
                    needs_reproject = True
                    break

        # Advisory codes (missing_description, empty_target, etc.) — no mutation

    plan.plan_json = json.dumps(workbook_json)
    db.flush()

    if needs_reproject:
        reproject_plan_from_json(plan_id, workbook_json, db, DEFAULT_USER_ID)
        # Re-load plan to get the bumped version written by reproject
        db.refresh(plan)
        # Re-persist dismissed_flag_ids since reproject re-serialized plan_json
        wj = _parse_plan_json(plan)
        rev = wj.setdefault("review", {})
        dis = rev.setdefault("dismissed_flag_ids", [])
        if flag_id not in dis:
            dis.append(flag_id)
        plan.plan_json = json.dumps(wj)
        db.flush()
        db.commit()
    else:
        # Bump version manually (no reproject path)
        plan.json_version = (plan.json_version or 1) + 1
        db.commit()

    return FlagActionOut(plan_id=plan_id, flag_id=flag_id, action="applied")


def dismiss_flag(
    plan_id: str,
    flag_id: str,
    base_version: int,
    db: Session,
) -> FlagActionOut:
    """Remove a flag from review display without applying its suggestion.

    Adds flag_id to dismissed_flag_ids and bumps json_version.
    """
    plan = _load_plan(plan_id, db)
    _version_guard(plan, base_version)

    workbook_json = _parse_plan_json(plan)

    review = workbook_json.setdefault("review", {})
    if not isinstance(review, dict):
        review = {}
        workbook_json["review"] = review
    dismissed: list[str] = review.setdefault("dismissed_flag_ids", [])
    if not isinstance(dismissed, list):
        dismissed = []
        review["dismissed_flag_ids"] = dismissed
    if flag_id not in dismissed:
        dismissed.append(flag_id)

    plan.plan_json = json.dumps(workbook_json)
    plan.json_version = (plan.json_version or 1) + 1
    db.commit()

    return FlagActionOut(plan_id=plan_id, flag_id=flag_id, action="dismissed")


def activate_plan(
    plan_id: str,
    base_version: int,
    db: Session,
) -> ActivateOut:
    """Transition plan from draft to active.

    Steps:
    1. Version guard → 409 if stale
    2. get_plan_review → 409 if any blocking flags remain
    3. Archive prior active plans for same user
    4. Set plan.status='active', plan.is_active=True
    5. reproject_plan_from_json (ensures fresh future todos on activation)
    6. Return ActivateOut
    """
    plan = _load_plan(plan_id, db)
    _version_guard(plan, base_version)

    # Check for blocking flags
    review_out = get_plan_review(plan_id, db)
    blocking = [f for f in review_out.review.flags if f.blocking]
    if blocking:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "blocking_flags",
                "flags": [f.flag_id for f in blocking],
            },
        )

    # Archive any currently active plans for this user
    db.query(Plan).filter(
        Plan.user_id == plan.user_id,
        Plan.is_active == True,  # noqa: E712
        Plan.id != plan_id,
    ).update({"is_active": False, "status": "archived"})
    db.flush()

    # Activate this plan
    plan.status = "active"
    plan.is_active = True
    db.flush()

    # Reproject to ensure future todos are fresh
    workbook_json = _parse_plan_json(plan)
    reproject_plan_from_json(plan_id, workbook_json, db, DEFAULT_USER_ID)

    return ActivateOut(plan_id=plan_id, status="active")
