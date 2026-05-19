"""
Tests for questionnaire endpoints:
  POST   /api/questionnaire/sessions
  GET    /api/questionnaire/sessions
  GET    /api/questionnaire/sessions/{id}
  PUT    /api/questionnaire/sessions/{id}/answers
  POST   /api/questionnaire/sessions/{id}/generate
  GET    /api/questionnaire/download/{token}
"""
import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db.models import GeneratedWorkbook


# ── Helpers ───────────────────────────────────────────────────────────────────

_BASIC_ANSWERS = [
    {"question_id": "q1_full_name",            "answer_json": '"Test User"',         "section_number": 1},
    {"question_id": "q2_date_of_birth",        "answer_json": '"1980-06-15"',         "section_number": 1},
    {"question_id": "q3_sex_at_birth",         "answer_json": '"Male"',               "section_number": 1},
    {"question_id": "q4_height_cm",            "answer_json": "175",                  "section_number": 1},
    {"question_id": "q5_weight_kg",            "answer_json": "80",                   "section_number": 1},
    {"question_id": "q16_dietary_pattern",     "answer_json": '"Omnivore"',           "section_number": 3},
    {"question_id": "q19_current_supplements", "answer_json": '["Creatine","Omega-3 fish oil"]', "section_number": 3},
    {"question_id": "q22_wake_time",           "answer_json": '"05:40"',              "section_number": 4},
    {"question_id": "q23_bed_time",            "answer_json": '"21:30"',              "section_number": 4},
    {"question_id": "q34_preferred_exercise_time", "answer_json": '"Morning"',        "section_number": 6},
]


def _create_session(client: TestClient) -> str:
    """Create a session and return its id."""
    resp = client.post("/api/questionnaire/sessions")
    assert resp.status_code == 201
    return resp.json()["id"]


def _fill_answers(client: TestClient, session_id: str) -> None:
    """Fill all basic answers for the given session."""
    for ans in _BASIC_ANSWERS:
        resp = client.put(f"/api/questionnaire/sessions/{session_id}/answers", json=ans)
        assert resp.status_code == 200


# ── Session CRUD ──────────────────────────────────────────────────────────────

def test_create_session(client: TestClient):
    """POST /sessions returns 201 with a valid session."""
    resp = client.post("/api/questionnaire/sessions")
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "in_progress"
    assert body["completed_count"] == 0
    assert body["total_questions"] == 40
    assert "id" in body


def test_list_sessions_includes_created(client: TestClient):
    """GET /sessions returns the session created in the same test."""
    sid = _create_session(client)
    resp = client.get("/api/questionnaire/sessions")
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()]
    assert sid in ids


