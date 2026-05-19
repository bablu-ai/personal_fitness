"""Pydantic schemas for questionnaire endpoints."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionRead(BaseModel):
    id: str
    user_id: str
    status: str
    current_question_id: str | None
    current_section: int
    completed_count: int
    total_questions: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionListItem(BaseModel):
    id: str
    status: str
    completed_count: int
    total_questions: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnswerUpsert(BaseModel):
    question_id: str
    answer_json: str
    section_number: int


class AnswerRead(BaseModel):
    id: str
    question_id: str
    section_number: int
    answer_json: str
    answered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetail(BaseModel):
    session: SessionRead
    answers: list[AnswerRead]


class GenerateResult(BaseModel):
    workbook_id: str
    xlsx_token: str
    plan_id: str | None
