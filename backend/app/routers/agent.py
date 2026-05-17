import os
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import llm_agent
from app.services.plan_ingest import IngestResult, run_ingest

# TODO[SECURITY]: Add rate limiting on this endpoint before production (OWASP LLM10)
# TODO[SECURITY]: Add per-user token budget tracking (OWASP LLM10)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/agent/chat", response_model=ChatResponse)
def agent_chat(body: ChatRequest, db: Session = Depends(get_db)):
    reply = llm_agent.chat(body.message, db)
    return ChatResponse(reply=reply)


@router.post(
    "/agent/ingest",
    response_model=IngestResult,
    summary="AI-powered plan ingest — accepts .xlsx or .json",
    description=(
        "Uploads a workbook or JSON file, extracts tasks via LLM (provider set by LLM_INGEST_MODEL), "
        "saves Plan + TaskTemplates + RotationDays + Screenings to the DB, "
        "and pre-generates 30 days of DailyTodo rows."
    ),
)
async def agent_ingest(
    file: UploadFile = File(...),
    rotation_start_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # TODO[SECURITY]: Add per-user token budget to prevent runaway LLM costs (OWASP LLM10)
    has_key = bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
    )
    if not has_key:
        raise HTTPException(
            status_code=503,
            detail="AI ingest requires an API key (GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY) in .env.",
        )

    filename = file.filename or "plan"
    if not (filename.endswith(".xlsx") or filename.endswith(".json")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .json files are accepted.")

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

    try:
        result = run_ingest(db, contents, filename, parsed_start)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Ingest failed: {exc}") from exc

    return result
