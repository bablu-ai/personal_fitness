"""
Tests for ``reproject_plan_from_json`` — the history-safe edit-time projector.

DB isolation: reuses conftest's ``db_session`` fixture (a fresh connection-
scoped in-memory SQLite per test). No shared .env / longevity.db is touched.
"""
import json
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.db.models import DailyTodo, Plan, RotationDay, Screening, TaskTemplate
from app.services.plan_reproject import reproject_plan_from_json

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)


# ── Builders ──────────────────────────────────────────────────────────────


def _make_plan(db, *, json_version=1):
    plan = Plan(id=str(uuid.uuid4()), name="Test Plan", user_id="default",
                is_active=True, json_version=json_version, plan_json="{}")
    db.add(plan)
    db.flush()
    return plan


def _make_task(db, plan, *, name, pillar="brief_today", schedule="daily",
               task_id=None, unit=None, extra_metadata=None,
               exercises_json=None, is_reference=False):
    t = TaskTemplate(
        id=task_id or str(uuid.uuid4()),
        plan_id=plan.id, user_id="default", name=name, pillar=pillar,
        schedule=schedule, unit=unit, is_reference=is_reference,
        extra_metadata=json.dumps(extra_metadata) if extra_metadata else None,
        exercises_json=json.dumps(exercises_json) if exercises_json else None,
    )
    db.add(t)
    db.flush()
    return t


def _make_todo(db, tmpl, *, on, completed=False, notes=None, actual=None):
    todo = DailyTodo(
        id=str(uuid.uuid4()), template_id=tmpl.id, user_id="default",
        date=on, completed=completed,
        completed_at=datetime.now(timezone.utc) if completed else None,
        actual_value=actual, notes=notes,
    )
    db.add(todo)
    db.flush()
    return todo


def _task_json(t, **overrides):
    base = {
        "task_id": t.id, "pillar": t.pillar, "name": t.name,
        "schedule": t.schedule, "is_reference": t.is_reference,
        "unit": t.unit,
        "extra_metadata": json.loads(t.extra_metadata) if t.extra_metadata else {},
        "exercises_json": json.loads(t.exercises_json) if t.exercises_json else [],
    }
    base.update(overrides)
    return base


def _wb(tasks, rotation_days=None, screenings=None):
    return {
        "format_version": "upload_v2",
        "tasks": tasks,
        "rotation_days": rotation_days or [],
        "screenings": screenings or [],
    }


# ── Rule 1: past is immutable ─────────────────────────────────────────────


