"""
Edit-time re-projection: canonical ``plan_json`` → DB rows, history-safe.

``ingest_from_workbook_json`` is the *first-ingest* projector — it wipes every
``DailyTodo`` for the user, which is correct on initial creation but
catastrophic on an edit (it would destroy months of completion history).

``reproject_plan_from_json`` is the *edit-time* variant. It rebuilds the DB
projection of one existing plan from edited JSON while guaranteeing:

1. **Past is immutable.** ``DailyTodo`` rows with ``date < today`` are never
   deleted or modified. A user's logged history is sacrosanct.
2. **Future is regenerated.** Only ``date >= today`` future rows are dropped,
   then the next 30 days are re-prefilled against the *new* template set.
3. **Today preserved-if-completed.** A ``date == today`` row that the user has
   already completed is kept and re-linked to the matching new template by
   ``task_id``; if the task was deleted it is retained as detached history,
   never deleted (orphan-safe).
4. **Stable identity.** Old↔new tasks are matched by JSON ``task_id`` ==
   ``TaskTemplate.id``. A rename keeps the same ``task_id`` so its history
   stays linked. ``(pillar, name)`` is only a fallback for legacy JSON that
   predates ``task_id``.
5. **Atomic.** The whole operation is one transaction. Any error rolls back so
   the prior plan / templates / todos are exactly as before.

**Tombstone invariant (non-obvious — read before editing).**
``DailyTodo.template_id`` is a NOT-NULL foreign key with no delete cascade, so
a todo can never be truly *orphaned* in the DB. When a task is deleted but it
still has retained history (past rows, or a completed today-row), its
``TaskTemplate`` is kept alive as a *tombstone*: the row stays so its history
FK remains valid, but it is excluded from future-todo generation. The "no
future todos for a deleted task" guarantee therefore comes from how prefill is
driven (only over JSON-derived templates) — never from a DB-level flag.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.constants import DEFAULT_USER_ID
from app.db.models import DailyTodo, Plan, RotationDay, Screening, TaskTemplate
from app.services.plan_ingest import _plan_to_json
from app.services.scheduler import _is_scheduled_today

# Columns on TaskTemplate that are simple scalar copies from a JSON task dict.
_TASK_SCALAR_FIELDS = (
    "pillar",
    "name",
    "description",
    "schedule",
    "timing",
    "target_value",
    "unit",
    "benefit_tags",
    "source_key",
    "link",
    "video_link",
    "safety_notes",
    "how_to",
    "why_mechanism",
)


def _to_json_text(value: object) -> str | None:
    """
    Serialize a lossless catch-all field (``extra_metadata`` / ``exercises_json``)
    for storage. ``_plan_to_json`` parses these back into dict/list, so on the
    way in they normally arrive as structures. Be defensive: if a raw JSON
    string is handed in, do not double-encode it.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _validate_tasks(workbook_json: dict) -> list[dict]:
    """
    Read-only pass 1: validate every JSON task before anything is mutated.

    Raising here guarantees the DB is still pristine (no rollback needed yet).
    Returns the task list on success.
    """
    tasks = workbook_json.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("workbook_json['tasks'] must be a list")

    seen_ids: set[str] = set()
    for idx, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"task #{idx} is not an object")
        name = task.get("name")
        pillar = task.get("pillar")
        if not name or not str(name).strip():
            raise ValueError(f"task #{idx} is missing a non-empty 'name'")
        if not pillar or not str(pillar).strip():
            raise ValueError(f"task #{idx} ('{name}') is missing a non-empty 'pillar'")
        tid = task.get("task_id")
        if tid:
            if tid in seen_ids:
                raise ValueError(f"duplicate task_id '{tid}' in workbook_json")
            seen_ids.add(tid)
    return tasks


def _apply_scalars(tmpl: TaskTemplate, task: dict) -> None:
    """Copy scalar + lossless fields from a JSON task dict onto a template."""
    for field in _TASK_SCALAR_FIELDS:
        if field in task:
            setattr(tmpl, field, task.get(field))
    if "is_reference" in task:
        tmpl.is_reference = bool(task.get("is_reference", False))
    if "extra_metadata" in task:
        tmpl.extra_metadata = _to_json_text(task.get("extra_metadata"))
    if "exercises_json" in task:
        tmpl.exercises_json = _to_json_text(task.get("exercises_json"))


