from fastapi.testclient import TestClient

from app.db.models import QuestionnaireAnswer, QuestionnaireQuestion


def _register(client: TestClient, email: str) -> str:
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "StrongerPass123"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _create_answered_session(client: TestClient) -> str:
    session_resp = client.post("/api/questionnaire/sessions")
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]
    answer_resp = client.put(
        f"/api/questionnaire/sessions/{session_id}/answers",
        json={
            "question_id": "q1_full_name",
            "section_number": 1,
            "answer_json": '"Pankaj Test"',
        },
    )
    assert answer_resp.status_code == 200
    return session_id


def test_answer_upsert_links_question_snapshot(client: TestClient, db_session):
    session_id = _create_answered_session(client)

    answer = (
        db_session.query(QuestionnaireAnswer)
        .filter(QuestionnaireAnswer.session_id == session_id)
        .one()
    )
    assert answer.question_snapshot_id is not None

    snapshot = db_session.get(QuestionnaireQuestion, answer.question_snapshot_id)
    assert snapshot is not None
    assert snapshot.question_id == "q1_full_name"
    assert snapshot.question_text == "What is your full name?"


def test_admin_session_list_rejects_non_admin(client: TestClient, monkeypatch):
    _create_answered_session(client)
    token = _register(client, "user@example.com")
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")

    resp = client.get(
        "/api/admin/questionnaires/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


def test_admin_session_list_accepts_admin(client: TestClient, monkeypatch):
    session_id = _create_answered_session(client)
    token = _register(client, "admin@example.com")
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")

    resp = client.get(
        "/api/admin/questionnaires/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert session_id in ids


def test_admin_detail_includes_unanswered_questions(client: TestClient, monkeypatch):
    session_id = _create_answered_session(client)
    token = _register(client, "admin@example.com")
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")

    resp = client.get(
        f"/api/admin/questionnaires/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["questions"]) == 40
    assert body["questions"][0]["question_text"] == "What is your full name?"
    assert body["questions"][0]["formatted_answer"] == "Pankaj Test"
    assert body["questions"][1]["answer_json"] is None


def test_admin_export_plain_text_format(client: TestClient, monkeypatch):
    session_id = _create_answered_session(client)
    token = _register(client, "admin@example.com")
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")

    resp = client.get(
        f"/api/admin/questionnaires/sessions/{session_id}/export.txt",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    text = resp.text
    assert f"Questionnaire Session: {session_id}" in text
    assert "Q1. What is your full name?" in text
    assert "Ans1: Pankaj Test" in text
    assert "------" in text
