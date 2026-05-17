"""
Benefit scorer — open architecture.
Weights and outcome definitions come from benefit_config.json.
Edit the JSON file to add outcomes, change weights, or rename pillars. No code changes needed.
"""
import json
from datetime import date
from sqlalchemy.orm import Session
from app.db.models import DailyTodo, TaskTemplate
from app.constants import BENEFIT_CONFIG_PATH
from app.schemas.benefits import BenefitScore, BenefitScoresResponse


def _load_config() -> dict:
    if BENEFIT_CONFIG_PATH.exists():
        return json.loads(BENEFIT_CONFIG_PATH.read_text())
    return {"weights": {}, "outcome_labels": {}, "outcome_icons": {}}


def calculate_benefit_scores(
    db: Session,
    target_date: date,
    user_id: str = "default",
) -> BenefitScoresResponse:
    config = _load_config()
    weights: dict[str, dict[str, float]] = config.get("weights", {})
    labels: dict[str, str] = config.get("outcome_labels", {})
    icons: dict[str, str] = config.get("outcome_icons", {})

    todos = (
        db.query(DailyTodo)
        .filter(DailyTodo.date == target_date, DailyTodo.user_id == user_id)
        .all()
    )

    # Aggregate completion by pillar
    pillar_stats: dict[str, dict[str, int]] = {}
    for todo in todos:
        template = db.get(TaskTemplate, todo.template_id)
        if not template:
            continue
        pillar = template.pillar
        if pillar not in pillar_stats:
            pillar_stats[pillar] = {"completed": 0, "total": 0}
        pillar_stats[pillar]["total"] += 1
        if todo.completed:
            pillar_stats[pillar]["completed"] += 1

    scores: list[BenefitScore] = []
    for outcome, pillar_weights in weights.items():
        total_weight = sum(pillar_weights.values())
        if total_weight == 0:
            continue

        raw_score = 0.0
        for pillar, weight in pillar_weights.items():
            stats = pillar_stats.get(pillar, {"completed": 0, "total": 1})
            rate = stats["completed"] / stats["total"] if stats["total"] > 0 else 0.0
            raw_score += rate * (weight / total_weight)

        scores.append(BenefitScore(
            outcome=outcome,
            label=labels.get(outcome, outcome.replace("_", " ").title()),
            score_pct=round(raw_score * 100, 1),
            icon=icons.get(outcome),
        ))

    return BenefitScoresResponse(date=str(target_date), scores=scores)
