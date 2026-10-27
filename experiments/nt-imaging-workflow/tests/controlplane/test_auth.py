from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient

from nt_imaging.controlplane.api import db
from nt_imaging.controlplane.auth import hash_password, new_secrets, verify_password
from nt_imaging.controlplane.db import iso, now

from .conftest import PASSWORD, csrf


def test_login_success_failure_and_password_storage(client: TestClient) -> None:
    encoded = hash_password(PASSWORD)
    assert PASSWORD not in encoded
    assert encoded.startswith("$argon2id$")
    assert verify_password(encoded, PASSWORD)
    db.upsert_user("doctor", encoded)
    failed = client.post("/api/v1/auth/login", json={"username": "doctor", "password": "wrong"})
    assert failed.status_code == 401
    assert failed.json()["error"]["message"] == "Invalid username or password"
    response = client.post("/api/v1/auth/login", json={"username": "doctor", "password": PASSWORD})
    assert response.status_code == 200
    token = client.cookies.get("__Host-nt_session")
    assert token
    with db.connect() as connection:
        session = connection.execute("SELECT * FROM sessions").fetchone()
        user = connection.execute("SELECT * FROM users").fetchone()
    assert token not in dict(session).values()
    assert PASSWORD not in user["password_hash"]


def test_logout_invalidates_session(doctor_client: TestClient) -> None:
    response = doctor_client.post("/api/v1/auth/logout", headers=csrf(doctor_client))
    assert response.status_code == 200
    assert doctor_client.get("/api/v1/runs").status_code == 401


def test_session_expiration(doctor_client: TestClient) -> None:
    with db.connect() as connection:
        connection.execute(
            "UPDATE sessions SET absolute_expires=? WHERE token_hash IN (SELECT token_hash FROM sessions)",
            (iso(now() - timedelta(seconds=1)),),
        )
    assert doctor_client.get("/api/v1/auth/me").status_code == 401


def test_password_reset_invalidates_sessions(doctor_client: TestClient) -> None:
    token = doctor_client.cookies.get("__Host-nt_session")
    assert db.session(token)
    db.upsert_user("doctor", hash_password("new-password-12"))
    assert db.session(token) is None


def test_csrf_required(doctor_client: TestClient) -> None:
    response = doctor_client.post("/api/v1/runs/does-not-matter/cancel")
    assert response.status_code == 403


def test_login_rate_limit(doctor_client: TestClient) -> None:
    for _ in range(5):
        response = doctor_client.post(
            "/api/v1/auth/login", json={"username": "doctor", "password": "wrong"}
        )
        assert response.status_code == 401
    response = doctor_client.post(
        "/api/v1/auth/login", json={"username": "doctor", "password": PASSWORD}
    )
    assert response.status_code == 429
    assert "password" not in response.text.lower()


def test_unauthenticated_access_and_docs_denied(client: TestClient) -> None:
    for path in (
        "/api/v1/runs",
        "/api/v1/dashboard/summary",
        "/api/v1/runs/123e4567-e89b-12d3-a456-426614174000/audit",
        "/docs",
        "/openapi.json",
    ):
        response = client.get(path)
        assert response.status_code in {401, 404}


def test_security_headers(doctor_client: TestClient) -> None:
    response = doctor_client.get("/api/v1/auth/me")
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"


def test_session_secrets_are_random_and_hashed() -> None:
    first, first_csrf = new_secrets()
    second, second_csrf = new_secrets()
    assert first != second and first_csrf != second_csrf
    db.upsert_user("doctor", hash_password(PASSWORD))
    db.create_session("doctor", first, first_csrf)
    with db.connect() as connection:
        row = connection.execute("SELECT * FROM sessions").fetchone()
    assert first not in dict(row).values()
    assert first_csrf not in dict(row).values()
