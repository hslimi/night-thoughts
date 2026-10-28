from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from nt_imaging.controlplane.api import db
from nt_imaging.controlplane.db import iso, now

from .conftest import interrupt_run


def test_debug_overview_run_trace_logs_and_support(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    run_id = interrupt_run(doctor_client, clean_fixture)
    overview = doctor_client.get("/api/v1/debug/overview")
    assert overview.status_code == 200
    body = overview.json()
    assert body["canonical_instance"] is True
    assert body["last_event_sequence"] > 0
    assert body["code_fingerprint"] and body["data_fingerprint"]
    inspected = doctor_client.get(f"/api/v1/debug/runs/{run_id}")
    assert inspected.status_code == 200
    assert inspected.json()["state"]["thread_id"] == run_id
    assert inspected.json()["model_calls"]
    assert inspected.json()["event_gaps"] == []
    trace = doctor_client.get(f"/api/v1/debug/runs/{run_id}/trace").json()
    assert trace["queue_wait_ms"] is not None
    logs = doctor_client.get(
        f"/api/v1/debug/logs?run={run_id}&event_type=MODEL_CALL_STARTED"
    ).json()
    assert logs["events"]
    support = doctor_client.get(f"/api/v1/debug/support-bundle?run={run_id}")
    assert support.status_code == 200
    assert "attachment" in support.headers["content-disposition"]
    assert "source_path" not in support.text
    assert "api_key" not in support.text
    assert "/Users/" not in support.text


def test_stale_worker_alert(doctor_client: TestClient) -> None:
    worker = db.worker_status()
    assert worker
    with db.connect() as connection:
        connection.execute(
            "UPDATE workers SET last_heartbeat=? WHERE worker_id=?",
            (iso(now() - timedelta(seconds=60)), worker["worker_id"]),
        )
    diagnostics = doctor_client.get("/api/v1/debug/diagnostics").json()
    assert diagnostics["checks"]["frontend_build"]["status"] == "PASS"
    assert any(alert["code"] == "WORKER_HEARTBEAT_STALE" for alert in diagnostics["alerts"])


def test_debug_requires_authentication(clean_fixture: Path) -> None:
    client = TestClient(
        __import__("nt_imaging.controlplane.api", fromlist=["app"]).app,
        base_url="https://testserver",
    )
    assert client.get("/api/v1/debug/overview").status_code == 401
    assert client.get("/api/v1/debug/diagnostics").status_code == 401
