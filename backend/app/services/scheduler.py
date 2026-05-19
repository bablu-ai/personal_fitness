"""
Daily TODO scheduler.
Generates DailyTodo rows for a given date from the active plan's TaskTemplates.
Schedule strings are parsed flexibly — unknown formats default to daily.
"""
import uuid
from datetime import date
import json
from sqlalchemy.orm import Session
from app.db.models import Plan, TaskTemplate, DailyTodo

WEEKDAY_MAP: dict[str, int] = {
    "mon": 0, "monday": 0,
    "tue": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}

# Schedules that mean "skip this task — never generate a daily todo"
_SKIP_PATTERNS = {
    "only if prescribed", "per specialist", "as needed", "prn",
    "skip", "n/a", "optional",
}


def _is_scheduled_today(schedule: str | None, today: date) -> bool:
    if not schedule:
        return True

    s = schedule.strip().lower()

    # Remove parenthetical qualifiers like "(no exceptions)" for matching
    import re
    s_clean = re.sub(r'\(.*?\)', '', s).strip()

    # Explicit skip markers — specialist / prescription only
    if s_clean in _SKIP_PATTERNS or any(p in s_clean for p in _SKIP_PATTERNS):
        return False

    if s_clean in ("daily", "every day", "everyday", "all days", "daily (no exceptions)"):
        return True

    if s_clean == "weekly":
        return today.weekday() == 0  # Monday

    if s_clean in ("weekdays", "workdays"):
        return today.weekday() < 5

    if s_clean in ("weekends",):
        return today.weekday() >= 5

    # Every other day: EOD, alternate day, every other day
    if s_clean in ("eod", "alternate day", "alternating day", "every other day", "every 2 days"):
        # Use ordinal so pattern is globally consistent regardless of plan start date
        return today.toordinal() % 2 == 0

    # 2×/wk → Monday + Thursday
    if re.search(r'2\s*[x×]\s*/?\s*w(ee)?k', s_clean):
        return today.weekday() in (0, 3)

    # 3×/wk → Monday + Wednesday + Friday
    if re.search(r'3\s*[x×]\s*/?\s*w(ee)?k', s_clean):
        return today.weekday() in (0, 2, 4)

    # Cycle schedules (e.g. "8wk on / 2wk off") → treat as daily, include every day
    if "cycle" in s_clean or "on/off" in s_clean or "on / off" in s_clean:
        return True

    # Comma-separated day names: "mon,wed,fri"
    parts = [p.strip() for p in s_clean.split(",")]
    day_numbers = [WEEKDAY_MAP[p] for p in parts if p in WEEKDAY_MAP]
    if day_numbers:
        return today.weekday() in day_numbers

    # Unknown schedule → include by default (open architecture: don't silently drop tasks)
    return True


def is_necessary_supplement(template: TaskTemplate) -> bool:
    """Necessary supplements: Active status + category containing B on supplements pillar."""
    if template.pillar != "supplements":
        return False
    try:
        meta = json.loads(template.extra_metadata or "{}")
    except ValueError:
        meta = {}
    status = str(meta.get("status", "")).strip().lower()
    category = str(meta.get("category", "")).strip().lower()
    return status == "active" and "b" in category


def generate_todos_for_date(
    db: Session,
    target_date: date,
    user_id: str = "default",
) -> list[DailyTodo]:
    existing = (
        db.query(DailyTodo)
        .filter(DailyTodo.date == target_date, DailyTodo.user_id == user_id)
        .all()
    )
    if existing:
        return existing

    active_plan = (
        db.query(Plan)
        .filter(Plan.is_active == True, Plan.user_id == user_id)  # noqa: E712
        .order_by(Plan.uploaded_at.desc())
        .first()
    )
    if not active_plan:
        return []

    templates = (
        db.query(TaskTemplate)
        .filter(TaskTemplate.plan_id == active_plan.id, TaskTemplate.is_reference == False)  # noqa: E712
        .all()
    )

    todos: list[DailyTodo] = []
    for template in templates:
        if _is_scheduled_today(template.schedule, target_date):
            todo = DailyTodo(
                id=str(uuid.uuid4()),
                template_id=template.id,
                user_id=user_id,
                date=target_date,
                completed=False,
            )
            db.add(todo)
            todos.append(todo)

    db.commit()
    return todos
