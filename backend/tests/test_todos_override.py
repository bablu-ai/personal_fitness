"""
Tests for per-day DailyTodo overrides (subagent #7).

Covers the response-layer overlay (name/target/hidden), summary exclusion of
hidden todos, and PATCH override write/merge/clear semantics, plus regression
on completion persistence and the necessary-supplements flow.

Uses the shared in-memory DB fixtures from conftest.py (isolated per test).
"""
from datetime import date, datetime, timezone
import json
import uuid

from app.db.models import Plan, TaskTemplate, DailyTodo


def _make_plan(db) -> Plan:
    plan = Plan(
        id=str(uuid.uuid4()),
        name="Test Plan",
        user_id="default",
        is_active=True,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(plan)
    db.flush()
    return plan


def _make_template(db, plan, **kw) -> TaskTemplate:
    t = TaskTemplate(
        id=str(uuid.uuid4()),
        plan_id=plan.id,
        user_id="default",
        pillar=kw.get("pillar", "brief_today"),
        name=kw.get("name", "Walk"),
        target_value=kw.get("target_value", "30 min"),
        is_reference=False,
        schedule=kw.get("schedule", "daily"),
        extra_metadata=kw.get("extra_metadata"),
    )
    db.add(t)
    db.flush()
    return t


def _make_todo(db, template, the_date, **kw) -> DailyTodo:
    todo = DailyTodo(
        id=str(uuid.uuid4()),
        template_id=template.id,
        user_id="default",
        date=the_date,
        completed=kw.get("completed", False),
        completed_at=kw.get("completed_at"),
        actual_value=kw.get("actual_value"),
        notes=kw.get("notes"),
        override_json=kw.get("override_json"),
    )
    db.add(todo)
    db.commit()
    return todo


D = date(2030, 6, 15)  # fixed future date with pre-seeded rows


def test_override_name_and_target_surface_in_day_view(client, db_session):
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan, name="Walk", target_value="30 min")
    _make_todo(
        db_session, tmpl, D,
        override_json=json.dumps({"name": "Stroll", "target_value": "10 min"}),
    )

    resp = client.get(f"/api/todos/{D.isoformat()}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["template"]["name"] == "Stroll"
    assert data[0]["template"]["target_value"] == "10 min"
    assert data[0]["override"] == {
        "name": "Stroll", "target_value": "10 min", "hidden": None,
    }

    # DB template is untouched
    db_session.expire_all()
    assert db_session.get(TaskTemplate, tmpl.id).name == "Walk"
    assert db_session.get(TaskTemplate, tmpl.id).target_value == "30 min"


def test_hidden_override_excluded_from_day_view_but_row_persists(client, db_session):
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan)
    todo = _make_todo(db_session, tmpl, D, override_json=json.dumps({"hidden": True}))

    resp = client.get(f"/api/todos/{D.isoformat()}")
    assert resp.status_code == 200
    assert resp.json() == []

    # Row still exists in DB (history preserved)
    db_session.expire_all()
    assert db_session.get(DailyTodo, todo.id) is not None


def test_hidden_override_excluded_from_summary(client, db_session):
    plan = _make_plan(db_session)
    visible_t = _make_template(db_session, plan, name="Visible")
    hidden_t = _make_template(db_session, plan, name="Hidden")
    _make_todo(db_session, visible_t, D, completed=True,
               completed_at=datetime.now(timezone.utc))
    _make_todo(db_session, hidden_t, D, override_json=json.dumps({"hidden": True}))

    resp = client.get(f"/api/todos/{D.isoformat()}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1            # hidden one not counted
    assert body["completed"] == 1
    assert body["completion_pct"] == 100.0
    assert "brief_today" in body["by_pillar"]
    assert body["by_pillar"]["brief_today"]["total"] == 1


def test_patch_writes_override(client, db_session):
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan, name="Walk")
    todo = _make_todo(db_session, tmpl, D)

    resp = client.patch(
        f"/api/todos/{todo.id}",
        json={"override": {"name": "Hike"}},
    )
    assert resp.status_code == 200
    assert resp.json()["template"]["name"] == "Hike"
    assert resp.json()["override"]["name"] == "Hike"

    db_session.expire_all()
    stored = json.loads(db_session.get(DailyTodo, todo.id).override_json)
    assert stored == {"name": "Hike"}