def _resolve_upserts(
    tasks: list[dict],
    existing: dict[str, TaskTemplate],
    by_pillar_name: dict[tuple[str, str], TaskTemplate],
    plan_id: str,
    user_id: str,
    db: Session,
) -> set[str]:
    """
    Pass 2a: update-in-place / insert each JSON task. Returns the set of
    TaskTemplate ids that the new JSON resolves to (the "kept" set).
    """
    kept_ids: set[str] = set()
    for task in tasks:
        tid = task.get("task_id")
        tmpl: TaskTemplate | None = None

        if tid and tid in existing:
            tmpl = existing[tid]
        elif not tid:
            # Legacy fallback only: JSON has no stable id at all.
            tmpl = by_pillar_name.get(
                (str(task.get("pillar")), str(task.get("name")))
            )

        if tmpl is None:
            # New task. Trust an explicit task_id as the PK (handoff contract);
            # otherwise mint one. Guard against colliding with a tombstone id.
            new_id = tid or str(uuid.uuid4())
            if new_id in existing:
                raise ValueError(
                    f"task_id '{new_id}' collides with an existing template"
                )
            tmpl = TaskTemplate(
                id=new_id,
                plan_id=plan_id,
                user_id=user_id,
                pillar=str(task.get("pillar")),
                name=str(task.get("name")),
            )
            db.add(tmpl)

        _apply_scalars(tmpl, task)
        kept_ids.add(tmpl.id)
    return kept_ids


def _regenerate_future_todos(
    db: Session,
    kept_ids: set[str],
    tasks_by_id: dict[str, dict],
    user_id: str,
    today: date,
) -> int:
    """
    Pass 2c: re-prefill the next 30 days.

    Iterates ONLY the JSON-derived (kept, non-reference) templates — never a
    ``TaskTemplate.plan_id == plan_id`` query — so tombstoned deleted tasks
    never get fresh future todos (the tombstone invariant).
    """
    count = 0
    for offset in range(30):
        target = today + timedelta(days=offset)
        for tid in kept_ids:
            task = tasks_by_id.get(tid)
            if task is None:
                continue
            if bool(task.get("is_reference", False)):
                continue
            if _is_scheduled_today(task.get("schedule"), target):
                db.add(
                    DailyTodo(
                        id=str(uuid.uuid4()),
                        template_id=tid,
                        user_id=user_id,
                        date=target,
                        completed=False,
                    )
                )
                count += 1
    return count


def _rebuild_rotation_and_screenings(
    db: Session, plan_id: str, user_id: str, workbook_json: dict
) -> None:
    """
    Full replace of RotationDay + Screening. These carry no per-day user
    history (RotationCompletion / ScreeningRecord are separate tables keyed by
    date, not by these rows' identity), so a clean rebuild is safe.
    """
    db.query(RotationDay).filter(RotationDay.plan_id == plan_id).delete(
        synchronize_session=False
    )
    db.query(Screening).filter(Screening.plan_id == plan_id).delete(
        synchronize_session=False
    )
    db.flush()

    for rd in workbook_json.get("rotation_days", []):
        db.add(
            RotationDay(
                plan_id=plan_id,
                user_id=user_id,
                day_number=rd.get("day_number", 1),
                week_number=rd.get("week_number"),
                block_name=rd.get("block_name", ""),
                warm_up=rd.get("warm_up"),
                priority_block=rd.get("priority_block"),
                secondary_block=rd.get("secondary_block"),
                cardio_steps=rd.get("cardio_steps"),
                cool_down=rd.get("cool_down"),
                nutrition_focus=rd.get("nutrition_focus"),
                intensity_cap=rd.get("intensity_cap"),
                source_key=rd.get("source_key"),
                sets=rd.get("sets"),
                reps=rd.get("reps"),
                duration=rd.get("duration"),
                notes=rd.get("notes"),
                morning_time=rd.get("morning_time"),
                warm_up_min=rd.get("warm_up_min"),
                upper_back_core_min=rd.get("upper_back_core_min"),
                secondary_min=rd.get("secondary_min"),
                cool_down_min=rd.get("cool_down_min"),
                total_min=rd.get("total_min"),
                fits_60=rd.get("fits_60"),
                priority_exercises=rd.get("priority_exercises"),
                secondary_exercises=rd.get("secondary_exercises"),
                week_rule=rd.get("week_rule"),
                extra_metadata=_to_json_text(rd.get("extra_metadata")),
            )
        )

    for sc in workbook_json.get("screenings", []):
        db.add(
            Screening(
                plan_id=plan_id,
                user_id=user_id,
                pillar=sc.get("pillar", "screenings_safety"),
                name=sc.get("name", ""),
                description=sc.get("description"),
                frequency_months=sc.get("frequency_months"),
                target_value=sc.get("target_value"),
                extra_metadata=_to_json_text(sc.get("extra_metadata")),
            )
        )


