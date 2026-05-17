from pydantic import BaseModel


class BenefitScore(BaseModel):
    outcome: str
    label: str
    score_pct: float
    icon: str | None = None


class BenefitScoresResponse(BaseModel):
    date: str
    scores: list[BenefitScore]
