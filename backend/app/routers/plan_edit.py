"""
Plan editor router — thin HTTP layer over ``plan_editor`` service.

All business logic lives in ``app.services.plan_editor``. Routes parse the
request, call the service, and return the typed response.

Prefix: /plan  (mounted as /api/plan in main.py)
Tags:   plan-edit
"""
from __future__ import annotations

import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.plan_edit import (
    ActivateOut,
    FlagActionOut,
    PlanReviewOut,
    RotationDayOut,
    RotationDayUpsert,
    ScreeningOut,
    ScreeningUpsert,
    TaskOut,
    TaskUpsert,
)
from app.services import plan_editor

router = APIRouter(prefix="/plan", tags=["plan-edit"])


@router.get(
    "/{plan_id}/review",
    response_model=PlanReviewOut,
    summary="Get full plan review with live flags",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan not found"},
    },
)
def get_plan_review(
    plan_id: str,
    db: Session = Depends(get_db),
) -> PlanReviewOut:
    return plan_editor.get_plan_review(plan_id, db)


@router.post(
    "/{plan_id}/tasks",
    response_model=TaskOut,
    status_code=201,
    summary="Add a new task to the plan",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan not found"},
        409: {"description": "Stale json_version — reload and retry"},
        422: {"description": "Validation error in task payload"},
    },
)
def add_task(
    plan_id: str,
    payload: TaskUpsert,
    v: int = Query(default=1, description="Current json_version (concurrency guard)"),
    db: Session = Depends(get_db),
) -> TaskOut:
    return plan_editor.add_task(plan_id, payload, v, db)


@router.put(
    "/{plan_id}/tasks/{task_id}",
    response_model=TaskOut,
    status_code=200,
    summary="Update an existing task in the plan",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan or task not found"},
        409: {"description": "Stale json_version — reload and retry"},
        422: {"description": "Validation error in task payload"},
    },
)
def update_task(
    plan_id: str,
    task_id: str,
    payload: TaskUpsert,
    v: int = Query(default=1, description="Current json_version (concurrency guard)"),
    db: Session = Depends(get_db),
) -> TaskOut:
    return plan_editor.update_task(plan_id, task_id, payload, v, db)


@router.delete(
    "/{plan_id}/tasks/{task_id}",
    status_code=204,
    summary="Delete a task from the plan",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan or task not found"},
        409: {"description": "Stale json_version — reload and retry"},
    },
)
def delete_task(
    plan_id: str,
    task_id: str,
    v: int = Query(default=1, description="Current json_version (concurrency guard)"),
    db: Session = Depends(get_db),
) -> None:
    plan_editor.delete_task(plan_id, task_id, v, db)


@router.put(
    "/{plan_id}/rotation/{day_number}",
    response_model=RotationDayOut,
    status_code=200,
    summary="Update a rotation day",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan not found"},
        409: {"description": "Stale json_version — reload and retry"},
        422: {"description": "Validation error in rotation day payload"},
    },
)
def update_rotation_day(
    plan_id: str,
    day_number: int,
    payload: RotationDayUpsert,
    v: int = Query(default=1, description="Current json_version (concurrency guard)"),
    db: Session = Depends(get_db),
) -> RotationDayOut:
    return plan_editor.update_rotation_day(plan_id, day_number, payload, v, db)


@router.put(
    "/{plan_id}/screenings/{screening_id}",
    response_model=ScreeningOut,
    status_code=200,
    summary="Update a screening",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan or screening not found"},
        409: {"description": "Stale json_version — reload and retry"},
        422: {"description": "Validation error in screening payload"},
    },
)
def update_screening(
    plan_id: str,
    screening_id: str,
    payload: ScreeningUpsert,
    v: int = Query(default=1, description="Current json_version (concurrency guard)"),
    db: Session = Depends(get_db),
) -> ScreeningOut:
    return plan_editor.update_screening(plan_id, screening_id, payload, v, db)


@router.post(
    "/{plan_id}/flags/{flag_id}/apply",
    response_model=FlagActionOut,
    status_code=200,
    summary="Apply a reviewer flag's suggestion",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan not found"},
        409: {"description": "Stale json_version — reload and retry"},
    },
)
def apply_flag(
    plan_id: str,
    flag_id: str,
    v: int = Query(default=1, description="Current json_version (concurrency guard)"),
    db: Session = Depends(get_db),
) -> FlagActionOut:
    return plan_editor.apply_flag(plan_id, flag_id, v, db)


@router.post(
    "/{plan_id}/flags/{flag_id}/dismiss",
    response_model=FlagActionOut,
    status_code=200,
    summary="Dismiss a reviewer flag without applying its suggestion",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan not found"},
        409: {"description": "Stale json_version — reload and retry"},
    },
)
def dismiss_flag(
    plan_id: str,
    flag_id: str,
    v: int = Query(default=1, description="Current json_version (concurrency guard)"),
    db: Session = Depends(get_db),
) -> FlagActionOut:
    return plan_editor.dismiss_flag(plan_id, flag_id, v, db)


@router.post(
    "/{plan_id}/activate",
    response_model=ActivateOut,
    status_code=200,
    summary="Activate a plan (draft → active); blocks on unresolved blocking flags",
    tags=["plan-edit"],
    responses={
        404: {"description": "Plan not found"},
        409: {"description": "Stale version or unresolved blocking flags"},
    },
)
def activate_plan(
    plan_id: str,
    v: int = Query(default=1, description="Current json_version (concurrency guard)"),
    db: Session = Depends(get_db),
) -> ActivateOut:
    return plan_editor.activate_plan(plan_id, v, db)


@router.get(
    "/{plan_id}/download.xlsx",
    summary="Download the plan as an xlsx workbook",
    tags=["plan-edit"],
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Excel workbook for this plan",
        },
        404: {"description": "Plan not found"},
        500: {"description": "Template xlsx not found on server"},
    },
)
def download_xlsx(
    plan_id: str,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from app.services.workbook_to_xlsx import generate_xlsx

    from app.db.models import Plan
    plan = db.query(Plan).filter(Plan.id == plan_id).one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found")

    raw = plan.plan_json
    workbook_json: dict = {}
    if raw and raw.strip() and raw.strip() not in ("{}", ""):
        try:
            workbook_json = json.loads(raw)
        except (ValueError, TypeError):
            workbook_json = {}

    try:
        xlsx_bytes = generate_xlsx(workbook_json)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="plan_{plan_id}.xlsx"',
        },
    )
