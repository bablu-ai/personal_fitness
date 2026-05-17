from datetime import datetime
from pydantic import BaseModel


class PlanOut(BaseModel):
    id: str
    name: str
    uploaded_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    plan: PlanOut
    tasks_imported: int
    pillars_found: list[str]
    rotation_days_imported: int = 0