def test_past_todos_preserved_byte_for_byte(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(db, plan, name="Walk")
    past = _make_todo(db, t, on=YESTERDAY, completed=True,
                      notes="felt great", actual="30 min")
    past_id = past.id
    db.commit()

    reproject_plan_from_json(plan.id, _wb([_task_json(t)]), db)

    kept = db.query(DailyTodo).filter(DailyTodo.id == past_id).one()
    assert kept.completed is True
    assert kept.notes == "felt great"
    assert kept.actual_value == "30 min"
    assert kept.date == YESTERDAY
    assert kept.template_id == t.id


# ── Rule 2: future is regenerated ─────────────────────────────────────────


def test_future_todos_regenerated_for_new_schedule(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(db, plan, name="Walk", schedule="daily")
    # Pre-existing stale future rows.
    for off in range(5):
        _make_todo(db, t, on=TODAY + timedelta(days=off))
    db.commit()

    # Edit schedule to weekly — far fewer future rows expected.
    res = reproject_plan_from_json(
        plan.id, _wb([_task_json(t, schedule="weekly")]), db
    )

    future = (
        db.query(DailyTodo)
        .filter(DailyTodo.template_id == t.id, DailyTodo.date >= TODAY)
        .all()
    )
    # weekly = only Mondays in the next 30 days (4 or 5), far fewer than 30.
    assert all(d.date.weekday() == 0 for d in future)
    assert len(future) == res["future_todos"]
    assert all(not d.completed for d in future)


def test_no_future_rows_left_for_old_template_set(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(db, plan, name="Walk", schedule="daily")
    db.commit()
    reproject_plan_from_json(plan.id, _wb([_task_json(t)]), db)
    future = (
        db.query(DailyTodo)
        .filter(DailyTodo.template_id == t.id, DailyTodo.date >= TODAY)
        .count()
    )
    assert future == 30  # daily, 30-day horizon


# ── Rule 3 + 4: rename keeps completed-today linked ───────────────────────


def test_rename_keeps_completed_today_linked_not_duplicated(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(db, plan, name="Old Name", schedule="daily")
    done = _make_todo(db, t, on=TODAY, completed=True, notes="done early")
    done_id = done.id
    db.commit()

    reproject_plan_from_json(
        plan.id, _wb([_task_json(t, name="New Name")]), db
    )

    # Same task_id row, renamed.
    tmpl = db.query(TaskTemplate).filter(TaskTemplate.id == t.id).one()
    assert tmpl.name == "New Name"

    # The completed today-todo survives, still linked, not duplicated.
    today_rows = (
        db.query(DailyTodo)
        .filter(DailyTodo.template_id == t.id, DailyTodo.date == TODAY)
        .all()
    )
    completed_rows = [r for r in today_rows if r.completed]
    assert len(completed_rows) == 1
    assert completed_rows[0].id == done_id
    assert completed_rows[0].notes == "done early"


# ── Rule 4: delete task with past history ─────────────────────────────────


def test_delete_task_retains_past_history_no_future(db_session):
    db = db_session
    plan = _make_plan(db)
    keep = _make_task(db, plan, name="Keep", schedule="daily")
    gone = _make_task(db, plan, name="Gone", schedule="daily")
    hist = _make_todo(db, gone, on=YESTERDAY, completed=True, notes="legacy")
    hist_id = hist.id
    _make_todo(db, gone, on=TODAY + timedelta(days=2))  # stale future
    db.commit()

    reproject_plan_from_json(plan.id, _wb([_task_json(keep)]), db)

    # Past history row retained (tombstone template kept alive for FK).
    survived = db.query(DailyTodo).filter(DailyTodo.id == hist_id).one()
    assert survived.completed is True
    assert survived.notes == "legacy"
    # No future rows for the deleted task.
    fut = (
        db.query(DailyTodo)
        .filter(DailyTodo.template_id == gone.id, DailyTodo.date >= TODAY)
        .count()
    )
    assert fut == 0
    # The kept task got fresh future rows.
    assert (
        db.query(DailyTodo)
        .filter(DailyTodo.template_id == keep.id, DailyTodo.date >= TODAY)
        .count()
        == 30
    )
    # Rule 4 at the JSON view layer: the tombstoned (deleted-with-history)
    # task must NOT resurface in canonical plan_json, or it would reappear
    # on the next edit.
    serialized = json.loads(
        db.query(Plan).filter(Plan.id == plan.id).one().plan_json
    )
    assert all(t["task_id"] != gone.id for t in serialized["tasks"])
    assert any(t["task_id"] == keep.id for t in serialized["tasks"])


def test_delete_task_with_no_history_is_hard_deleted(db_session):
    db = db_session
    plan = _make_plan(db)
    keep = _make_task(db, plan, name="Keep")
    gone = _make_task(db, plan, name="Gone")  # no todos at all
    gone_id = gone.id
    db.commit()

    reproject_plan_from_json(plan.id, _wb([_task_json(keep)]), db)

    assert (
        db.query(TaskTemplate).filter(TaskTemplate.id == gone_id).count() == 0
    )


# ── New task in JSON ──────────────────────────────────────────────────────


def test_new_task_gets_fresh_future_todos(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(db, plan, name="Existing", schedule="daily")
    db.commit()

    new_id = str(uuid.uuid4())
    new_task = {
        "task_id": new_id, "pillar": "supplements", "name": "Creatine",
        "schedule": "daily", "is_reference": False,
    }
    res = reproject_plan_from_json(
        plan.id, _wb([_task_json(t), new_task]), db
    )

    assert (
        db.query(TaskTemplate).filter(TaskTemplate.id == new_id).one().name
        == "Creatine"
    )
    assert (
        db.query(DailyTodo)
        .filter(DailyTodo.template_id == new_id, DailyTodo.date >= TODAY)
        .count()
        == 30
    )
    assert res["tasks"] == 2


def test_reference_task_gets_no_future_todos(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(db, plan, name="Ref", is_reference=True, schedule="daily")
    db.commit()
    reproject_plan_from_json(plan.id, _wb([_task_json(t)]), db)
    assert (
        db.query(DailyTodo).filter(DailyTodo.template_id == t.id).count() == 0
    )


# ── Lossless round trip ───────────────────────────────────────────────────


def test_lossless_fields_survive_json_db_roundtrip(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(
        db, plan, name="Bench", unit="kg",
        extra_metadata={"status": "Active", "category": "B"},
        exercises_json=[{"name": "Bench Press", "sets": "3", "reps": "8"}],
    )
    db.commit()

    reproject_plan_from_json(plan.id, _wb([_task_json(t)]), db)

    plan_db = db.query(Plan).filter(Plan.id == plan.id).one()
    parsed = json.loads(plan_db.plan_json)
    jt = next(x for x in parsed["tasks"] if x["task_id"] == t.id)
    assert jt["unit"] == "kg"
    assert jt["extra_metadata"] == {"status": "Active", "category": "B"}
    assert jt["exercises_json"] == [
        {"name": "Bench Press", "sets": "3", "reps": "8"}
    ]
    # And the DB row stored them as JSON strings, not double-encoded.
    tmpl = db.query(TaskTemplate).filter(TaskTemplate.id == t.id).one()
    assert json.loads(tmpl.extra_metadata) == {"status": "Active",
                                               "category": "B"}
    assert json.loads(tmpl.exercises_json)[0]["name"] == "Bench Press"


def test_json_version_bumped_and_status_untouched(db_session):
    db = db_session
    plan = _make_plan(db, json_version=3)
    plan.status = "active"
    t = _make_task(db, plan, name="Walk")
    db.commit()

    reproject_plan_from_json(plan.id, _wb([_task_json(t)]), db)

    refreshed = db.query(Plan).filter(Plan.id == plan.id).one()
    assert refreshed.json_version == 4
    assert refreshed.status == "active"  # reproject must NOT change status
    assert refreshed.is_active is True


# ── Rotation + screenings full replace ────────────────────────────────────


def test_rotation_and_screenings_rebuilt(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(db, plan, name="Walk")
    db.add(RotationDay(id=str(uuid.uuid4()), plan_id=plan.id,
                       user_id="default", day_number=99, block_name="OLD"))
    db.add(Screening(id=str(uuid.uuid4()), plan_id=plan.id,
                      user_id="default", pillar="blood_markers", name="OLD"))
    db.commit()

    wb = _wb(
        [_task_json(t)],
        rotation_days=[{"day_number": 1, "block_name": "Push Day"}],
        screenings=[{"pillar": "blood_markers", "name": "Lipid Panel",
                     "frequency_months": 12}],
    )
    reproject_plan_from_json(plan.id, wb, db)

    rds = db.query(RotationDay).filter(RotationDay.plan_id == plan.id).all()
    assert len(rds) == 1 and rds[0].block_name == "Push Day"
    scs = db.query(Screening).filter(Screening.plan_id == plan.id).all()
    assert len(scs) == 1 and scs[0].name == "Lipid Panel"


# ── Rule 5: atomic rollback ───────────────────────────────────────────────


def test_malformed_json_rolls_back_completely(db_session):
    db = db_session
    plan = _make_plan(db, json_version=1)
    t = _make_task(db, plan, name="Walk", schedule="daily")
    past = _make_todo(db, t, on=YESTERDAY, completed=True, notes="keep me")
    fut = _make_todo(db, t, on=TODAY + timedelta(days=1))
    db.commit()

    base_templates = db.query(TaskTemplate).count()
    base_todos = db.query(DailyTodo).count()
    base_version = plan.json_version

    bad = _wb([{"task_id": str(uuid.uuid4()), "pillar": "brief_today"}])  # no name
    with pytest.raises(ValueError):
        reproject_plan_from_json(plan.id, bad, db)

    # DB completely unchanged.
    assert db.query(TaskTemplate).count() == base_templates
    assert db.query(DailyTodo).count() == base_todos
    assert db.query(DailyTodo).filter(DailyTodo.id == past.id).one().notes \
        == "keep me"
    assert db.query(DailyTodo).filter(DailyTodo.id == fut.id).count() == 1
    assert db.query(Plan).filter(Plan.id == plan.id).one().json_version \
        == base_version


def test_mid_mutation_failure_rolls_back(db_session, monkeypatch):
    """
    Failure AFTER deletes/inserts have happened must roll the whole
    transaction back. We force _plan_to_json (Pass 2f, late) to raise so
    the earlier mutations are real, then assert nothing persisted.
    """
    db = db_session
    plan = _make_plan(db, json_version=2)
    t = _make_task(db, plan, name="Walk", schedule="daily")
    past = _make_todo(db, t, on=YESTERDAY, completed=True, notes="keep me")
    fut = _make_todo(db, t, on=TODAY + timedelta(days=1))
    db.commit()

    base_templates = db.query(TaskTemplate).count()
    base_todos = db.query(DailyTodo).count()

    import app.services.plan_reproject as mod

    def _boom(*_a, **_k):
        raise RuntimeError("simulated late failure after mutations")

    monkeypatch.setattr(mod, "_plan_to_json", _boom)

    with pytest.raises(RuntimeError):
        reproject_plan_from_json(plan.id, _wb([_task_json(t)]), db)

    # Everything restored: counts, history, version.
    assert db.query(TaskTemplate).count() == base_templates
    assert db.query(DailyTodo).count() == base_todos
    assert (
        db.query(DailyTodo).filter(DailyTodo.id == past.id).one().notes
        == "keep me"
    )
    assert db.query(DailyTodo).filter(DailyTodo.id == fut.id).count() == 1
    assert db.query(Plan).filter(Plan.id == plan.id).one().json_version == 2


def test_unknown_plan_raises(db_session):
    with pytest.raises(ValueError):
        reproject_plan_from_json("nonexistent", _wb([]), db_session)


def test_duplicate_task_id_rejected(db_session):
    db = db_session
    plan = _make_plan(db)
    t = _make_task(db, plan, name="Walk")
    db.commit()
    dup = t.id
    wb = _wb([
        {"task_id": dup, "pillar": "p", "name": "A"},
        {"task_id": dup, "pillar": "p", "name": "B"},
    ])
    with pytest.raises(ValueError):
        reproject_plan_from_json(plan.id, wb, db)
