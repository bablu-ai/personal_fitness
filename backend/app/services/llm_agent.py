"""
LLM Agent — Phase 1 stub.
Provider-aware: set LLM_MODEL to a model name to select the provider automatically.
  gemini-*  → Google Generative AI (needs GEMINI_API_KEY or GOOGLE_API_KEY)
  claude-*  → Anthropic (needs ANTHROPIC_API_KEY)
  anything  → OpenAI (needs OPENAI_API_KEY)
GEMINI_LLM_MODEL overrides the specific Gemini model when using the Google provider.
All LLM calls are proxied through the backend — never called from the browser.
# TODO[SECURITY]: Add per-session token limits before production (OWASP LLM10)
# TODO[SECURITY]: Add input sanitization before injecting into prompts (OWASP LLM01)
# TODO[SECURITY]: Rate-limit /api/agent/chat endpoint (OWASP LLM10)
"""
import os
from datetime import date
from sqlalchemy.orm import Session
from app.db.models import DailyTodo, Plan, TaskTemplate
from app.services.benefit_scorer import calculate_benefit_scores

# Safety ceiling — prevents a huge workbook from consuming the entire context window.
_PLAN_JSON_CHAR_LIMIT = 60_000


def _is_agent_enabled() -> bool:
    return bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
    )


def _make_chat_llm():
    """Create LLM client for chat — provider detected from LLM_MODEL prefix."""
    model = os.getenv("LLM_MODEL", "gpt-4.1-nano")

    if model.startswith("gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        gemini_model = os.getenv("GEMINI_LLM_MODEL", model)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        return ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=api_key,
            temperature=0.3,
        )

    if model.startswith("claude"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, temperature=0.3)  # type: ignore[call-arg]

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=model, temperature=0.3)


def _get_plan_json(db: Session, user_id: str) -> str:
    """Return the stored plan_json from the active plan, or empty string if absent."""
    plan = (
        db.query(Plan)
        .filter(Plan.is_active == True, Plan.user_id == user_id)  # noqa: E712
        .order_by(Plan.uploaded_at.desc())
        .first()
    )
    if not plan or not plan.plan_json:
        return ""

    raw = plan.plan_json
    if len(raw) > _PLAN_JSON_CHAR_LIMIT:
        raw = raw[:_PLAN_JSON_CHAR_LIMIT] + "\n... (truncated)"
    return raw


def _build_today_context(db: Session, user_id: str) -> str:
    """Build a summary of today's progress to ground the agent."""
    today = date.today()
    todos = (
        db.query(DailyTodo)
        .filter(DailyTodo.date == today, DailyTodo.user_id == user_id)
        .all()
    )

    completed = [t for t in todos if t.completed]
    pending = [t for t in todos if not t.completed]

    def todo_line(todo: DailyTodo) -> str:
        template = db.get(TaskTemplate, todo.template_id)
        if not template:
            return ""
        parts = [f"{template.pillar}: {template.name}"]
        if template.target_value:
            parts.append(f"(target: {template.target_value} {template.unit or ''})")
        return " ".join(parts)

    benefit_response = calculate_benefit_scores(db, today, user_id)
    benefit_summary = ", ".join(
        f"{s.label}: {s.score_pct}%" for s in benefit_response.scores
    )

    return "\n".join([
        f"Today is {today}.",
        f"Completed ({len(completed)}): {'; '.join(todo_line(t) for t in completed) or 'none'}",
        f"Pending ({len(pending)}): {'; '.join(todo_line(t) for t in pending) or 'none'}",
        f"Benefit scores: {benefit_summary or 'no data yet'}",
    ])


def chat(message: str, db: Session, user_id: str = "default") -> str:
    """
    Route a user message to the LLM agent.
    Returns the agent's response as a string.
    Falls back to a helpful stub if no API key is configured.
    """
    if not _is_agent_enabled():
        return (
            "AI assistant is not configured yet. "
            "Add GEMINI_API_KEY (or OPENAI_API_KEY) to your .env file to enable it."
        )

    try:
        today_context = _build_today_context(db, user_id)
        plan_json = _get_plan_json(db, user_id)

        plan_section = (
            f"\n\n--- FULL PLAN (JSON) ---\n{plan_json}"
            if plan_json
            else "\n\n--- FULL PLAN ---\nNo plan uploaded yet."
        )

        system_prompt = (
            "You are a personal longevity coach assistant. "
            "You have access to the user's complete longevity plan (tasks, supplements, "
            "exercise rotation, screenings, and reference material) as structured JSON below. "
            "Use it to answer specific questions about their plan, schedule, rotation days, "
            "supplement dosages, exercise instructions, or health screenings. "
            "Also use today's progress summary to give context-aware encouragement. "
            "Be concise, evidence-based, and encouraging. "
            "Never make medical diagnoses or replace professional medical advice.\n\n"
            f"--- TODAY'S PROGRESS ---\n{today_context}"
            f"{plan_section}"
        )

        llm = _make_chat_llm()
        from langchain_core.messages import HumanMessage, SystemMessage
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=message),
        ])
        return response.content  # type: ignore[return-value]

    except Exception:  # noqa: BLE001
        return "Sorry, I couldn't process that request. Please try again."
