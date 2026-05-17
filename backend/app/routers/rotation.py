"""
30-day rotation router.
GET   /api/rotation/today   → today's rotation day
GET   /api/rotation/week    → Mon–Sun grid for a given week
PATCH /api/rotation/start   → set rotation_start_date on active plan
PATCH /api/rotation/complete → mark a specific date's rotation as done
"""
from datetime import date, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Plan, RotationDay, RotationCompletion
from app.constants import DEFAULT_USER_ID

router = APIRouter()


class RotationDayOut(BaseModel):
    day_number: int
    week_number: int | None
    block_name: str
    # v3 fields
    warm_up: str | None
    priority_block: str | None
    secondary_block: str | None
    cardio_steps: str | None
    cool_down: str | None
    nutrition_focus: str | None
    intensity_cap: str | None
    source_key: str | None
    sets: str | None
    reps: str | None
    duration: str | None
    notes: str | None
    # v4 time-budget fields
    morning_time: str | None
    warm_up_min: str | None
    upper_back_core_min: str | None
    secondary_min: str | None
    cool_down_min: str | None
    total_min: str | None
    fits_60: str | None
    priority_exercises: str | None
    secondary_exercises: str | None
    week_rule: str | None
    completed_today: bool
    rotation_start_date: str | None

    model_config = {"from_attributes": True}


class RotationStartRequest(BaseModel):
    rotation_start_date: str  # YYYY-MM-DD


class RotationCompleteRequest(BaseModel):
    day_number: int
    completed: bool
    target_date: Optional[str] = None  # YYYY-MM-DD; defaults to today


class RotationWeekDay(BaseModel):
    calendar_date: str
    day_of_week: str
    rotation_day_number: int
    block_name: str
    # v3 fields
    warm_up: str | None
    priority_block: str | None
    secondary_block: str | None
    cardio_steps: str | None
    cool_down: str | None
    nutrition_focus: str | None
    intensity_cap: str | None
    sets: str | None
    reps: str | None
    duration: str | None
    notes: str | None
    # v4 time-budget fields
    morning_time: str | None
    warm_up_min: str | None
    upper_back_core_min: str | None
    secondary_min: str | None
    cool_down_min: str | None
    total_min: str | None
    fits_60: str | None
    priority_exercises: str | None
    secondary_exercises: str | None
    week_rule: str | None
    completed: bool
    is_today: bool


def _active_plan(db: Session, user_id: str = DEFAULT_USER_ID) -> Plan | None:
    return (
        db.query(Plan)
        .filter(Plan.is_active == True, Plan.user_id == user_id)  # noqa: E712
        .order_by(Plan.uploaded_at.desc())
        .first()
    )


@router.get("/rotation/today", response_model=RotationDayOut | None)
def get_today_rotation(db: Session = Depends(get_db)):
    plan = _active_plan(db)
    if not plan or not plan.rotation_start_date:
        return None

    today = date.today()
    days_elapsed = (today - plan.rotation_start_date).days
    day_number = (days_elapsed % 30) + 1  # cycles 1–30

    rotation_day = (
        db.query(RotationDay)
        .filter(RotationDay.plan_id == plan.id, RotationDay.day_number == day_number)
        .first()
    )
    if not rotation_day:
        return None

    completed_today = (
        db.query(RotationCompletion)
        .filter(
            RotationCompletion.rotation_day_id == rotation_day.id,
            RotationCompletion.completion_date == today,
            RotationCompletion.completed == True,  # noqa: E712
        )
        .first()
    ) is not None

    return RotationDayOut(
        day_number=rotation_day.day_number,
        week_number=rotation_day.week_number,
        block_name=rotation_day.block_name,
        warm_up=rotation_day.warm_up,
        priority_block=rotation_day.priority_block,
        secondary_block=rotation_day.secondary_block,
        cardio_steps=rotation_day.cardio_steps,
        cool_down=rotation_day.cool_down,
        nutrition_focus=rotation_day.nutrition_focus,
        intensity_cap=rotation_day.intensity_cap,
        source_key=rotation_day.source_key,
        sets=rotation_day.sets,
        reps=rotation_day.reps,
        duration=rotation_day.duration,
        notes=rotation_day.notes,
        morning_time=rotation_day.morning_time,
        warm_up_min=rotation_day.warm_up_min,
        upper_back_core_min=rotation_day.upper_back_core_min,
        secondary_min=rotation_day.secondary_min,
        cool_down_min=rotation_day.cool_down_min,
        total_min=rotation_day.total_min,
        fits_60=rotation_day.fits_60,
        priority_exercises=rotation_day.priority_exercises,
        secondary_exercises=rotation_day.secondary_exercises,
        week_rule=rotation_day.week_rule,
        completed_today=completed_today,
        rotation_start_date=plan.rotation_start_date.isoformat() if plan.rotation_start_date else None,
    )


