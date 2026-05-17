"""
Screenings router.
GET  /api/screenings/due       → screenings overdue or due within 60 days
GET  /api/screenings           → all screenings for the active plan
POST /api/screenings/{id}/done → record a completion date
"""
from datetime import date, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Plan, Screening, ScreeningRecord
from app.constants import DEFAULT_USER_ID

router = APIRouter()

LOOKAHEAD_DAYS = 60  # surface screenings due within this window


class ScreeningOut(BaseModel):
    id: str
    pillar: str
    name: str
    description: str | None
    frequency_months: int | None
    target_value: str | None
    last_done_date: str | None   # YYYY-MM-DD or null
    next_due_date: str | None    # YYYY-MM-DD or null
    is_overdue: bool
    due_in_days: int | None      # negative = overdue by that many days

    model_config = {"from_attributes": True}


class DoneRequest(BaseModel):
    completed_date: str | None = None  # defaults to today
    notes: str | None = None


def _active_plan(db: Session) -> Plan | None:
    return (
        db.query(Plan)
        .filter(Plan.is_active == True, Plan.user_id == DEFAULT_USER_ID)  # noqa: E712
        .order_by(Plan.uploaded_at.desc())
        .first()
    )


def _build_screening_out(screening: Screening, last_record: ScreeningRecord | None) -> ScreeningOut:
    today = date.today()
    last_done = last_record.completed_date if last_record else None

    next_due: date | None = None
    if screening.frequency_months and last_done:
        next_due = last_done + timedelta(days=screening.frequency_months * 30)
    elif not last_done:
        # Never done — treat as immediately due
        next_due = today

    is_overdue = next_due is not None and next_due <= today
    due_in_days: int | None = None
    if next_due is not None:
        due_in_days = (next_due - today).days

    return ScreeningOut(
        id=screening.id,
        pillar=screening.pillar,
        name=screening.name,
        description=screening.description,
        frequency_months=screening.frequency_months,
        target_value=screening.target_value,
        last_done_date=last_done.isoformat() if last_done else None,
        next_due_date=next_due.isoformat() if next_due else None,
        is_overdue=is_overdue,
        due_in_days=due_in_days,
    )


@router.get("/screenings", response_model=list[ScreeningOut])
def list_screenings(db: Session = Depends(get_db)):
    plan = _active_plan(db)
    if not plan:
        return []

    screenings = db.query(Screening).filter(Screening.plan_id == plan.id).all()

    # Latest completion record per screening
    latest: dict[str, ScreeningRecord] = {}
    for s in screenings:
        rec = (
            db.query(ScreeningRecord)
            .filter(ScreeningRecord.screening_id == s.id)
            .order_by(ScreeningRecord.completed_date.desc())
            .first()
        )
        if rec:
            latest[s.id] = rec

    return [_build_screening_out(s, latest.get(s.id)) for s in screenings]


@router.get("/screenings/due", response_model=list[ScreeningOut])
def get_due_screenings(db: Session = Depends(get_db)):
    plan = _active_plan(db)
    if not plan:
        return []

    screenings = db.query(Screening).filter(Screening.plan_id == plan.id).all()
    result = []

    for s in screenings:
        rec = (
            db.query(ScreeningRecord)
            .filter(ScreeningRecord.screening_id == s.id)
            .order_by(ScreeningRecord.completed_date.desc())
            .first()
        )
        out = _build_screening_out(s, rec)
        # Include if never done, overdue, or due within LOOKAHEAD_DAYS
        if out.due_in_days is not None and out.due_in_days <= LOOKAHEAD_DAYS:
            result.append(out)

    return sorted(result, key=lambda x: x.due_in_days if x.due_in_days is not None else 0)


@router.post("/screenings/{screening_id}/done", response_model=ScreeningOut)
def mark_screening_done(
    screening_id: str,
    body: DoneRequest,
    db: Session = Depends(get_db),
):
    screening = db.get(Screening, screening_id)
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found.")

    done_date = date.fromisoformat(body.completed_date) if body.completed_date else date.today()
    db.add(ScreeningRecord(
        screening_id=screening_id,
        user_id=DEFAULT_USER_ID,
        completed_date=done_date,
        notes=body.notes,
    ))
    db.commit()

    rec = (
        db.query(ScreeningRecord)
        .filter(ScreeningRecord.screening_id == screening_id)
        .order_by(ScreeningRecord.completed_date.desc())
        .first()
    )
    return _build_screening_out(screening, rec)
