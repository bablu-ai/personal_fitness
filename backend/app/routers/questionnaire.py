"""
Questionnaire router — session management, answer upsert, plan generation, and xlsx download.

All endpoints use DEFAULT_USER_ID for Phase 1 POC.
Phase 2: swap in real user_id from JWT token.
"""
import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.constants import DEFAULT_USER_ID
from app.db.database import get_db
from app.db.models import GeneratedWorkbook, QuestionnaireAnswer, QuestionnaireSession
from app.schemas.questionnaire import (
    AnswerRead,
    AnswerUpsert,
    GenerateResult,
    SessionDetail,
    SessionListItem,
    SessionRead,
)
from app.services.questionnaire_generator import build_workbook_json

router = APIRouter()

_TOKEN_TTL_HOURS = 24


# ── Session endpoints ─────────────────────────────────────────────────────────

@router.post(
    "/questionnaire/sessions",
    response_model=SessionRead,
    status_code=201,
    summary="Start a new questionnaire session",
    tags=["questionnaire"],
)
def create_session(db: Session = Depends(get_db)) -> SessionRead:
    """Create and return a new questionnaire session."""
    # TODO[SECURITY]: use real user_id from JWT (Phase 2)
    session = QuestionnaireSession(user_id=DEFAULT_USER_ID)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionRead.model_validate(session)


@router.get(
    "/questionnaire/sessions",
    response_model=list[SessionListItem],
    summary="List all questionnaire sessions for the current user",
    tags=["questionnaire"],
)
def list_sessions(db: Session = Depends(get_db)) -> list[SessionListItem]:
    """Return all sessions for DEFAULT_USER_ID, newest first."""
    # TODO[SECURITY]: use real user_id from JWT (Phase 2)
    sessions = (
        db.query(QuestionnaireSession)
        .filter(QuestionnaireSession.user_id == DEFAULT_USER_ID)
        .order_by(QuestionnaireSession.created_at.desc())
        .all()
    )
    return [SessionListItem.model_validate(s) for s in sessions]


@router.get(
    "/questionnaire/sessions/{session_id}",
    response_model=SessionDetail,
    summary="Get a questionnaire session with all its answers",
    tags=["questionnaire"],
    responses={404: {"description": "Session not found"}},
)
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionDetail:
    """Return session metadata plus all answers."""
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    answers = (
        db.query(QuestionnaireAnswer)
        .filter(QuestionnaireAnswer.session_id == session_id)
        .order_by(QuestionnaireAnswer.answered_at)
        .all()
    )
    return SessionDetail(
        session=SessionRead.model_validate(session),
        answers=[AnswerRead.model_validate(a) for a in answers],
    )


# ── Answer upsert ─────────────────────────────────────────────────────────────

@router.put(
    "/questionnaire/sessions/{session_id}/answers",
    response_model=AnswerRead,
    summary="Upsert an answer for a questionnaire session",
    tags=["questionnaire"],
    responses={404: {"description": "Session not found"}},
)
def upsert_answer(
    session_id: str,
    body: AnswerUpsert,
    db: Session = Depends(get_db),
) -> AnswerRead:
    """
    Insert or update an answer for the given question_id.
    Also updates session.current_question_id, completed_count, and updated_at.
    """
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Upsert: find existing answer for this question or create a new one
    existing = (
        db.query(QuestionnaireAnswer)
        .filter(
            QuestionnaireAnswer.session_id == session_id,
            QuestionnaireAnswer.question_id == body.question_id,
        )
        .first()
    )

    if existing:
        existing.answer_json = body.answer_json
        existing.section_number = body.section_number
        existing.answered_at = datetime.now(timezone.utc)
        answer = existing
    else:
        answer = QuestionnaireAnswer(
            session_id=session_id,
            question_id=body.question_id,
            section_number=body.section_number,
            answer_json=body.answer_json,
        )
        db.add(answer)

    # Update session progress tracking
    session.current_question_id = body.question_id
    session.current_section = body.section_number
    # Recount completed answers to stay accurate after any upserts
    session.updated_at = datetime.now(timezone.utc)

    db.flush()

    # Recount distinct answered questions
    count = (
        db.query(QuestionnaireAnswer)
        .filter(QuestionnaireAnswer.session_id == session_id)
        .count()
    )
    session.completed_count = count

    db.commit()
    db.refresh(answer)
    return AnswerRead.model_validate(answer)


