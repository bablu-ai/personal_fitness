"""Admin-only questionnaire inspection and export routes."""
from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import QuestionnaireAnswer, QuestionnaireQuestion, QuestionnaireSession, User
from app.routers.auth import get_current_user
from app.schemas.admin import (
    AdminQuestionAnswer,
    AdminQuestionnaireDetail,
    AdminQuestionnaireSession,
)
from app.services.questionnaire_catalog import ensure_questionnaire_questions

router = APIRouter()


def _admin_emails() -> set[str]:
    return {
        email.strip().lower()
        for email in os.getenv("ADMIN_EMAILS", "").split(",")
        if email.strip()
    }


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow only logged-in users whose email is in ADMIN_EMAILS."""
    if current_user.email.lower() not in _admin_emails():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized.",
        )
    return current_user


def _session_out(session: QuestionnaireSession, user_email: str | None) -> AdminQuestionnaireSession:
    return AdminQuestionnaireSession(
        id=session.id,
        user_id=session.user_id,
        user_email=user_email,
        status=session.status,
        completed_count=session.completed_count,
        total_questions=session.total_questions,
        questionnaire_version=session.questionnaire_version,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _format_answer(answer_json: str | None) -> str | None:
    if not answer_json:
        return None
    try:
        parsed: Any = json.loads(answer_json)
    except json.JSONDecodeError:
        return answer_json

    if parsed is None:
        return None
    if isinstance(parsed, str):
        return parsed
    if isinstance(parsed, (int, float, bool)):
        return str(parsed)
    if isinstance(parsed, list):
        return ", ".join(str(item) for item in parsed)
    if isinstance(parsed, dict):
        parts: list[str] = []
        for key in ("value", "choice", "answer"):
            if key in parsed and parsed[key] not in (None, ""):
                parts.append(str(parsed[key]))
                break
        if "choices" in parsed and isinstance(parsed["choices"], list):
            parts.append(", ".join(str(item) for item in parsed["choices"]))
        for key in ("detail", "text", "other"):
            if key in parsed and parsed[key] not in (None, ""):
                parts.append(str(parsed[key]))
        return " - ".join(part for part in parts if part) or json.dumps(parsed, ensure_ascii=False)
    return str(parsed)


def _load_session_detail(db: Session, session_id: str) -> AdminQuestionnaireDetail:
    session = db.get(QuestionnaireSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    ensure_questionnaire_questions(db, session.questionnaire_version)
    db.commit()

    user = db.get(User, session.user_id)
    questions = (
        db.query(QuestionnaireQuestion)
        .filter(QuestionnaireQuestion.version == session.questionnaire_version)
        .order_by(QuestionnaireQuestion.question_number)
        .all()
    )
    answers = {
        answer.question_id: answer
        for answer in db.query(QuestionnaireAnswer)
        .filter(QuestionnaireAnswer.session_id == session_id)
        .all()
    }

    return AdminQuestionnaireDetail(
        session=_session_out(session, user.email if user else None),
        questions=[
            AdminQuestionAnswer(
                question_id=question.question_id,
                question_snapshot_id=answer.question_snapshot_id if answer else question.id,
                section_number=question.section_number,
                question_number=question.question_number,
                question_text=question.question_text,
                question_type=question.question_type,
                answer_json=answer.answer_json if answer else None,
                formatted_answer=_format_answer(answer.answer_json if answer else None),
                answered_at=answer.answered_at if answer else None,
            )
            for question in questions
            for answer in [answers.get(question.question_id)]
        ],
    )


@router.get(
    "/admin/questionnaires/sessions",
    response_model=list[AdminQuestionnaireSession],
    tags=["admin"],
)
def list_questionnaire_sessions(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminQuestionnaireSession]:
    """List all questionnaire sessions across users."""
    ensure_questionnaire_questions(db)
    db.commit()
    rows = (
        db.query(QuestionnaireSession, User.email)
        .outerjoin(User, QuestionnaireSession.user_id == User.id)
        .order_by(QuestionnaireSession.updated_at.desc())
        .all()
    )
    return [_session_out(session, email) for session, email in rows]


@router.get(
    "/admin/questionnaires/sessions/{session_id}",
    response_model=AdminQuestionnaireDetail,
    tags=["admin"],
)
def get_questionnaire_session(
    session_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminQuestionnaireDetail:
    """Return all versioned questions and answers for a questionnaire session."""
    return _load_session_detail(db, session_id)


@router.get(
    "/admin/questionnaires/sessions/{session_id}/export.txt",
    tags=["admin"],
)
def export_questionnaire_session(
    session_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Export a questionnaire session as plain text."""
    detail = _load_session_detail(db, session_id)
    user_label = detail.session.user_email or detail.session.user_id
    lines = [
        f"Questionnaire Session: {detail.session.id}",
        f"User: {user_label}",
        f"Status: {detail.session.status}",
        f"Created: {detail.session.created_at.isoformat()}",
        "",
    ]
    for index, item in enumerate(detail.questions, start=1):
        lines.append(f"Q{index}. {item.question_text}")
        lines.append(f"Ans{index}: {item.formatted_answer or ''}")
        lines.append("------")

    return Response(
        content="\n".join(lines) + "\n",
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="questionnaire_{session_id}.txt"'},
    )
