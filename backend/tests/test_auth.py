"""
Tests for auth endpoints:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
"""
from fastapi.testclient import TestClient


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_creates_user(client: TestClient):
    """Happy path: valid email + password returns 201 with access_token."""
    resp = client.post(
        "/api/auth/register",
        json={"email": "alice@example.com", "password": "securepass1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "user_id" in body
    assert body["user_id"]  # non-empty string


def test_register_duplicate_email(client: TestClient):
    """Registering with an email that already exists returns 409."""
    payload = {"email": "bob@example.com", "password": "securepass1"}
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 409


def test_register_rejects_short_password(client: TestClient):
    """Password shorter than 8 characters must be rejected with 422."""
    resp = client.post(
        "/api/auth/register",
        json={"email": "charlie@example.com", "password": "short"},
    )
    assert resp.status_code == 422


def test_register_rejects_invalid_email(client: TestClient):
    """Non-email string in email field must be rejected with 422."""
    resp = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "securepass1"},
    )
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client: TestClient):
    """Happy path: correct credentials return 200 with access_token."""
    client.post(
        "/api/auth/register",
        json={"email": "dave@example.com", "password": "securepass1"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "dave@example.com", "password": "securepass1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """Wrong password must return 401 with a generic error message."""
    client.post(
        "/api/auth/register",
        json={"email": "eve@example.com", "password": "securepass1"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "eve@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    # Generic message — must not reveal whether email exists (OWASP A07)
    assert "Invalid credentials" in resp.json()["detail"]


def test_login_unknown_email(client: TestClient):
    """Unknown email must return 401 with the same generic message as wrong password."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "securepass1"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


# ── /me ───────────────────────────────────────────────────────────────────────

def test_me_requires_auth(client: TestClient):
    """GET /api/auth/me without a Bearer token must be rejected (4xx)."""
    resp = client.get("/api/auth/me")
    # HTTPBearer returns 403 on missing credentials in some FastAPI versions,
    # 401 in others — either way the request must be denied.
    assert resp.status_code in (401, 403)


def test_me_returns_current_user(client: TestClient):
    """Valid Bearer token returns user profile."""
    reg = client.post(
        "/api/auth/register",
        json={"email": "frank@example.com", "password": "securepass1"},
    )
    token = reg.json()["access_token"]
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "frank@example.com"
    assert "id" in body
    assert "created_at" in body


def test_me_rejects_invalid_token(client: TestClient):
    """An invalid/tampered token must return 401."""
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
    )
    assert resp.status_code == 401
