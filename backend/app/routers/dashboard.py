from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import DailyTodo
from app.schemas.dashboard import DailyRow, WeeklyRow, MonthlyRow
from app.constants import DEFAULT_USER_ID
from collections import defaultdict

router = APIRouter()


def _get_todos_in_range(db: Session, start: date, end: date, user_id: str):
    return (
        db.query(DailyTodo)
        .filter(
            DailyTodo.date >= start,
            DailyTodo.date <= end,
            DailyTodo.user_id == user_id,
        )
        .all()
    )


@router.get("/dashboard/daily", response_model=list[DailyRow])
def daily_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    end = date.today()
    start = end - timedelta(days=days - 1)
    todos = _get_todos_in_range(db, start, end, DEFAULT_USER_ID)

    by_date: dict[date, dict] = defaultdict(lambda: {"total": 0, "completed": 0})
    for todo in todos:
        by_date[todo.date]["total"] += 1
        if todo.completed:
            by_date[todo.date]["completed"] += 1

    rows = []
    for d in (start + timedelta(n) for n in range(days)):
        stats = by_date.get(d, {"total": 0, "completed": 0})
        rows.append(DailyRow(
            date=d,
            total=stats["total"],
            completed=stats["completed"],
            completion_pct=round(stats["completed"] / stats["total"] * 100, 1) if stats["total"] else 0.0,
        ))
    return rows


@router.get("/dashboard/weekly", response_model=list[WeeklyRow])
def weekly_dashboard(
    weeks: int = Query(default=12, ge=1, le=52),
    db: Session = Depends(get_db),
):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    start = week_start - timedelta(weeks=weeks - 1)
    todos = _get_todos_in_range(db, start, today, DEFAULT_USER_ID)

    by_week: dict[date, dict] = defaultdict(lambda: {"total": 0, "completed": 0, "days": set()})
    for todo in todos:
        ws = todo.date - timedelta(days=todo.date.weekday())
        by_week[ws]["total"] += 1
        if todo.completed:
            by_week[ws]["completed"] += 1
        by_week[ws]["days"].add(todo.date)

    rows = []
    for w in range(weeks):
        ws = week_start - timedelta(weeks=weeks - 1 - w)
        stats = by_week.get(ws, {"total": 0, "completed": 0, "days": set()})
        rows.append(WeeklyRow(
            week_start=ws,
            total=stats["total"],
            completed=stats["completed"],
            completion_pct=round(stats["completed"] / stats["total"] * 100, 1) if stats["total"] else 0.0,
            days_tracked=len(stats["days"]),
        ))
    return rows


@router.get("/dashboard/monthly", response_model=list[MonthlyRow])
def monthly_dashboard(
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    today = date.today()
    rows = []

    for m in range(months - 1, -1, -1):
        year = today.year - ((today.month - 1 - m) // 12 + (1 if (today.month - 1 - m) < 0 else 0))
        month = ((today.month - 1 - m) % 12) + 1
        month_str = f"{year:04d}-{month:02d}"

        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)

        todos = _get_todos_in_range(db, start, min(end, today), DEFAULT_USER_ID)
        total = len(todos)
        completed = sum(1 for t in todos if t.completed)
        days_tracked = len({t.date for t in todos})

        rows.append(MonthlyRow(
            month=month_str,
            total=total,
            completed=completed,
            completion_pct=round(completed / total * 100, 1) if total else 0.0,
            days_tracked=days_tracked,
        ))

    return rows