def reproject_plan_from_json(
    plan_id: str,
    workbook_json: dict,
    db: Session,
    user_id: str = DEFAULT_USER_ID,
) -> dict:
    """
    Rebuild the DB projection of an existing plan from edited canonical JSON
    without destroying completion history. See the module docstring for the
    five history-safety rules this function enforces.

    Returns ``{"plan_id", "tasks", "future_todos"}``.

    Raises ``ValueError`` on malformed JSON (caller should surface 422). On any
    error the transaction is rolled back; the plan is exactly as before.
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).one_or_none()
    if plan is None:
        raise ValueError(f"plan '{plan_id}' not found")

    # ── Pass 1: validate everything before a single mutation ──────────────
    tasks = _validate_tasks(workbook_json)
    tasks_by_id: dict[str, dict] = {}

    try:
        existing_list = (
            db.query(TaskTemplate)
            .filter(TaskTemplate.plan_id == plan_id)
            .all()
        )
        existing: dict[str, TaskTemplate] = {t.id: t for t in existing_list}
        by_pillar_name: dict[tuple[str, str], TaskTemplate] = {
            (t.pillar, t.name): t for t in existing_list
        }

        # ── Pass 2a: upsert tasks from JSON ───────────────────────────────
        kept_ids = _resolve_upserts(
            tasks, existing, by_pillar_name, plan_id, user_id, db
        )
        db.flush()

        # tasks_by_id maps a *kept* template id → its JSON dict (for prefill).
        for task in tasks:
            tid = task.get("task_id")
            if tid and tid in kept_ids:
                tasks_by_id[tid] = task
        # New rows (id minted in _resolve_upserts) — re-derive their mapping.
        for tmpl in db.query(TaskTemplate).filter(
            TaskTemplate.plan_id == plan_id
        ):
            if tmpl.id in kept_ids and tmpl.id not in tasks_by_id:
                # Match back to the JSON task by (pillar, name) for new rows.
                for task in tasks:
                    if (
                        not task.get("task_id")
                        and str(task.get("pillar")) == tmpl.pillar
                        and str(task.get("name")) == tmpl.name
                    ):
                        tasks_by_id[tmpl.id] = task
                        break

        today = date.today()

        # ── Pass 2b: drop ONLY future + non-completed-today todos ─────────
        # Past (date < today) is never touched (rule 1). A completed today-row
        # is kept (rule 3). Everything else from today forward is regenerated.
        all_plan_template_ids = [t.id for t in existing_list] + [
            tid for tid in kept_ids if tid not in existing
        ]
        if all_plan_template_ids:
            future_todos = (
                db.query(DailyTodo)
                .filter(
                    DailyTodo.template_id.in_(all_plan_template_ids),
                    DailyTodo.date >= today,
                )
                .all()
            )
            for todo in future_todos:
                if todo.date == today and todo.completed:
                    # Rule 3: keep completed today-rows. Re-link to the
                    # matching new template by task_id if it survived;
                    # otherwise leave it pointing at the (tombstoned)
                    # template — retained history, never deleted.
                    continue
                db.delete(todo)
            db.flush()

        # ── Pass 2c: regenerate the next 30 days from the new task set ────
        future_count = _regenerate_future_todos(
            db, kept_ids, tasks_by_id, user_id, today
        )

        # ── Pass 2d: delete templates absent from new JSON, unless they
        # still carry retained history (tombstone invariant) ─────────────
        tombstone_ids: set[str] = set()
        for tid, tmpl in existing.items():
            if tid in kept_ids:
                continue
            remaining = (
                db.query(DailyTodo)
                .filter(DailyTodo.template_id == tid)
                .count()
            )
            if remaining == 0:
                db.delete(tmpl)
            else:
                # Keep as tombstone — its history FK stays valid and it is
                # NOT in kept_ids so it generated no future todos. It must
                # also be invisible to the canonical JSON (rule 4): a
                # deleted task must not reappear on the next edit.
                tombstone_ids.add(tid)
        db.flush()

        # ── Pass 2e: rebuild rotation + screenings (no per-day history) ───
        _rebuild_rotation_and_screenings(db, plan_id, user_id, workbook_json)
        db.flush()

        # ── Pass 2f: re-serialize canonical JSON from the new DB state and
        # bump the concurrency guard, all in this one transaction.
        # _plan_to_json queries every TaskTemplate for the plan, which
        # includes tombstones; strip them so a deleted-with-history task
        # does NOT resurface in plan_json on the next edit (rule 4). ──────
        serialized = _plan_to_json(db, plan_id)
        if tombstone_ids:
            serialized["tasks"] = [
                t for t in serialized["tasks"]
                if t.get("task_id") not in tombstone_ids
            ]
        plan.plan_json = json.dumps(serialized)
        plan.json_version = (plan.json_version or 1) + 1
        db.flush()

        # kept_ids is exactly the JSON-resolved template set (tombstones are
        # deliberately excluded — they are retained history, not live tasks).
        task_count = len(kept_ids)

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "plan_id": plan_id,
        "tasks": task_count,
        "future_todos": future_count,
    }
