from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from nt_imaging.controlplane.api import app, db
from nt_imaging.controlplane.auth import hash_password, new_secrets


def test_console_security_headers_and_csrf() -> None:
    client = TestClient(app, base_url="https://testserver")
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    db.upsert_user("doctor", hash_password("correct-horse-12"))
    login = client.post(
        "/api/v1/auth/login", json={"username": "doctor", "password": "correct-horse-12"}
    )
    assert login.status_code == 200
    response = client.post(
        "/api/v1/runs",
        data={"confirmed": "true", "modality": "XR"},
        files={"file": ("x.png", b"png", "image/png")},
    )
    assert response.status_code == 403


def test_upload_api_has_no_arbitrary_server_path_field() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "frontend" / "src" / "components" / "NewRun.tsx").read_text()
    assert "append('path'" not in source
    assert "append('file'" in source


def test_model_html_is_not_rendered_as_raw_html() -> None:
    root = Path(__file__).resolve().parents[2] / "frontend" / "src"
    for source in root.rglob("*.tsx"):
        assert "dangerouslySetInnerHTML" not in source.read_text()


def test_session_csrf_secrets_remain_opaque() -> None:
    token, csrf_token = new_secrets()
    assert token != csrf_token
    assert len(token) >= 32 and len(csrf_token) >= 32