def test_get_session_detail_not_found(client: TestClient):
    """GET /sessions/{id} for a non-existent id returns 404."""
    resp = client.get(f"/api/questionnaire/sessions/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_session_detail_returns_answers(client: TestClient):
    """GET /sessions/{id} returns session data plus answers list."""
    sid = _create_session(client)
    _fill_answers(client, sid)
    resp = client.get(f"/api/questionnaire/sessions/{sid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session"]["id"] == sid
    assert len(body["answers"]) == len(_BASIC_ANSWERS)


# ── Answer upsert ─────────────────────────────────────────────────────────────

def test_upsert_answer_creates_new(client: TestClient):
    """PUT /answers creates a new answer row and returns 200."""
    sid = _create_session(client)
    resp = client.put(
        f"/api/questionnaire/sessions/{sid}/answers",
        json={"question_id": "q1_full_name", "answer_json": '"Alice"', "section_number": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["question_id"] == "q1_full_name"
    assert body["answer_json"] == '"Alice"'


def test_upsert_answer_updates_existing(client: TestClient):
    """Second PUT with same question_id updates the row (no duplicate created)."""
    sid = _create_session(client)
    client.put(
        f"/api/questionnaire/sessions/{sid}/answers",
        json={"question_id": "q1_full_name", "answer_json": '"Alice"', "section_number": 1},
    )
    client.put(
        f"/api/questionnaire/sessions/{sid}/answers",
        json={"question_id": "q1_full_name", "answer_json": '"Alice Updated"', "section_number": 1},
    )

    # Only one answer should exist for this question
    detail = client.get(f"/api/questionnaire/sessions/{sid}")
    answers = detail.json()["answers"]
    q1_answers = [a for a in answers if a["question_id"] == "q1_full_name"]
    assert len(q1_answers) == 1
    assert q1_answers[0]["answer_json"] == '"Alice Updated"'


def test_upsert_answer_updates_completed_count(client: TestClient):
    """completed_count increments with each new unique question answered."""
    sid = _create_session(client)
    client.put(
        f"/api/questionnaire/sessions/{sid}/answers",
        json={"question_id": "q1_full_name", "answer_json": '"Alice"', "section_number": 1},
    )
    client.put(
        f"/api/questionnaire/sessions/{sid}/answers",
        json={"question_id": "q2_date_of_birth", "answer_json": '"1980-01-01"', "section_number": 1},
    )

    detail = client.get(f"/api/questionnaire/sessions/{sid}")
    assert detail.json()["session"]["completed_count"] == 2


def test_upsert_answer_session_not_found(client: TestClient):
    """PUT /answers for a non-existent session returns 404."""
    resp = client.put(
        f"/api/questionnaire/sessions/{uuid.uuid4()}/answers",
        json={"question_id": "q1_full_name", "answer_json": '"Alice"', "section_number": 1},
    )
    assert resp.status_code == 404


# ── Generate ──────────────────────────────────────────────────────────────────

def test_generate_returns_202_with_token(client: TestClient):
    """POST /generate after answering questions returns 202 with xlsx_token."""
    sid = _create_session(client)
    _fill_answers(client, sid)
    resp = client.post(f"/api/questionnaire/sessions/{sid}/generate")
    assert resp.status_code == 202
    body = resp.json()
    assert "xlsx_token" in body
    assert body["xlsx_token"]
    assert "workbook_id" in body
    assert "plan_id" in body
    assert body["plan_id"]  # a plan was created


def test_generate_sets_session_status(client: TestClient):
    """After generate, session.status == 'plan_generated'."""
    sid = _create_session(client)
    _fill_answers(client, sid)
    client.post(f"/api/questionnaire/sessions/{sid}/generate")
    detail = client.get(f"/api/questionnaire/sessions/{sid}")
    assert detail.json()["session"]["status"] == "plan_generated"


def test_generate_session_not_found(client: TestClient):
    """POST /generate for non-existent session returns 404."""
    resp = client.post(f"/api/questionnaire/sessions/{uuid.uuid4()}/generate")
    assert resp.status_code == 404


# ── Download ──────────────────────────────────────────────────────────────────

def test_download_valid_token(client: TestClient, db_session):
    """GET /download/{token} returns xlsx bytes for a valid token."""
    sid = _create_session(client)
    _fill_answers(client, sid)
    gen_resp = client.post(f"/api/questionnaire/sessions/{sid}/generate")
    token = gen_resp.json()["xlsx_token"]

    resp = client.get(f"/api/questionnaire/download/{token}")
    assert resp.status_code == 200
    ct = resp.headers.get("content-type", "")
    assert "spreadsheetml" in ct or "octet-stream" in ct


def test_download_expired_token(client: TestClient, db_session):
    """GET /download/{token} returns 404 when token is expired."""
    sid = _create_session(client)
    _fill_answers(client, sid)
    gen_resp = client.post(f"/api/questionnaire/sessions/{sid}/generate")
    assert gen_resp.status_code == 202
    token = gen_resp.json()["xlsx_token"]
    workbook_id = gen_resp.json()["workbook_id"]

    # Manually expire the token in DB
    record = db_session.get(GeneratedWorkbook, workbook_id)
    assert record is not None
    record.token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    resp = client.get(f"/api/questionnaire/download/{token}")
    assert resp.status_code == 404


def test_download_unknown_token(client: TestClient):
    """GET /download/{token} for a non-existent token returns 404."""
    resp = client.get(f"/api/questionnaire/download/{uuid.uuid4()}")
    assert resp.status_code == 404


# ── Stale-todo regression ─────────────────────────────────────────────────────

def test_generate_clears_stale_daily_todos(client: TestClient, db_session):
    """
    Regression: when /generate is called twice, the second call must delete the
    DailyTodo rows created by the first call so that generate_todos_for_date
    returns fresh rows tied to the new plan, not stale rows from the old plan.
    """
    from datetime import date
    from app.db.models import DailyTodo, TaskTemplate

    # First generate
    sid1 = _create_session(client)
    _fill_answers(client, sid1)
    gen1 = client.post(f"/api/questionnaire/sessions/{sid1}/generate")
    assert gen1.status_code == 202
    plan_id_1 = gen1.json()["plan_id"]

    # Capture today's todo template_ids pointing at plan_1 templates
    today = date.today()
    todos_after_first = (
        db_session.query(DailyTodo)
        .filter(DailyTodo.user_id == "default", DailyTodo.date == today)
        .all()
    )
    plan1_template_ids = {
        tmpl.id
        for tmpl in db_session.query(TaskTemplate)
        .filter(TaskTemplate.plan_id == plan_id_1)
        .all()
    }
    # Ensure first generate created some todos for today
    assert any(t.template_id in plan1_template_ids for t in todos_after_first), (
        "First generate must have created at least one DailyTodo for today"
    )

    # Second generate (new session, same user)
    sid2 = _create_session(client)
    _fill_answers(client, sid2)
    gen2 = client.post(f"/api/questionnaire/sessions/{sid2}/generate")
    assert gen2.status_code == 202

    # After the second generate, NO DailyTodo should point at plan_1 templates
    db_session.expire_all()  # refresh cache
    todos_after_second = (
        db_session.query(DailyTodo)
        .filter(DailyTodo.user_id == "default", DailyTodo.date == today)
        .all()
    )
    stale = [t for t in todos_after_second if t.template_id in plan1_template_ids]
    assert stale == [], (
        f"Found {len(stale)} stale DailyTodo(s) pointing at plan_1 templates after re-generate"
    )


# ── Workbook JSON content ─────────────────────────────────────────────────────

def test_build_workbook_json_content(client: TestClient, db_session):
    """After generate, GeneratedWorkbook.workbook_json has correct user_profile fields."""
    sid = _create_session(client)
    _fill_answers(client, sid)
    gen_resp = client.post(f"/api/questionnaire/sessions/{sid}/generate")
    workbook_id = gen_resp.json()["workbook_id"]

    record = db_session.get(GeneratedWorkbook, workbook_id)
    wj = json.loads(record.workbook_json)

    assert wj["format_version"] == "questionnaire_v1"
    profile = wj["user_profile"]
    assert profile["name"] == "Test User"
    assert profile["sex"] == "M"
    assert profile["height_cm"] == 175.0
    assert profile["weight_kg"] == 80.0
    assert profile["protein_target_g"] == round(80 * 1.6)
    assert wj["supplements_status"]["Creatine"] == "active"
    assert wj["supplements_status"]["Curcumin"] == "review"
