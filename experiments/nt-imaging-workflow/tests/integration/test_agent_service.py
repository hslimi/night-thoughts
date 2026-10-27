from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from nt_imaging.controlplane.api import app, db
from nt_imaging.controlplane.auth import hash_password


def test_local_inspector_uses_stable_checkpoint_thread() -> None:
    client = TestClient(app, base_url="https://testserver")
    db.upsert_user("doctor", hash_password("correct-horse-12"))
    login = client.post(
        "/api/v1/auth/login", json={"username": "doctor", "password": "correct-horse-12"}
    )
    assert login.status_code == 200
    run_id = str(uuid.uuid4())
    state = {
        "run_id": run_id,
        "thread_id": run_id,
        "status": "AWAITING_HUMAN_APPROVAL",
        "inference_mode": "MOCK",
    }
    db.save_snapshot(state, "AWAITING_HUMAN_APPROVAL")
    response = client.get(f"/api/v1/runs/{run_id}/events")
    assert response.status_code == 200
    assert response.json()["run"]["thread_id"] == run_id
    assert response.json()["polling_hint_ms"] == 3000
