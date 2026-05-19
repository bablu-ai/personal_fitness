from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import DailyTodo, TaskTemplate, Plan
from app.services.scheduler import generate_todos_for_date, is_necessary_supplement
import json
from app.schemas.todo import (
    DailyTodoOut,
    TodoUpdateRequest,
    TodoOverride,
    DaySummary,
    TaskDetailOut,
    TaskTemplateOut,
    Exercise,
)
from app.constants import DEFAULT_USER_ID

router = APIRouter()


def _parse_override(raw: str | None) -> dict:
    """Decode DailyTodo.override_json. Malformed JSON is treated as no override
    (never raise — a bad overlay must not 500 the day view)."""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _override_out(override: dict) -> TodoOverride | None:
    """Build the response TodoOverride from a stored overlay dict, ignoring
    any unknown/legacy keys so a stale overlay never 500s the response."""
    if not override:
        return None
    known = {
        k: override[k]
        for k in ("name", "target_value", "hidden")
        if k in override
    }
    if not known:
        return None
    try:
        return TodoOverride.model_validate(known)
    except Exception:
        return None


def _to_out(todo: DailyTodo) -> DailyTodoOut | None:
    """Build the response DTO for one todo, applying its per-day overlay.

    Returns None when the overlay marks the todo hidden for this date — the
    DB row is untouched (history stays queryable); it is only excluded from
    the response. name/target_value from the overlay win over the template
    without mutating it.
    """
    override = _parse_override(todo.override_json)
    if override.get("hidden") is True:
        return None

    template_out = TaskTemplateOut.model_validate(todo.template)
    name = override.get("name")
    if isinstance(name, str) and name.strip():
        template_out.name = name
    target = override.get("target_value")
    if isinstance(target, str) and target.strip():
        template_out.target_value = target

    out = DailyTodoOut(
        id=todo.id,
        date=todo.date,
        completed=todo.completed,
        completed_at=todo.completed_at,
        actual_value=todo.actual_value,
        notes=todo.notes,
        template=template_out,
        override=_override_out(override),
    )
    return out


def _serialize(todos: list[DailyTodo]) -> list[DailyTodoOut]:
    return [out for t in todos if (out := _to_out(t)) is not None]


@router.get("/todos/today", response_model=list[DailyTodoOut])
def get_today_todos(db: Session = Depends(get_db)):
    todos = generate_todos_for_date(db, date.today(), DEFAULT_USER_ID)
    return _serialize(todos)


@router.get("/todos/{todo_date}", response_model=list[DailyTodoOut])
def get_todos_for_date(todo_date: date, db: Session = Depends(get_db)):
    todos = generate_todos_for_date(db, todo_date, DEFAULT_USER_ID)
    return _serialize(todos)


@router.get("/todos/supplements/necessary", response_model=list[DailyTodoOut])
def get_necessary_supplements_todos(db: Session = Depends(get_db)):
    todos = generate_todos_for_date(db, date.today(), DEFAULT_USER_ID)
    return _serialize(
        [t for t in todos if t.template and is_necessary_supplement(t.template)]
    )


