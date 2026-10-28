from __future__ import annotations

import importlib.util
import json
import os
import platform
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from ..audit import AuditDB
from ..config import Settings, get_omlx_api_key
from .db import ControlDB, fingerprint, now
from .runtime import runtime_identity
from .sse import active_sse_connections
from .worker import public_state


def _age_seconds(timestamp: str | None) -> float | None:
    if not timestamp:
        return None
    return max(0.0, (now() - datetime.fromisoformat(timestamp)).total_seconds())


def _active_job(db: ControlDB) -> dict[str, Any] | None:
    with db.connect() as connection:
        row = connection.execute(
            "SELECT job_id,run_id,kind,status,created_at,updated_at,heartbeat_at FROM jobs WHERE status IN ('RUNNING','EXPORTING') ORDER BY updated_at LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def _overview(settings: Settings, db: ControlDB) -> dict[str, Any]:
    worker = db.worker_status()
    with db.connect() as connection:
        queued = connection.execute("SELECT COUNT(*) FROM jobs WHERE status='QUEUED'").fetchone()[0]
    return {
        **runtime_identity(settings),
        "workflow_version": settings.workflow_version,
        "inference_mode": settings.inference_mode,
        "vision_model_id": settings.vision_model,
        "text_model_id": settings.text_model,
        "canonical_instance": True,
        "database_fingerprint": fingerprint(settings.data_root / "controlplane.sqlite3"),
        "worker": dict(worker) if worker else None,
        "worker_heartbeat_age_seconds": _age_seconds(worker["last_heartbeat"] if worker else None),
        "queue_depth": queued,
        "active_job": _active_job(db),
        "sse_connection_count": active_sse_connections(),
        "last_event_sequence": db.latest_sequence(),
    }


def _alerts(settings: Settings, db: ControlDB) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    identity = runtime_identity(settings)
    worker = db.worker_status()
    age = _age_seconds(worker["last_heartbeat"] if worker else None)
    if age is None or age > 15:
        alerts.append(
            {
                "code": "WORKER_HEARTBEAT_STALE",
                "message": "Worker heartbeat is missing or older than 15 seconds",
                "age_seconds": age,
            }
        )
    if worker and (
        worker["code_fingerprint"] != identity["code_fingerprint"]
        or worker["data_fingerprint"] != identity["data_fingerprint"]
    ):
        alerts.append(
            {
                "code": "RUNTIME_IDENTITY_MISMATCH",
                "message": "API and worker code or data-root identity differs",
            }
        )
    job = _active_job(db)
    if job and (_age_seconds(job["updated_at"]) or 0) > 60:
        alerts.append(
            {
                "code": "JOB_PROGRESS_STALE",
                "message": "Running job has not progressed for more than 60 seconds",
                "job_id": job["job_id"],
                "run_id": job["run_id"],
            }
        )
    with db.connect() as connection:
        queued = connection.execute(
            "SELECT job_id,run_id,created_at FROM jobs WHERE status='QUEUED' ORDER BY created_at LIMIT 1"
        ).fetchone()
    if queued and (age is None or age > 15):
        alerts.append(
            {
                "code": "QUEUE_WITHOUT_WORKER",
                "message": "Queued work has no fresh worker heartbeat",
                "job_id": queued["job_id"],
                "run_id": queued["run_id"],
            }
        )
    for event in db.events(limit=5000):
        if event["event_type"] != "MODEL_CALL_STARTED":
            continue
        later = [
            candidate
            for candidate in db.run_events(event["run_id"], after=event["sequence"])
            if candidate.get("model_call_sequence") == event.get("model_call_sequence")
            and candidate["event_type"] in {"MODEL_CALL_COMPLETED", "MODEL_CALL_FAILED"}
        ]
        if (
            not later
            and (_age_seconds(event["timestamp_utc"]) or 0) > settings.model_timeout_seconds
        ):
            alerts.append(
                {
                    "code": "MODEL_CALL_TIMEOUT",
                    "message": "Model call exceeded its configured timeout",
                    "run_id": event["run_id"],
                    "model_call_sequence": event["model_call_sequence"],
                }
            )
    return alerts


def _diagnostics(settings: Settings, db: ControlDB) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    try:
        with db.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("CREATE TEMP TABLE nt_diagnostic_write(value INTEGER)")
            connection.execute("DROP TABLE nt_diagnostic_write")
            connection.execute("ROLLBACK")
        checks["database"] = {"status": "PASS", "read_write": True}
    except sqlite3.Error as exc:
        checks["database"] = {"status": "FAIL", "error_category": type(exc).__name__}
    checkpoint = settings.data_root / "deployed-checkpoints.sqlite3"
    checks["checkpoint"] = {
        "status": "PASS" if checkpoint.exists() else "WARN",
        "available": checkpoint.exists(),
    }
    checks["artifacts"] = {
        "status": "PASS" if os.access(settings.data_root, os.R_OK | os.W_OK) else "FAIL"
    }
    checks["ocr"] = {
        "status": "PASS"
        if platform.system() == "Darwin" and importlib.util.find_spec("Vision")
        else "FAIL",
        "engine": "Apple Vision",
    }
    frontend = Path(__file__).resolve().parents[3] / "frontend" / "dist" / "index.html"
    checks["frontend_build"] = {
        "status": "PASS" if frontend.exists() else "FAIL",
        "present": frontend.exists(),
    }
    checks["sse"] = {
        "status": "PASS",
        "connections": active_sse_connections(),
        "last_sequence": db.latest_sequence(),
    }
    checks["worker"] = {
        "status": "PASS" if not _alerts(settings, db) else "FAIL",
        "alerts": _alerts(settings, db),
    }
    try:
        headers = {"Authorization": f"Bearer {get_omlx_api_key()}"}
        with httpx.Client(timeout=5) as client:
            health = client.get("http://127.0.0.1:8000/health")
            models = client.get(f"{settings.omlx_base_url}/models", headers=headers)
        checks["omlx"] = {
            "status": "PASS" if health.status_code == 200 and models.status_code == 200 else "FAIL",
            "health_http": health.status_code,
            "models_http": models.status_code,
            "model_ids": [item["id"] for item in models.json().get("data", [])]
            if models.status_code == 200
            else [],
        }
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        checks["omlx"] = {"status": "FAIL", "error_category": type(exc).__name__}
    return checks


def register_debug_routes(
    app: FastAPI, settings: Settings, db: ControlDB, audit: AuditDB, actor: Any, state_for: Any
) -> None:
    @app.get("/api/v1/debug/overview")
    async def overview(_: str = Depends(actor)) -> dict[str, Any]:
        return _overview(settings, db)

    @app.get("/api/v1/debug/diagnostics")
    async def diagnostics(_: str = Depends(actor)) -> dict[str, Any]:
        return {"checks": _diagnostics(settings, db), "alerts": _alerts(settings, db)}

    @app.get("/api/v1/debug/runs/{run}")
    async def inspect(run: str, _: str = Depends(actor)) -> dict[str, Any]:
        state = state_for(run)
        job = db.job_for_run(state["run_id"])
        with audit.connect() as connection:
            calls = connection.execute(
                "SELECT stage,model_id,latency_ms,status,output_sha256,created_at FROM model_calls WHERE run_id=? ORDER BY created_at",
                (state["run_id"],),
            ).fetchall()
        return {
            "state": public_state(state),
            "events": db.run_events(state["run_id"]),
            "model_calls": [dict(row) for row in calls],
            "job": dict(job) if job else None,
            "retry_eligible": state.get("status") == "FAILED"
            and bool((state.get("error") or {}).get("retryable")),
            "cancel_eligible": state.get("status")
            not in {"APPROVED_DRAFT_EXPORTED", "CANCELLED", "HUMAN_REJECTED"},
            "event_gaps": db.event_gaps(state["run_id"]),
        }

    @app.get("/api/v1/debug/runs/{run}/trace")
    async def trace(run: str, _: str = Depends(actor)) -> dict[str, Any]:
        state = state_for(run)
        events = db.run_events(state["run_id"])
        starts = [event for event in events if event["event_type"] == "RUN_CREATED"]
        started = [event for event in events if event["event_type"] == "RUN_STARTED"]
        humans = [event for event in events if event["event_type"] == "HUMAN_APPROVAL_REQUIRED"]
        decisions = [event for event in events if event["event_type"] == "HUMAN_DECISION_RECORDED"]
        queue_ms = None
        human_ms = None
        if starts and started:
            queue_ms = int(
                (
                    datetime.fromisoformat(started[0]["timestamp_utc"])
                    - datetime.fromisoformat(starts[0]["timestamp_utc"])
                ).total_seconds()
                * 1000
            )
        if humans and decisions:
            human_ms = int(
                (
                    datetime.fromisoformat(decisions[-1]["timestamp_utc"])
                    - datetime.fromisoformat(humans[-1]["timestamp_utc"])
                ).total_seconds()
                * 1000
            )
        return {
            "run_id": state["run_id"],
            "events": events,
            "queue_wait_ms": queue_ms,
            "human_wait_ms": human_ms,
            "total_node_duration_ms": sum(
                event.get("duration_ms") or 0
                for event in events
                if event["event_type"] in {"NODE_COMPLETED", "NODE_FAILED"}
            ),
        }

    @app.get("/api/v1/debug/logs")
    async def logs(
        run: str | None = None,
        q: str | None = None,
        event_type: str | None = None,
        limit: int = 200,
        _: str = Depends(actor),
    ) -> dict[str, Any]:
        bounded = max(1, min(limit, 500))
        events = db.events(run_id=run, limit=5000)
        filtered = [
            event
            for event in events
            if (not event_type or event["event_type"] == event_type)
            and (not q or q.lower() in json.dumps(event, default=str).lower())
        ]
        return {
            "events": filtered[-bounded:],
            "count": len(filtered),
            "redaction": "No credentials, raw DICOM metadata, full prompts, or patient identifiers",
        }

    @app.get("/api/v1/debug/support-bundle")
    async def support(run: str | None = None, _: str = Depends(actor)) -> JSONResponse:
        selected = state_for(run) if run else None
        bundle = {
            "overview": _overview(settings, db),
            "diagnostics": _diagnostics(settings, db),
            "alerts": _alerts(settings, db),
            "recent_errors": [
                event
                for event in db.events(limit=5000)
                if event["event_type"] in {"RUN_FAILED", "NODE_FAILED", "MODEL_CALL_FAILED"}
            ][-100:],
            "run": public_state(selected) if selected else None,
            "run_events": db.run_events(selected["run_id"]) if selected else [],
            "redaction": "Sanitized operational metadata only; no secrets or medical-image artifacts",
        }
        return JSONResponse(
            bundle, headers={"Content-Disposition": "attachment; filename=nt-imaging-support.json"}
        )