@router.get("/rotation/week", response_model=list[RotationWeekDay])
def get_week_rotation(
    week_start: Optional[str] = Query(None, description="YYYY-MM-DD of any day in the desired week"),
    db: Session = Depends(get_db),
):
    plan = _active_plan(db)
    if not plan or not plan.rotation_start_date:
        return []

    # Anchor to the Monday of the requested week (or current week)
    anchor = date.fromisoformat(week_start) if week_start else date.today()
    monday = anchor - timedelta(days=anchor.weekday())
    today = date.today()

    # Pre-load all rotation days for this plan
    rotation_map: dict[int, RotationDay] = {
        rd.day_number: rd
        for rd in db.query(RotationDay).filter(RotationDay.plan_id == plan.id).all()
    }

    # Pre-load completions for this week
    week_dates = [monday + timedelta(days=i) for i in range(7)]
    completions: set[tuple[int, str]] = set()
    for rd_id, comp_date in (
        db.query(RotationCompletion.rotation_day_id, RotationCompletion.completion_date)
        .filter(
            RotationCompletion.plan_id == plan.id,
            RotationCompletion.completion_date.in_(week_dates),
            RotationCompletion.completed == True,  # noqa: E712
        )
        .all()
    ):
        # Map rotation_day_id → day_number
        for day_num, rd in rotation_map.items():
            if rd.id == rd_id:
                completions.add((day_num, comp_date.isoformat()))

    result: list[RotationWeekDay] = []
    for d in week_dates:
        days_elapsed = (d - plan.rotation_start_date).days
        day_number = (days_elapsed % 30) + 1
        rd = rotation_map.get(day_number)
        result.append(RotationWeekDay(
            calendar_date=d.isoformat(),
            day_of_week=d.strftime("%A"),
            rotation_day_number=day_number,
            block_name=rd.block_name if rd else f"Day {day_number}",
            warm_up=rd.warm_up if rd else None,
            priority_block=rd.priority_block if rd else None,
            secondary_block=rd.secondary_block if rd else None,
            cardio_steps=rd.cardio_steps if rd else None,
            cool_down=rd.cool_down if rd else None,
            nutrition_focus=rd.nutrition_focus if rd else None,
            intensity_cap=rd.intensity_cap if rd else None,
            sets=rd.sets if rd else None,
            reps=rd.reps if rd else None,
            duration=rd.duration if rd else None,
            notes=rd.notes if rd else None,
            morning_time=rd.morning_time if rd else None,
            warm_up_min=rd.warm_up_min if rd else None,
            upper_back_core_min=rd.upper_back_core_min if rd else None,
            secondary_min=rd.secondary_min if rd else None,
            cool_down_min=rd.cool_down_min if rd else None,
            total_min=rd.total_min if rd else None,
            fits_60=rd.fits_60 if rd else None,
            priority_exercises=rd.priority_exercises if rd else None,
            secondary_exercises=rd.secondary_exercises if rd else None,
            week_rule=rd.week_rule if rd else None,
            completed=(day_number, d.isoformat()) in completions,
            is_today=d == today,
        ))

    return result


@router.patch("/rotation/start")
def set_rotation_start(body: RotationStartRequest, db: Session = Depends(get_db)):
    try:
        start = date.fromisoformat(body.rotation_start_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="rotation_start_date must be YYYY-MM-DD.")

    plan = _active_plan(db)
    if not plan:
        raise HTTPException(status_code=404, detail="No active plan found. Upload a workbook first.")

    plan.rotation_start_date = start
    db.commit()
    return {"rotation_start_date": start.isoformat()}


@router.patch("/rotation/complete")
def complete_rotation(body: RotationCompleteRequest, db: Session = Depends(get_db)):
    plan = _active_plan(db)
    if not plan:
        raise HTTPException(status_code=404, detail="No active plan.")

    rotation_day = (
        db.query(RotationDay)
        .filter(RotationDay.plan_id == plan.id, RotationDay.day_number == body.day_number)
        .first()
    )
    if not rotation_day:
        raise HTTPException(status_code=404, detail=f"Day {body.day_number} not found in rotation.")

    target = date.fromisoformat(body.target_date) if body.target_date else date.today()
    existing = (
        db.query(RotationCompletion)
        .filter(
            RotationCompletion.rotation_day_id == rotation_day.id,
            RotationCompletion.completion_date == target,
        )
        .first()
    )

    if existing:
        existing.completed = body.completed
    else:
        db.add(RotationCompletion(
            rotation_day_id=rotation_day.id,
            plan_id=plan.id,
            user_id=DEFAULT_USER_ID,
            completion_date=target,
            completed=body.completed,
        ))

    db.commit()
    return {"day_number": body.day_number, "completed": body.completed, "date": target.isoformat()}
