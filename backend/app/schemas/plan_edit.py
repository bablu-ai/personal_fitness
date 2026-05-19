"""
Pydantic v2 request/response models for the plan editor API.

All input models use ``extra="forbid"`` to reject unknown fields at the boundary.
Output models are more permissive (they come from the DB, not from untrusted input).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ── Sub-models ────────────────────────────────────────────────────────────────


class ReviewFlag(BaseModel):
    """One Tier-B advisory or blocking flag from the plan reviewer."""

    flag_id: str
    task_id: str | None = None
    code: str
    message: str
    suggestion: str | bool | None = None
    blocking: bool


class ReviewEnvelope(BaseModel):
    """The ``review`` object inside ``PlanReviewOut``."""

    auto_removed: list[dict] = Field(default_factory=list)
    agent_fixed: list[dict] = Field(default_factory=list)
    flags: list[ReviewFlag] = Field(default_factory=list)
    advisor_notes: list[str] = Field(default_factory=list)


class TaskOut(BaseModel):
    """Serialized view of one ``TaskTemplate`` row as returned to the client."""

    task_id: str
    plan_id: str
    pillar: str
    name: str
    description: str | None = None
    schedule: str | None = None
    timing: str | None = None
    target_value: str | None = None
    unit: str | None = None
    benefit_tags: str | None = None
    source_key: str | None = None
    link: str | None = None
    video_link: str | None = None
    safety_notes: str | None = None
    how_to: str | None = None
    why_mechanism: str | None = None
    is_reference: bool = False
    origin: str = "ingest"


class TaskUpsert(BaseModel):
    """Payload for POST /tasks and PUT /tasks/{task_id}."""

    model_config = ConfigDict(extra="forbid")

    # Required fields with validation constraints
    name: str = Field(min_length=1, max_length=200)
    pillar: str = Field(min_length=1, max_length=80)

    # All other fields are optional
    description: str | None = None
    schedule: str | None = None
    timing: str | None = None
    target_value: str | None = None
    unit: str | None = None
    benefit_tags: str | None = None
    source_key: str | None = None
    link: str | None = None
    video_link: str | None = None
    safety_notes: str | None = None
    how_to: str | None = None
    why_mechanism: str | None = None
    is_reference: bool = False


class RotationDayOut(BaseModel):
    """Serialized view of one ``RotationDay`` row."""

    id: str
    plan_id: str
    day_number: int
    week_number: int | None = None
    block_name: str
    morning_time: str | None = None
    warm_up_min: str | None = None
    upper_back_core_min: str | None = None
    secondary_min: str | None = None
    cool_down_min: str | None = None
    total_min: str | None = None
    fits_60: str | None = None
    priority_exercises: str | None = None
    secondary_exercises: str | None = None
    week_rule: str | None = None
    notes: str | None = None


class RotationDayUpsert(BaseModel):
    """Payload for PUT /rotation/{day_number}."""

    model_config = ConfigDict(extra="forbid")

    day_number: int  # required

    week_number: int | None = None
    block_name: str | None = None
    morning_time: str | None = None
    warm_up_min: str | None = None
    upper_back_core_min: str | None = None
    secondary_min: str | None = None
    cool_down_min: str | None = None
    total_min: str | None = None
    fits_60: str | None = None
    priority_exercises: str | None = None
    secondary_exercises: str | None = None
    week_rule: str | None = None
    notes: str | None = None


class ScreeningOut(BaseModel):
    """Serialized view of one ``Screening`` row."""

    id: str
    plan_id: str
    pillar: str
    name: str
    description: str | None = None
    frequency_months: int | None = None
    target_value: str | None = None


class ScreeningUpsert(BaseModel):
    """Payload for PUT /screenings/{screening_id}."""

    model_config = ConfigDict(extra="forbid")

    # Required fields
    name: str = Field(min_length=1)
    pillar: str = Field(min_length=1)

    # Optional fields
    description: str | None = None
    frequency_months: int | None = None
    target_value: str | None = None


class PlanReviewOut(BaseModel):
    """Full plan review response — the canonical read shape for the editor UI."""

    plan_id: str
    status: str
    json_version: int
    tasks_by_pillar: dict[str, list[TaskOut]]
    rotation_days: list[RotationDayOut]
    screenings: list[ScreeningOut]
    review: ReviewEnvelope


class ActivateOut(BaseModel):
    """Response for POST /plan/{plan_id}/activate."""

    plan_id: str
    status: str


class FlagActionOut(BaseModel):
    """Response for POST /plan/{plan_id}/flags/{flag_id}/apply|dismiss."""

    plan_id: str
    flag_id: str
    action: str  # "applied" | "dismissed"
