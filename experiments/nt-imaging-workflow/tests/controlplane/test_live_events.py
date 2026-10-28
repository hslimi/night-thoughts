from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nt_imaging.config import Settings
from nt_imaging.controlplane.api import app, db
from nt_imaging.controlplane.worker import Worker

from .conftest import create_run, interrupt_run


def test_durable_event_order_replay_and_safe_payload(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    run_id = interrupt_run(doctor_client, clean_fixture)
    events = db.run_events(run_id)
    assert len(events) > 20
    sequences = [event["sequence"] for event in events]
    run_sequences = [event["run_sequence"] for event in events]
    assert sequences == sorted(sequences) and len(set(sequences)) == len(sequences)
    assert run_sequences == list(range(1, len(events) + 1))
    assert not db.event_gaps(run_id)
    types = {event["event_type"] for event in events}
    assert {
        "RUN_CREATED",
        "RUN_STARTED",
        "NODE_STARTED",
        "NODE_COMPLETED",
        "PREPARATION_STARTED",
        "PREPARATION_OPERATION_COMPLETED",
        "PREPARATION_COMPLETED",
        "DERIVED_SAFETY_RESULT",
        "MODEL_CALL_STARTED",
        "MODEL_CALL_COMPLETED",
        "HUMAN_APPROVAL_REQUIRED",
    } <= types
    replay = db.run_events(run_id, after=sequences[2])
    assert [event["sequence"] for event in replay] == sequences[3:]
    for event in events:
        assert "source_path" not in event["payload"].get("snapshot", {})
        assert "prompt" not in event["payload"]


def test_transactional_event_failure_rolls_back_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    state = {
        "run_id": "123e4567-e89b-12d3-a456-426614174000",
        "thread_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "QUEUED",
        "workflow_version": "test",
        "inference_mode": "MOCK",
    }
    db.save_snapshot(state)
    original = db._append_event

    def fail(*args, **kwargs):
        raise RuntimeError("injected event failure")

    monkeypatch.setattr(db, "_append_event", fail)
    with pytest.raises(RuntimeError):
        db.record_event("NODE_STARTED", state={**state, "status": "RUNNING"})
    monkeypatch.setattr(db, "_append_event", original)
    assert db.snapshot(state["run_id"])["status"] == "QUEUED"
    assert db.run_events(state["run_id"]) == []


def test_worker_lifecycle_heartbeat() -> None:
    worker = Worker(Settings.from_env())
    worker.run(once=True)
    status = db.worker_status()
    assert status and status["status"] == "STOPPED"
    types = {event["event_type"] for event in db.events()}
    assert {"WORKER_STARTED", "WORKER_STOPPED"} <= types


def read_until(response, predicate, maximum: int = 100) -> list[str]:
    lines = []
    for line in response.iter_lines():
        if line:
            lines.append(line)
            if predicate(lines):
                return lines
            if len(lines) >= maximum:
                break
    raise AssertionError(f"SSE condition not reached: {lines[-10:]}")


def test_sse_authentication_snapshot_replay_and_multiple_tabs(
    doctor_client: TestClient, clean_fixture: Path
) -> None:
    run_id = create_run(doctor_client, clean_fixture)
    unauthenticated = TestClient(app, base_url="https://testserver")
    assert unauthenticated.get("/api/events").status_code == 401
    assert unauthenticated.get(f"/api/runs/{run_id}/events").status_code == 401
    with doctor_client.stream("GET", f"/api/runs/{run_id}/events") as response:
        assert response.status_code == 200
        assert response.headers["x-accel-buffering"] == "no"
        lines = read_until(response, lambda current: any("RUN_CREATED" in line for line in current))
        assert any("event: snapshot" in line for line in lines)
        assert any("event: RUN_CREATED" in line for line in lines)
    first_sequence = db.run_events(run_id)[0]["sequence"]
    with doctor_client.stream(
        "GET", f"/api/runs/{run_id}/events", headers={"Last-Event-ID": str(first_sequence)}
    ) as response:
        lines = read_until(
            response, lambda current: any("event: RUN_QUEUED" in line for line in current)
        )
        assert f"id: {first_sequence}" not in lines
    before = len(db.run_events(run_id))
    with doctor_client.stream("GET", f"/api/runs/{run_id}/events") as first:
        read_until(first, lambda current: any("event: snapshot" in line for line in current))
        with doctor_client.stream("GET", f"/api/runs/{run_id}/events") as second:
            read_until(second, lambda current: any("event: snapshot" in line for line in current))
    assert len(db.run_events(run_id)) == before


def test_sse_gap_emits_resync(doctor_client: TestClient, clean_fixture: Path) -> None:
    run_id = create_run(doctor_client, clean_fixture)
    state = db.snapshot(run_id)
    third = db.record_event("NODE_STARTED", state=state, node_name="ingest_validate")
    with db.connect() as connection:
        connection.execute("DELETE FROM app_events WHERE run_id=? AND run_sequence=2", (run_id,))
    with doctor_client.stream(
        "GET", f"/api/runs/{run_id}/events", headers={"Last-Event-ID": str(third - 2)}
    ) as response:
        lines = read_until(
            response, lambda current: any("event: NODE_STARTED" in line for line in current)
        )
        assert any("event: resync" in line for line in lines)
        assert db.event_gaps(run_id) == [2]
        payload = json.loads(next(line[6:] for line in lines if line.startswith("data: {")))
        assert "run" in payload or "last_sequence" in payload
