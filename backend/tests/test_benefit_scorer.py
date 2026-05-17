from unittest.mock import MagicMock, patch
from datetime import date
from app.services.benefit_scorer import calculate_benefit_scores
from app.schemas.benefits import BenefitScoresResponse


MOCK_CONFIG = {
    "weights": {
        "longevity": {"exercise": 50, "nutrition": 50}
    },
    "outcome_labels": {"longevity": "Longevity"},
    "outcome_icons": {"longevity": "star"},
}


def _mock_todo(pillar: str, completed: bool):
    todo = MagicMock()
    todo.completed = completed
    todo.template_id = f"tmpl-{pillar}"
    template = MagicMock()
    template.pillar = pillar
    todo.template = template
    return todo, template


def test_full_completion_gives_100():
    db = MagicMock()
    exercise_todo, exercise_tmpl = _mock_todo("exercise", True)
    nutrition_todo, nutrition_tmpl = _mock_todo("nutrition", True)

    db.query.return_value.filter.return_value.all.return_value = [exercise_todo, nutrition_todo]
    db.get.side_effect = lambda model, id: exercise_tmpl if "exercise" in id else nutrition_tmpl

    with patch("app.services.benefit_scorer._load_config", return_value=MOCK_CONFIG):
        result = calculate_benefit_scores(db, date.today())

    assert isinstance(result, BenefitScoresResponse)
    score = next(s for s in result.scores if s.outcome == "longevity")
    assert score.score_pct == 100.0


def test_no_completion_gives_0():
    db = MagicMock()
    exercise_todo, exercise_tmpl = _mock_todo("exercise", False)
    nutrition_todo, nutrition_tmpl = _mock_todo("nutrition", False)

    db.query.return_value.filter.return_value.all.return_value = [exercise_todo, nutrition_todo]
    db.get.side_effect = lambda model, id: exercise_tmpl if "exercise" in id else nutrition_tmpl

    with patch("app.services.benefit_scorer._load_config", return_value=MOCK_CONFIG):
        result = calculate_benefit_scores(db, date.today())

    score = next(s for s in result.scores if s.outcome == "longevity")
    assert score.score_pct == 0.0


def test_partial_completion():
    db = MagicMock()
    exercise_todo, exercise_tmpl = _mock_todo("exercise", True)
    nutrition_todo, nutrition_tmpl = _mock_todo("nutrition", False)

    db.query.return_value.filter.return_value.all.return_value = [exercise_todo, nutrition_todo]
    db.get.side_effect = lambda model, id: exercise_tmpl if "exercise" in id else nutrition_tmpl

    with patch("app.services.benefit_scorer._load_config", return_value=MOCK_CONFIG):
        result = calculate_benefit_scores(db, date.today())

    score = next(s for s in result.scores if s.outcome == "longevity")
    assert score.score_pct == 50.0


def test_empty_todos_returns_zero_pct_scores():
    # With no todos, scores are still computed but at 0% (pillar_stats defaults to 0/1)
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    with patch("app.services.benefit_scorer._load_config", return_value=MOCK_CONFIG):
        result = calculate_benefit_scores(db, date.today())

    assert len(result.scores) == len(MOCK_CONFIG["weights"])
    assert all(s.score_pct == 0.0 for s in result.scores)
