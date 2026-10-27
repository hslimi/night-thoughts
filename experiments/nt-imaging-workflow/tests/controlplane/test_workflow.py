from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from nt_imaging.config import Settings
from nt_imaging.controlplane.api import db

from .conftest import create_run, csrf, decide, interrupt_run, work_once


def test_upload_list_detail_and_approval(doctor_client: TestClient, clean_fixture: Path) -> None:
    run_id = interrupt_run(doctor_client, clean_fixture)
    assert doctor_client.get("/api/v1/runs").status_code == 200
    assert doctor_client.get(f"/api/v1/runs/{run_id}/timeline").status_code == 200
    assert doctor_client.get(f"/api/v1/runs/{run_id}/image").status_code == 200
    assert doctor_client.get(f"/api/v1/runs/{run_id}/events").json()["polling_hint_ms"] == 3000
    decide(doctor_client, run_id, "APPROVE")
    detail = doctor_client.get(f"/api/v1/runs/{run_id}").json()
    assert detail["status"] == "APPROVED_DRAFT_EXPORTED"
    exports = doctor_client.get(f"/api/v1/runs/{run_id}/exports").json()
    assert exports["eligible"] and len(exports["exports"]) == 3
    download = doctor_client.get(f"/api/v1/runs/{run_id}/exports/report_json")
    assert download.status_code == 200
    assert "AI-ASSISTED DRAFT" in download.text


def test_rejection_never_exports(doctor_client: TestClient, clean_fixture: Path) -> None:
    run_id = interrupt_run(doctor_client, clean_fixture)
    decide(doctor_client, run_id, "REJECT", "Synthetic rejection")
    detail = doctor_client.get(f"/api/v1/runs/{run_id}").json()
    assert detail["status"] == "HUMAN_REJECTED"
    assert not doctor_client.get(f"/api/v1/runs/{run_id}/exports").json()["eligible"]
    assert doctor_client.get(f"/api/v1/runs/{run_id}/exports/report_json").status_code == 404


def test_request_changes_bounded_revision_then_approval(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    run_id = interrupt_run(doctor_client, clean_fixture)
    decide(doctor_client, run_id, "REQUEST_CHANGES", "Clarify the synthetic limitations")
    detail = doctor_client.get(f"/api/v1/runs/{run_id}").json()
    assert detail["status"] == "AWAITING_HUMAN_APPROVAL"
    assert detail["revision"] == 1
    assert detail["attempt"] == 1
    assert detail["grounding_status"] == detail["quality_status"] == "PASS"
    assert detail["export_manifest"] is None
    reviews = doctor_client.get(f"/api/v1/runs/{run_id}/reviews").json()
    assert reviews["decisions"][0]["note"] == "Clarify the synthetic limitations"
    decide(doctor_client, run_id, "APPROVE")
    assert doctor_client.get(f"/api/v1/runs/{run_id}").json()["status"] == "APPROVED_DRAFT_EXPORTED"


def test_queued_and_late_cancellation_prevent_export(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    queued = create_run(doctor_client, clean_fixture)
    response = doctor_client.post(f"/api/v1/runs/{queued}/cancel", headers=csrf(doctor_client))
    assert response.status_code == 200
    work_once()
    assert doctor_client.get(f"/api/v1/runs/{queued}").json()["status"] == "CANCELLED"
    run_id = interrupt_run(doctor_client, clean_fixture)
    db.requeue(
        run_id,
        "DECISION",
        {"decision": {"decision": "APPROVE", "reviewer_display_name": "doctor", "note": ""}},
    )
    doctor_client.post(f"/api/v1/runs/{run_id}/cancel", headers=csrf(doctor_client))
    work_once()
    assert doctor_client.get(f"/api/v1/runs/{run_id}").json()["status"] == "CANCELLED"
    assert doctor_client.get(f"/api/v1/runs/{run_id}/exports/report_json").status_code == 404


def test_approval_with_failed_gate_rejected(doctor_client: TestClient, clean_fixture: Path) -> None:
    run_id = interrupt_run(doctor_client, clean_fixture)
    state = db.snapshot(run_id)
    state["quality_status"] = "FAIL"
    db.save_snapshot(state, "AWAITING_HUMAN_APPROVAL")
    response = doctor_client.post(
        f"/api/v1/runs/{run_id}/decision",
        json={"decision": "APPROVE", "note": ""},
        headers=csrf(doctor_client),
    )
    assert response.status_code == 409
    assert doctor_client.get(f"/api/v1/runs/{run_id}/exports/report_json").status_code == 404


def test_cross_run_artifact_and_export_access_fails(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    run_id = interrupt_run(doctor_client, clean_fixture)
    other = "123e4567-e89b-12d3-a456-426614174000"
    assert doctor_client.get(f"/api/v1/runs/{other}/image").status_code == 404
    assert doctor_client.get(f"/api/v1/runs/{other}/exports/report_json").status_code == 404
    assert (
        doctor_client.get(f"/api/v1/runs/{run_id}/exports/../../settings.json").status_code == 404
    )


def test_one_worker_processes_one_run_at_a_time(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    first = create_run(doctor_client, clean_fixture)
    second = create_run(doctor_client, clean_fixture)
    work_once()
    assert doctor_client.get(f"/api/v1/runs/{first}").json()["status"] == "AWAITING_HUMAN_APPROVAL"
    assert doctor_client.get(f"/api/v1/runs/{second}").json()["status"] == "QUEUED"
    work_once()
    assert doctor_client.get(f"/api/v1/runs/{second}").json()["status"] == "AWAITING_HUMAN_APPROVAL"


def test_restart_recovery_and_technical_retry(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    run_id = create_run(doctor_client, clean_fixture)
    job = db.claim()
    assert job["status"] == "RUNNING"
    from nt_imaging.controlplane.worker import Worker

    Worker(Settings.from_env()).recover()
    detail = doctor_client.get(f"/api/v1/runs/{run_id}").json()
    assert detail["status"] == "NEEDS_HUMAN_REVIEW"
    assert detail["error"]["retryable"]
    state = db.snapshot(run_id)
    state["status"] = "FAILED"
    db.save_snapshot(state, "FAILED")
    response = doctor_client.post(f"/api/v1/runs/{run_id}/retry", headers=csrf(doctor_client))
    assert response.status_code == 202
    assert response.json()["run_id"] != run_id


def test_upload_validation_and_queue_saturation(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    response = doctor_client.post(
        "/api/v1/runs",
        files={"file": ("x.png", b"bad", "image/png")},
        data={"modality": "XR", "confirmed": "false"},
        headers=csrf(doctor_client),
    )
    assert response.status_code == 400
    import uuid

    for _ in range(8):
        run = str(uuid.uuid4())
        db.enqueue(run, "START", {"state": {"run_id": run, "thread_id": run, "status": "RECEIVED"}})
    response = doctor_client.post(
        "/api/v1/runs",
        files={"file": ("synthetic.png", clean_fixture.read_bytes(), "image/png")},
        data={"modality": "XR", "confirmed": "true"},
        headers=csrf(doctor_client),
    )
    assert response.status_code == 429
