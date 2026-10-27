from __future__ import annotations

import runpy
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nt_imaging.config import Settings
from nt_imaging.controlplane.api import app, db, limiter
from nt_imaging.controlplane.auth import hash_password
from nt_imaging.controlplane.worker import Worker
from nt_imaging.state import initial_state


@pytest.fixture
def doctor_client() -> TestClient:
    with db.connect() as connection:
        for table in ("jobs", "snapshots", "sessions", "users", "security_events"):
            connection.execute(f"DELETE FROM {table}")
    limiter.attempts.clear()
    client = TestClient(app, base_url="https://testserver")
    db.upsert_user("doctor", hash_password("correct-horse-12"))
    response = client.post(
        "/api/v1/auth/login", json={"username": "doctor", "password": "correct-horse-12"}
    )
    assert response.status_code == 200
    return client


migrate = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts" / "migrate_v3.py"))[
    "main"
]


def login(client: TestClient) -> None:
    db.upsert_user("doctor", hash_password("correct-horse-12"))
    response = client.post(
        "/api/v1/auth/login", json={"username": "doctor", "password": "correct-horse-12"}
    )
    assert response.status_code == 200


def test_preparation_endpoints_and_local_inspector(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    state = initial_state(str(clean_fixture), inference_mode="MOCK", declared_modality="XR")
    run_id = state["run_id"]
    db.enqueue(run_id, "START", {"state": state})
    snapshot = state.copy()
    snapshot["status"] = "QUEUED"
    db.save_snapshot(snapshot, "QUEUED")
    Worker(Settings.from_env()).run(once=True)
    for path in ("source-preview", "comparison", "preparation-receipt", "graph-inspector"):
        response = doctor_client.get(f"/api/v1/runs/{run_id}/{path}")
        assert response.status_code == 200, (path, response.text)
        assert "/Users/" not in response.text
    receipt = doctor_client.get(f"/api/v1/runs/{run_id}/preparation-receipt").json()
    assert receipt["preparation_policy_version"] == "cxr-preparation-v2"
    inspector = doctor_client.get(f"/api/v1/runs/{run_id}/graph-inspector").json()
    assert "imaging_readiness" in inspector["completed_nodes"]
    assert inspector["observability"].startswith("Local structured events")


def test_legacy_snapshot_migration_and_counts(doctor_client: TestClient) -> None:
    run_id = str(uuid.uuid4())
    legacy = initial_state("unused", inference_mode="MOCK")
    legacy.update(
        {
            "run_id": run_id,
            "thread_id": run_id,
            "status": "APPROVED_DRAFT_EXPORTED",
            "preprocessed_artifact_id": uuid.uuid4().hex,
            "preprocessed_sha256": "a" * 64,
            "preprocess_metadata": {"width": 384},
        }
    )
    legacy.pop("preparation_policy_version", None)
    db.save_snapshot(legacy, "APPROVED_DRAFT_EXPORTED")
    migrate()
    state = db.snapshot(run_id)
    assert state["preparation_warnings"] == ["LEGACY_NO_PREPARATION_RECEIPT"]
    assert state["prepared_sha256"] == "a" * 64
    summary = doctor_client.get("/api/v1/dashboard/summary").json()
    assert summary["completed_exports"] >= 1
    assert summary["actionable"] >= 0
    response = doctor_client.get(f"/api/v1/runs/{run_id}/preparation-receipt")
    assert response.json()["status"] == "LEGACY_NO_PREPARATION_RECEIPT"


def test_filters_pagination_and_fault_labels(doctor_client: TestClient) -> None:
    run_id = str(uuid.uuid4())
    state = initial_state("unused", inference_mode="MOCK", fault_profile="grounding_fail_once")
    state.update(
        {
            "run_id": run_id,
            "thread_id": run_id,
            "status": "NEEDS_HUMAN_REVIEW",
            "modality": "XR",
            "vision_model_id": "MedMO-8B-Next",
        }
    )
    db.save_snapshot(state, "NEEDS_HUMAN_REVIEW")
    response = doctor_client.get("/api/v1/runs?inference_mode=MOCK&page=1&page_size=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    summary = doctor_client.get("/api/v1/dashboard/summary").json()
    assert summary["mock_label"] is not None
    assert summary["actionable"] >= 1


def test_no_required_langsmith_integration() -> None:
    root = Path(__file__).resolve().parents[2]
    pyproject = (root / "pyproject.toml").read_text()
    assert "langgraph-cli" not in pyproject
    assert "langgraph-sdk" not in pyproject
    for name in ["production.sh", "dev.sh", "mock_guide.sh"]:
        assert "LANGSMITH" not in (root / "scripts" / name).read_text()
    assert not (root / "langgraph.json").exists()
