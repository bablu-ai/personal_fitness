from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import DailyTodo, TaskTemplate, Plan
from app.services.scheduler import generate_todos_for_date
import json
from app.schemas.todo import DailyTodoOut, TodoUpdateRequest, DaySummary, TaskDetailOut, TaskTemplateOut, RelatedExercise, Exercise
from app.constants import DEFAULT_USER_ID

router = APIRouter()


@router.get("/todos/today", response_model=list[DailyTodoOut])
def get_today_todos(db: Session = Depends(get_db)):
    todos = generate_todos_for_date(db, date.today(), DEFAULT_USER_ID)
    return todos


@router.get("/todos/{todo_date}", response_model=list[DailyTodoOut])
def get_todos_for_date(todo_date: date, db: Session = Depends(get_db)):
    todos = generate_todos_for_date(db, todo_date, DEFAULT_USER_ID)
    return todos


@router.patch("/todos/{todo_id}", response_model=DailyTodoOut)
def update_todo(todo_id: str, body: TodoUpdateRequest, db: Session = Depends(get_db)):
    todo = db.get(DailyTodo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found.")

    todo.completed = body.completed
    todo.completed_at = datetime.now(timezone.utc) if body.completed else None
    if body.actual_value is not None:
        todo.actual_value = body.actual_value
    if body.notes is not None:
        todo.notes = body.notes

    db.commit()
    db.refresh(todo)
    return todo


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