# ── Generate endpoint ─────────────────────────────────────────────────────────

@router.post(
    "/questionnaire/sessions/{session_id}/generate",
    response_model=GenerateResult,
    status_code=202,
    summary="Generate a longevity plan from questionnaire answers",
    tags=["questionnaire"],
    responses={
        404: {"description": "Session not found"},
        500: {"description": "Plan generation failed"},
    },
)
def generate_plan(session_id: str, db: Session = Depends(get_db)) -> GenerateResult:
    """
    Build workbook JSON from answers, ingest into the DB as a Plan,
    and create a time-limited download token for the xlsx file.
    """
    # Import here to avoid circular import at module level
    from app.services.plan_ingest import ingest_from_workbook_json

    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        # 1. Build workbook JSON from questionnaire answers
        workbook_json = build_workbook_json(session_id, db)

        # 2. Ingest into DB (creates Plan, TaskTemplates, RotationDays, Screenings, DailyTodos)
        # TODO[SECURITY]: use real user_id from JWT (Phase 2)
        ingest_result = ingest_from_workbook_json(workbook_json, db, DEFAULT_USER_ID)

        # 3. Create GeneratedWorkbook record with a 24-hour download token
        xlsx_token = str(uuid.uuid4())
        token_expires_at = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)
        workbook_record = GeneratedWorkbook(
            session_id=session_id,
            plan_id=ingest_result.get("plan_id"),
            version=1,
            workbook_json=json.dumps(workbook_json),
            xlsx_token=xlsx_token,
            token_expires_at=token_expires_at,
        )
        db.add(workbook_record)

        # 4. Mark session as plan_generated
        session.status = "plan_generated"
        session.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(workbook_record)

        return GenerateResult(
            workbook_id=workbook_record.id,
            xlsx_token=xlsx_token,
            plan_id=ingest_result.get("plan_id"),
        )

    except Exception as exc:
        # Log server-side; return generic 500 to client (no stack trace leakage)
        print(f"[questionnaire] generate failed for session {session_id}: {exc}")
        session.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plan generation failed. Please try again.",
        ) from exc


# ── Download endpoint ─────────────────────────────────────────────────────────

@router.get(
    "/questionnaire/download/{token}",
    summary="Download the generated xlsx file using a one-time token",
    tags=["questionnaire"],
    responses={
        404: {"description": "Token not found or expired"},
    },
)
def download_xlsx(token: str, db: Session = Depends(get_db)) -> StreamingResponse:
    """
    Stream the personalised xlsx file.
    The token is valid for 24 hours and is invalidated immediately after download.
    """
    from app.services.workbook_to_xlsx import generate_xlsx

    record = (
        db.query(GeneratedWorkbook)
        .filter(GeneratedWorkbook.xlsx_token == token)
        .first()
    )

    now = datetime.now(timezone.utc)

    if not record or record.token_expires_at is None:
        raise HTTPException(status_code=404, detail="Token not found or expired.")

    # Normalise token_expires_at to UTC-aware for comparison
    expires = record.token_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now >= expires:
        raise HTTPException(status_code=404, detail="Token not found or expired.")

    try:
        workbook_json = json.loads(record.workbook_json)
        xlsx_bytes = generate_xlsx(workbook_json)
    except FileNotFoundError as exc:
        print(f"[questionnaire] xlsx template missing: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="xlsx template not available.",
        ) from exc

    # Invalidate token immediately after generating the file (mark as used)
    record.token_expires_at = now - timedelta(seconds=1)
    db.commit()

    name = workbook_json.get("personal_settings", {}).get("name", "longevity") or "longevity"
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
    filename = f"{safe_name}_longevity_plan.xlsx"

    import io
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