def test_patch_merges_into_existing_override(client, db_session):
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan)
    todo = _make_todo(db_session, tmpl, D, override_json=json.dumps({"name": "A"}))

    resp = client.patch(
        f"/api/todos/{todo.id}",
        json={"override": {"target_value": "5 min"}},
    )
    assert resp.status_code == 200
    db_session.expire_all()
    stored = json.loads(db_session.get(DailyTodo, todo.id).override_json)
    assert stored == {"name": "A", "target_value": "5 min"}


def test_patch_clearing_override_reverts_to_template(client, db_session):
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan, name="Walk", target_value="30 min")
    todo = _make_todo(
        db_session, tmpl, D,
        override_json=json.dumps({"name": "Stroll"}),
    )

    resp = client.patch(f"/api/todos/{todo.id}", json={"override": None})
    assert resp.status_code == 200
    assert resp.json()["template"]["name"] == "Walk"
    assert resp.json()["override"] is None

    db_session.expire_all()
    assert db_session.get(DailyTodo, todo.id).override_json is None

    # empty object also clears
    todo2 = _make_todo(db_session, tmpl, date(2030, 6, 16),
                       override_json=json.dumps({"name": "X"}))
    r2 = client.patch(f"/api/todos/{todo2.id}", json={"override": {}})
    assert r2.status_code == 200
    db_session.expire_all()
    assert db_session.get(DailyTodo, todo2.id).override_json is None


def test_patch_override_plus_completion_both_applied(client, db_session):
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan, name="Walk")
    todo = _make_todo(db_session, tmpl, D)

    resp = client.patch(
        f"/api/todos/{todo.id}",
        json={"completed": True, "override": {"name": "Hike"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["completed"] is True
    assert body["completed_at"] is not None
    assert body["template"]["name"] == "Hike"


def test_override_only_patch_preserves_existing_completion(client, db_session):
    """Rename-for-today must NOT clear an existing checkmark."""
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan)
    todo = _make_todo(db_session, tmpl, D, completed=True,
                      completed_at=datetime.now(timezone.utc))

    resp = client.patch(
        f"/api/todos/{todo.id}",
        json={"override": {"name": "Renamed"}},
    )
    assert resp.status_code == 200
    assert resp.json()["completed"] is True
    db_session.expire_all()
    assert db_session.get(DailyTodo, todo.id).completed is True


def test_patch_unknown_todo_404(client, db_session):
    resp = client.patch("/api/todos/does-not-exist", json={"completed": True})
    assert resp.status_code == 404


def test_patch_malformed_override_422(client, db_session):
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan)
    todo = _make_todo(db_session, tmpl, D)

    # unknown field rejected (extra="forbid")
    r1 = client.patch(f"/api/todos/{todo.id}",
                      json={"override": {"bogus": "x"}})
    assert r1.status_code == 422

    # empty-string name violates min_length
    r2 = client.patch(f"/api/todos/{todo.id}",
                      json={"override": {"name": ""}})
    assert r2.status_code == 422


def test_completion_persistence_regression(client, db_session):
    """Existing completion flow still works (no override involved)."""
    plan = _make_plan(db_session)
    tmpl = _make_template(db_session, plan)
    todo = _make_todo(db_session, tmpl, D)

    client.patch(f"/api/todos/{todo.id}",
                 json={"completed": True, "actual_value": "31 min",
                       "notes": "felt good"})
    db_session.expire_all()
    row = db_session.get(DailyTodo, todo.id)
    assert row.completed is True
    assert row.actual_value == "31 min"
    assert row.notes == "felt good"

    client.patch(f"/api/todos/{todo.id}", json={"completed": False})
    db_session.expire_all()
    row = db_session.get(DailyTodo, todo.id)
    assert row.completed is False
    assert row.completed_at is None


def test_necessary_supplements_regression_with_hidden(client, db_session):
    """Necessary-supplements flow stays green; hidden supplement is dropped."""
    plan = _make_plan(db_session)
    meta = json.dumps({"status": "Active", "category": "B"})
    needed = _make_template(db_session, plan, pillar="supplements",
                            name="Vit D", extra_metadata=meta)
    hidden_needed = _make_template(db_session, plan, pillar="supplements",
                                   name="Magnesium", extra_metadata=meta)
    _make_todo(db_session, needed, date.today())
    _make_todo(db_session, hidden_needed, date.today(),
               override_json=json.dumps({"hidden": True}))

    resp = client.get("/api/todos/supplements/necessary")
    assert resp.status_code == 200
    names = [t["template"]["name"] for t in resp.json()]
    assert "Vit D" in names
    assert "Magnesium" not in names
