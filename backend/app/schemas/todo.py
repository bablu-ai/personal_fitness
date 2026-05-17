import json
from datetime import date, datetime
from pydantic import BaseModel, model_validator
from typing import Any


class Exercise(BaseModel):
    """Per-exercise detail embedded in a workout block — from exercises_json column."""
    name: str
    category: str | None = None
    setup: str | None = None
    starting_position: str | None = None
    how_to: str | None = None
    bracing_cue: str | None = None
    common_mistakes: str | None = None
    week1_dosage: str | None = None
    safety_notes: str | None = None
    why_it_matters: str | None = None
    video_link: str | None = None
    gif_link: str | None = None


class TaskTemplateOut(BaseModel):
    id: str
    pillar: str
    name: str
    description: str | None
    schedule: str | None
    timing: str | None
    target_value: str | None
    unit: str | None
    benefit_tags: str | None
    source_key: str | None
    link: str | None
    video_link: str | None
    safety_notes: str | None
    how_to: str | None
    why_mechanism: str | None
    is_reference: bool
    extra_metadata: dict[str, Any] | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_extra_metadata(cls, data: Any) -> Any:
        # extra_metadata is stored as a JSON string in DB — decode it for the response
        if hasattr(data, "__dict__"):
            raw = getattr(data, "extra_metadata", None)
            if isinstance(raw, str):
                try:
                    data.__dict__["extra_metadata"] = json.loads(raw)
                except (ValueError, AttributeError):
                    pass
        elif isinstance(data, dict):
            raw = data.get("extra_metadata")
            if isinstance(raw, str):
                try:
                    data["extra_metadata"] = json.loads(raw)
                except ValueError:
                    pass
        return data


class RelatedExercise(BaseModel):
    id: str
    name: str
    how_to: str | None
    video_link: str | None
    safety_notes: str | None
    target_value: str | None


class TaskDetailOut(TaskTemplateOut):
    related_exercises: list[RelatedExercise] = []
    exercises: list[Exercise] = []


class DailyTodoOut(BaseModel):
    id: str
    date: date
    completed: bool
    completed_at: datetime | None
    actual_value: str | None
    notes: str | None
    template: TaskTemplateOut

    model_config = {"from_attributes": True}


class TodoUpdateRequest(BaseModel):
    completed: bool
    actual_value: str | None = None
    notes: str | None = None


class DaySummary(BaseModel):
    date: date
    total: int
    completed: int
    completion_pct: float
    by_pillar: dict[str, dict]
