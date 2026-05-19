import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, Text, Integer, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Phase 2: populated with real OAuth user IDs; "default" for single-user POC
    user_id: Mapped[str] = mapped_column(String, default="default", index=True)
    # User-settable start date for 30-day rotation cycling
    rotation_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Normalized JSON snapshot produced by the AI ingest pipeline — used by agent chat
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Review lifecycle: draft (under review, not driving todos) | active (approved) | archived (superseded)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active", server_default="active")
    # Concurrency guard: bumped on every plan_json write; stale-base saves rejected with 409
    json_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    task_templates: Mapped[list["TaskTemplate"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    rotation_days: Mapped[list["RotationDay"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    screenings: Mapped[list["Screening"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class TaskTemplate(Base):
    """
    One row per task from the Excel workbook.
    Pillar comes from sheet name — not hardcoded — so new sheets add new pillars automatically.
    """
    __tablename__ = "task_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("plans.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, default="default", index=True)

    pillar: Mapped[str] = mapped_column(String, nullable=False)        # from Excel sheet name
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    schedule: Mapped[str | None] = mapped_column(String)
    timing: Mapped[str | None] = mapped_column(String)
    target_value: Mapped[str | None] = mapped_column(String)
    unit: Mapped[str | None] = mapped_column(String)
    benefit_tags: Mapped[str | None] = mapped_column(Text)
    # Rich detail fields — promoted from extra_metadata for frontend rendering
    source_key: Mapped[str | None] = mapped_column(String)
    link: Mapped[str | None] = mapped_column(String)
    video_link: Mapped[str | None] = mapped_column(String)
    safety_notes: Mapped[str | None] = mapped_column(Text)
    how_to: Mapped[str | None] = mapped_column(Text)
    why_mechanism: Mapped[str | None] = mapped_column(Text)
    # Reference rows are parsed but never generate daily todos (shown in Reference tab)
    is_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_metadata: Mapped[str | None] = mapped_column(Text)           # JSON catch-all
    # JSON list of IngestedExercise dicts for workout blocks (brief_today Priority/Secondary/Warm-up blocks)
    exercises_json: Mapped[str | None] = mapped_column(Text)
    # Edit-tracking origin: ingest | user_added | user_edited | agent_fixed
    origin: Mapped[str] = mapped_column(String, nullable=False, default="ingest", server_default="ingest")

    plan: Mapped["Plan"] = relationship(back_populates="task_templates")
    daily_todos: Mapped[list["DailyTodo"]] = relationship(back_populates="template")


class DailyTodo(Base):
    __tablename__ = "daily_todos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    template_id: Mapped[str] = mapped_column(String, ForeignKey("task_templates.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, default="default", index=True)

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_value: Mapped[str | None] = mapped_column(String)           # what user actually logged
    notes: Mapped[str | None] = mapped_column(Text)
    # Per-day overlay JSON {"name"?: str, "target_value"?: str, "hidden"?: bool} — overrides template for this date only
    override_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    template: Mapped["TaskTemplate"] = relationship(back_populates="daily_todos")


class RotationDay(Base):
    """One row per day (1–30) of the 30-day exercise rotation."""
    __tablename__ = "rotation_days"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("plans.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, default="default", index=True)

    day_number: Mapped[int] = mapped_column(Integer, nullable=False)    # 1–30
    week_number: Mapped[int | None] = mapped_column(Integer)           # 1–4
    block_name: Mapped[str] = mapped_column(String, nullable=False)    # workout focus / session name
    # v3 fields (null when v4 workbook uploaded)
    warm_up: Mapped[str | None] = mapped_column(Text)
    priority_block: Mapped[str | None] = mapped_column(Text)
    secondary_block: Mapped[str | None] = mapped_column(Text)
    cardio_steps: Mapped[str | None] = mapped_column(String)
    cool_down: Mapped[str | None] = mapped_column(Text)
    nutrition_focus: Mapped[str | None] = mapped_column(Text)
    intensity_cap: Mapped[str | None] = mapped_column(String)
    source_key: Mapped[str | None] = mapped_column(String)
    sets: Mapped[str | None] = mapped_column(String)
    reps: Mapped[str | None] = mapped_column(String)
    duration: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(Text)
    # v4 fields — time-budget + exercise-name columns
    morning_time: Mapped[str | None] = mapped_column(String)           # "5:40 AM"
    warm_up_min: Mapped[str | None] = mapped_column(String)            # "8"
    upper_back_core_min: Mapped[str | None] = mapped_column(String)    # "12"
    secondary_min: Mapped[str | None] = mapped_column(String)          # "10"
    cool_down_min: Mapped[str | None] = mapped_column(String)          # "5"
    total_min: Mapped[str | None] = mapped_column(String)              # "55"
    fits_60: Mapped[str | None] = mapped_column(String)                # "Yes" / "✓"
    priority_exercises: Mapped[str | None] = mapped_column(Text)       # comma-separated list
    secondary_exercises: Mapped[str | None] = mapped_column(Text)      # comma-separated list
    week_rule: Mapped[str | None] = mapped_column(String)              # "Week 1: Easy / RPE 5-6"
    extra_metadata: Mapped[str | None] = mapped_column(Text)

    plan: Mapped["Plan"] = relationship(back_populates="rotation_days")
    completions: Mapped[list["RotationCompletion"]] = relationship(back_populates="rotation_day", cascade="all, delete-orphan")


class RotationCompletion(Base):
    """Records when a rotation day was completed (one row per calendar date)."""
    __tablename__ = "rotation_completions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    rotation_day_id: Mapped[str] = mapped_column(String, ForeignKey("rotation_days.id"), nullable=False)
    plan_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, default="default", index=True)
    completion_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=True)

    rotation_day: Mapped["RotationDay"] = relationship(back_populates="completions")


class Screening(Base):
    """
    Periodic health screening or blood marker check (annual, biannual, etc.).
    Parsed from the Screenings_Safety and Blood_Markers sheets.
    Not in daily todos — surfaces as 'due' alerts instead.
    """
    __tablename__ = "screenings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("plans.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, default="default", index=True)
    pillar: Mapped[str] = mapped_column(String, nullable=False)   # "screenings_safety" | "blood_markers"
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    frequency_months: Mapped[int | None] = mapped_column(Integer)  # 12 = annual, 6 = biannual
    target_value: Mapped[str | None] = mapped_column(String)       # optimal range for blood markers
    extra_metadata: Mapped[str | None] = mapped_column(Text)

    plan: Mapped["Plan"] = relationship(back_populates="screenings")
    records: Mapped[list["ScreeningRecord"]] = relationship(back_populates="screening", cascade="all, delete-orphan")


class ScreeningRecord(Base):
    """Records when a screening was completed."""
    __tablename__ = "screening_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    screening_id: Mapped[str] = mapped_column(String, ForeignKey("screenings.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, default="default", index=True)
    completed_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    screening: Mapped["Screening"] = relationship(back_populates="records")


# ── Auth ─────────────────────────────────────────────────────────────────────

class User(Base):
    """Registered user. Phase 1: POC with stub auth. Phase 2: enforce MFA, refresh rotation."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Questionnaire ─────────────────────────────────────────────────────────────

class QuestionnaireSession(Base):
    """One questionnaire fill-out session per user attempt."""
    __tablename__ = "questionnaire_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    # TODO[SECURITY]: use real user_id from JWT when Phase 2 auth is active
    user_id: Mapped[str] = mapped_column(String, nullable=False, default="default", index=True)
    # values: in_progress | completed | generating | plan_generated | failed
    status: Mapped[str] = mapped_column(String, nullable=False, default="in_progress")
    current_question_id: Mapped[str | None] = mapped_column(String, nullable=True)
    current_section: Mapped[int] = mapped_column(Integer, default=1)
    completed_count: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=40)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    answers: Mapped[list["QuestionnaireAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    workbooks: Mapped[list["GeneratedWorkbook"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class QuestionnaireAnswer(Base):
    """One answer per question per session (upsert on question_id)."""
    __tablename__ = "questionnaire_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("questionnaire_sessions.id"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String, nullable=False)
    section_number: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_json: Mapped[str] = mapped_column(Text, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("session_id", "question_id"),)

    session: Mapped["QuestionnaireSession"] = relationship(back_populates="answers")


class GeneratedWorkbook(Base):
    """Workbook JSON generated from questionnaire answers, with a short-lived download token."""
    __tablename__ = "generated_workbooks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("questionnaire_sessions.id"), nullable=False
    )
    plan_id: Mapped[str | None] = mapped_column(String, ForeignKey("plans.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    workbook_json: Mapped[str] = mapped_column(Text, nullable=False)
    xlsx_token: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["QuestionnaireSession"] = relationship(back_populates="workbooks")
