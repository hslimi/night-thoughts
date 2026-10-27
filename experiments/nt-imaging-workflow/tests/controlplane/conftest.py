from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nt_imaging.config import Settings
from nt_imaging.controlplane.api import app, db, limiter
from nt_imaging.controlplane.auth import hash_password
from nt_imaging.controlplane.worker import Worker

PASSWORD = "correct-horse-12"


@pytest.fixture(autouse=True)
def clean_controlplane():
    with db.connect() as connection:
        for table in ("jobs", "snapshots", "sessions", "users", "security_events"):
            connection.execute(f"DELETE FROM {table}")
    limiter.attempts.clear()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, base_url="https://testserver")


@pytest.fixture
def doctor_client(client: TestClient) -> TestClient:
    db.upsert_user("doctor", hash_password(PASSWORD))
    response = client.post("/api/v1/auth/login", json={"username": "doctor", "password": PASSWORD})
    assert response.status_code == 200
    return client


def csrf(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("__Host-nt_csrf", "")}


def create_run(client: TestClient, fixture: Path) -> str:
    response = client.post(
        "/api/v1/runs",
        files={"file": ("synthetic.png", fixture.read_bytes(), "image/png")},
        data={"modality": "XR", "confirmed": "true"},
        headers=csrf(client),
    )
    assert response.status_code == 202, response.text
    return response.json()["run_id"]


def work_once() -> None:
    Worker(Settings.from_env()).run(once=True)


def interrupt_run(client: TestClient, fixture: Path) -> str:
    run_id = create_run(client, fixture)
    work_once()
    response = client.get(f"/api/v1/runs/{run_id}")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "AWAITING_HUMAN_APPROVAL", response.text
    return run_id


def decide(client: TestClient, run_id: str, decision: str, note: str = ""):
    response = client.post(
        f"/api/v1/runs/{run_id}/decision",
        json={"decision": decision, "note": note},
        headers=csrf(client),
    )
    assert response.status_code == 202, response.text
    work_once()
    return response
