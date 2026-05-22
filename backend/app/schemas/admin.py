"""Pydantic schemas for admin questionnaire views."""
from datetime import datetime

from pydantic import BaseModel


class AdminQuestionnaireSession(BaseModel):
    id: str
    user_id: str
    user_email: str | None
    status: str
    completed_count: int
    total_questions: int
    questionnaire_version: int
    created_at: datetime
    updated_at: datetime


class AdminQuestionAnswer(BaseModel):
    question_id: str
    question_snapshot_id: str | None
    section_number: int
    question_number: int
    question_text: str
    question_type: str
    answer_json: str | None
    formatted_answer: str | None
    answered_at: datetime | None


class AdminQuestionnaireDetail(BaseModel):
    session: AdminQuestionnaireSession
    questions: list[AdminQuestionAnswer]