@router.patch(
    "/todos/{todo_id}",
    response_model=DailyTodoOut,
    summary="Update a daily todo's completion and/or per-day override",
    tags=["todos"],
    responses={
        404: {"description": "Todo not found"},
        422: {"description": "Invalid request body (e.g. unknown override field)"},
    },
)
def update_todo(todo_id: str, body: TodoUpdateRequest, db: Session = Depends(get_db)):
    """Update completion fields and/or the per-day overlay for one todo.

    Override semantics:
    - `override` absent  -> override_json unchanged.
    - `override` is null or an empty object -> override_json cleared (revert
      to template values for this date).
    - `override` with fields -> merged into the existing override_json
      (previously-set keys are preserved unless re-specified).

    `completed` is optional: omitting it leaves an existing completion intact
    (so an override-only edit does not clear the checkmark). The plan/template
    is never mutated.
    """
    todo = db.get(DailyTodo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found.")

    if body.completed is not None:
        todo.completed = body.completed
        todo.completed_at = datetime.now(timezone.utc) if body.completed else None
    if body.actual_value is not None:
        todo.actual_value = body.actual_value
    if body.notes is not None:
        todo.notes = body.notes

    if "override" in body.model_fields_set:
        if body.override is None:
            todo.override_json = None
        else:
            patch = body.override.model_dump(exclude_unset=True)
            if not patch:
                # empty object -> clear (revert to template)
                todo.override_json = None
            else:
                current = _parse_override(todo.override_json)
                current.update(patch)
                # drop keys explicitly nulled so they revert to template
                current = {k: v for k, v in current.items() if v is not None}
                todo.override_json = json.dumps(current) if current else None

    db.commit()
    db.refresh(todo)
    out = _to_out(todo)
    if out is None:
        # Todo was just hidden for this date — still return its state so the
        # client can reflect the override (it simply won't list it in day views).
        out = DailyTodoOut(
            id=todo.id,
            date=todo.date,
            completed=todo.completed,
            completed_at=todo.completed_at,
            actual_value=todo.actual_value,
            notes=todo.notes,
            template=TaskTemplateOut.model_validate(todo.template),
            override=_override_out(_parse_override(todo.override_json)),
        )
    return out


@router.get("/tasks/{template_id}/detail", response_model=TaskDetailOut,
            summary="Full task detail with embedded exercises")
def get_task_detail(template_id: str, db: Session = Depends(get_db)):
    template = db.get(TaskTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Task not found.")

    exercises: list[Exercise] = []
    if template.exercises_json:
        try:
            raw = json.loads(template.exercises_json)
            exercises = [Exercise(**ex) for ex in raw if isinstance(ex, dict)]
        except Exception:
            pass

    out = TaskDetailOut.model_validate(template)
    out.exercises = exercises
    return out


@router.get("/reference", response_model=list[TaskTemplateOut],
            summary="Reference entries (nutrition, sleep, cognitive) — not daily todos")
def get_reference_items(db: Session = Depends(get_db)):
    plan = (
        db.query(Plan)
        .filter(Plan.is_active == True, Plan.user_id == DEFAULT_USER_ID)  # noqa: E712
        .order_by(Plan.uploaded_at.desc())
        .first()
    )
    if not plan:
        return []
    return (
        db.query(TaskTemplate)
        .filter(TaskTemplate.plan_id == plan.id, TaskTemplate.is_reference == True)  # noqa: E712
        .order_by(TaskTemplate.pillar, TaskTemplate.name)
        .all()
    )


@router.get("/todos/{todo_date}/summary", response_model=DaySummary)
def get_day_summary(todo_date: date, db: Session = Depends(get_db)):
    todos = (
        db.query(DailyTodo)
        .filter(DailyTodo.date == todo_date, DailyTodo.user_id == DEFAULT_USER_ID)
        .all()
    )

    # Hidden per-day overrides are excluded from totals and per-pillar counts
    # (the DB rows still exist for history).
    todos = [t for t in todos if _parse_override(t.override_json).get("hidden") is not True]

    by_pillar: dict[str, dict] = {}
    for todo in todos:
        pillar = todo.template.pillar if todo.template else "unknown"
        if pillar not in by_pillar:
            by_pillar[pillar] = {"total": 0, "completed": 0, "pct": 0.0}
        by_pillar[pillar]["total"] += 1
        if todo.completed:
            by_pillar[pillar]["completed"] += 1

    for pillar, stats in by_pillar.items():
        stats["pct"] = round(stats["completed"] / stats["total"] * 100, 1) if stats["total"] else 0.0

    total = len(todos)
    completed = sum(1 for t in todos if t.completed)

    return DaySummary(
        date=todo_date,
        total=total,
        completed=completed,
        completion_pct=round(completed / total * 100, 1) if total else 0.0,
        by_pillar=by_pillar,
    )
