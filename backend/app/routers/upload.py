import io
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Plan, TaskTemplate, RotationDay, DailyTodo, Screening
from app.services.excel_parser import parse_workbook, parse_rotation_sheet, parse_screening_sheets
from app.schemas.plan import PlanOut, UploadResponse
from app.constants import DEFAULT_USER_ID

router = APIRouter()


def _wipe_user_data(db: Session, user_id: str) -> date | None:
    """
    Delete all plan data for a user and return the previous rotation_start_date
    so the caller can carry it forward to the new plan.
    """
    prev_plan = (
        db.query(Plan)
        .filter(Plan.user_id == user_id, Plan.is_active == True)  # noqa: E712
        .order_by(Plan.uploaded_at.desc())
        .first()
    )
    prev_start = prev_plan.rotation_start_date if prev_plan else None

    # Delete todos first (no cascade from TaskTemplate in DB)
    db.query(DailyTodo).filter(DailyTodo.user_id == user_id).delete()

    # Delete all plans — ORM cascade removes TaskTemplates, RotationDays,
    # RotationCompletions, Screenings, ScreeningRecords
    old_plans = db.query(Plan).filter(Plan.user_id == user_id).all()
    for plan in old_plans:
        db.delete(plan)

    db.flush()
    return prev_start


@router.post("/upload", response_model=UploadResponse)
async def upload_plan(
    file: UploadFile = File(...),
    rotation_start_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are accepted.")

    try:
        contents = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read uploaded file.")

    parsed_start: date | None = None
    if rotation_start_date:
        try:
            parsed_start = date.fromisoformat(rotation_start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="rotation_start_date must be YYYY-MM-DD.")

    # Wipe old data and recover the previous rotation start date
    prev_start = _wipe_user_data(db, DEFAULT_USER_ID)

    # Use the provided date, fall back to whatever the previous plan had
    effective_start = parsed_start or prev_start

    plan_id = str(uuid.uuid4())
    plan = Plan(
        id=plan_id,
        name=file.filename,
        is_active=True,
        user_id=DEFAULT_USER_ID,
        rotation_start_date=effective_start,
    )
    db.add(plan)

    try:
        tasks = parse_workbook(io.BytesIO(contents), plan_id, DEFAULT_USER_ID)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Failed to parse workbook: {str(e)}")

    if not tasks:
        db.rollback()
        raise HTTPException(status_code=422, detail="No tasks found in workbook. Check sheet names and column headers.")

    for task in tasks:
        db.add(TaskTemplate(**task))

    rotation_count = 0
    try:
        rotation_rows = parse_rotation_sheet(io.BytesIO(contents), plan_id, DEFAULT_USER_ID)
        for row in rotation_rows:
            db.add(RotationDay(**row))
        rotation_count = len(rotation_rows)
    except Exception:
        pass

    try:
        screening_rows = parse_screening_sheets(io.BytesIO(contents), plan_id, DEFAULT_USER_ID)
        for row in screening_rows:
            db.add(Screening(**row))
    except Exception:
        pass

    db.commit()
    db.refresh(plan)

    pillars = sorted({t["pillar"] for t in tasks})

    return UploadResponse(
        plan=PlanOut.model_validate(plan),
        tasks_imported=len(tasks),
        pillars_found=pillars,
        rotation_days_imported=rotation_count,
    )
