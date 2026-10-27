from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Literal, cast

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from ..artifacts import ArtifactStore, validate_id
from ..audit import AuditDB, utc_now
from ..config import Settings
from ..constants import DISCLAIMER, MOCK_LABEL
from ..schemas import HumanDecision
from ..state import initial_state
from .auth import LoginLimiter, csrf_valid, new_secrets, verify_password
from .db import ControlDB, InvalidTransition, QueueFull
from .worker import public_state

settings = Settings.from_env()
settings.ensure_directories()
db = ControlDB(settings.data_root / "controlplane.sqlite3")
audit = AuditDB(settings.data_root / "nt_imaging.sqlite3")
limiter = LoginLimiter()
app = FastAPI(title="Nightthoughts Doctor Console", docs_url=None, redoc_url=None, openapi_url=None)
RUN_ID = re.compile(r"^[0-9a-f-]{36}$")
SESSION_COOKIE = "__Host-nt_session"
CSRF_COOKIE = "__Host-nt_csrf"


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["APPROVE", "REJECT", "REQUEST_CHANGES"]
    note: str = Field(default="", max_length=1000)


class RunResponse(BaseModel):
    run_id: str
    status: str


class AuthResponse(BaseModel):
    username: str
    csrf_token: str


class MessageResponse(BaseModel):
    status: str


@app.middleware("http")
async def security_middleware(request: Request, call_next: Any) -> Any:
    length = request.headers.get("content-length")
    if length and int(length) > settings.max_upload_bytes + 1_000_000:
        return JSONResponse(
            {
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "Request exceeds the configured limit",
                }
            },
            status_code=413,
        )
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; connect-src 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    code = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_REQUIRED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "INVALID_STATE",
        413: "REQUEST_TOO_LARGE",
        429: "RATE_LIMITED",
        500: "SERVER_ERROR",
    }.get(exc.status_code, "REQUEST_FAILED")
    return JSONResponse(
        {"error": {"code": code, "message": str(exc.detail), "details": {}}},
        status_code=exc.status_code,
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_error(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        {
            "error": {
                "code": "SERVER_ERROR",
                "message": "The request could not be completed",
                "details": {},
            }
        },
        status_code=500,
    )


def run_id(value: str) -> str:
    if not RUN_ID.fullmatch(value):
        raise HTTPException(404, "Run not found")
    return str(uuid.UUID(value))


def session_token(request: Request) -> str:
    return request.cookies.get(SESSION_COOKIE, "")


def actor(request: Request) -> str:
    session = db.session(session_token(request))
    if not session:
        raise HTTPException(401, "Authentication required")
    request.state.username = session["username"]
    return str(session["username"])


def csrf(request: Request) -> None:
    token = request.headers.get("x-csrf-token", "")
    if not token or not csrf_valid(db, session_token(request), token):
        raise HTTPException(403, "CSRF validation failed")


def state_for(run: str) -> dict[str, Any]:
    state = db.snapshot(run_id(run))
    if not state:
        raise HTTPException(404, "Run not found")
    return state


def client_key(request: Request, username: str) -> str:
    host = request.client.host if request.client else "unknown"
    if host == "127.0.0.1":
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            host = forwarded.split(",", 1)[0].strip()
    return f"{host}:{username.lower()}"


def set_session_cookies(response: JSONResponse, token: str, csrf_token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        secure=True,
        httponly=True,
        samesite="strict",
        path="/",
        max_age=28800,
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        secure=True,
        httponly=False,
        samesite="strict",
        path="/",
        max_age=28800,
    )


@app.post("/api/v1/auth/login", response_model=AuthResponse)
async def login(request: Request, body: LoginRequest) -> JSONResponse:
    key = client_key(request, body.username)
    remaining = limiter.blocked(key)
    if remaining:
        db.security_event("LOGIN_RATE_LIMITED", body.username)
        raise HTTPException(
            429, "Too many attempts; try again later", headers={"Retry-After": str(remaining)}
        )
    user = db.user(body.username)
    if not user or not verify_password(user["password_hash"], body.password):
        limiter.failed(key)
        db.security_event("LOGIN_FAILED", body.username)
        raise HTTPException(401, "Invalid username or password")
    limiter.succeeded(key)
    token, csrf_token = new_secrets()
    db.create_session(body.username, token, csrf_token)
    db.security_event("LOGIN_SUCCESS", body.username)
    response = JSONResponse({"username": body.username, "csrf_token": csrf_token})
    set_session_cookies(response, token, csrf_token)
    return response


@app.post("/api/v1/auth/logout", response_model=MessageResponse)
async def logout(request: Request, username: str = Depends(actor)) -> JSONResponse:
    csrf(request)
    db.delete_session(session_token(request))
    db.security_event("LOGOUT", username)
    response = JSONResponse({"status": "LOGGED_OUT"})
    response.delete_cookie(SESSION_COOKIE, path="/", secure=True, httponly=True, samesite="strict")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=True, httponly=False, samesite="strict")
    return response


@app.get("/api/v1/auth/me", response_model=AuthResponse)
async def me(request: Request, username: str = Depends(actor)) -> dict[str, str]:
    return {"username": username, "csrf_token": request.cookies.get(CSRF_COOKIE, "")}


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def ready() -> JSONResponse:
    try:
        with db.connect() as connection:
            connection.execute("SELECT 1").fetchone()
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get("http://127.0.0.1:8000/health")
        omlx = response.status_code == 200
        return JSONResponse(
            {
                "status": "ready" if omlx else "degraded",
                "database": "ok",
                "inference": "ok" if omlx else "unavailable",
            },
            status_code=200 if omlx else 503,
        )
    except Exception:  # noqa: BLE001 - health endpoint intentionally returns an opaque unavailable status
        return JSONResponse({"status": "unavailable"}, status_code=503)


@app.get("/api/v1/dashboard/summary")
async def dashboard_summary(_: str = Depends(actor)) -> dict[str, Any]:
    runs = db.snapshots()
    counts: dict[str, int] = {}
    for run in runs:
        counts[run["status"]] = counts.get(run["status"], 0) + 1
    actionable_statuses = {
        "AWAITING_HUMAN_APPROVAL",
        "NEEDS_HUMAN_REVIEW",
        "FAILED",
        "IMAGE_PREPARATION_FAILED",
        "MODEL_OUTPUT_INVALID",
    }
    actionable = sum(1 for run in runs if run["status"] in actionable_statuses)
    with db.connect() as connection:
        queued = connection.execute("SELECT COUNT(*) FROM jobs WHERE status='QUEUED'").fetchone()[0]
        active = connection.execute(
            "SELECT COUNT(*) FROM jobs WHERE status IN ('RUNNING','EXPORTING')"
        ).fetchone()[0]
        heartbeat = connection.execute("SELECT MAX(heartbeat_at) FROM jobs").fetchone()[0]
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            omlx_response = await client.get("http://127.0.0.1:8000/health")
        omlx_reachable = omlx_response.status_code == 200
    except httpx.HTTPError:
        omlx_reachable = False
    return {
        "counts": counts,
        "total": len(runs),
        "actionable": actionable,
        "completed_exports": counts.get("APPROVED_DRAFT_EXPORTED", 0),
        "cancelled": counts.get("CANCELLED", 0),
        "failures": sum(
            counts.get(status, 0)
            for status in ("FAILED", "MODEL_OUTPUT_INVALID", "IMAGE_PREPARATION_FAILED")
        ),
        "queue_depth": queued,
        "active_workers": active,
        "worker_heartbeat": heartbeat,
        "omlx_reachable": omlx_reachable,
        "omlx_checked_at": utc_now(),
        "vision_model_id": settings.vision_model,
        "text_model_id": settings.text_model,
        "inference_mode": settings.inference_mode,
        "mock_label": MOCK_LABEL if settings.inference_mode == "MOCK" else None,
    }


@app.get("/api/v1/runs")
async def list_runs(
    status: str | None = None,
    q: str | None = None,
    modality: str | None = None,
    inference_mode: str | None = None,
    model_id: str | None = None,
    source_sha256: str | None = None,
    date: str | None = None,
    page: int = 1,
    page_size: int = 25,
    sort: str = "updated_desc",
    _: str = Depends(actor),
) -> list[dict[str, Any]]:
    if page < 1 or page_size < 1 or page_size > 100 or sort not in {"updated_desc", "updated_asc"}:
        raise HTTPException(400, "Invalid pagination or sort")
    runs = db.snapshots()
    filtered = [
        run
        for run in runs
        if (not status or run["status"] == status)
        and (not q or q in run["run_id"])
        and (not modality or run.get("modality") == modality)
        and (not inference_mode or run.get("inference_mode") == inference_mode)
        and (not model_id or model_id in {run.get("vision_model_id"), run.get("text_model_id")})
        and (not source_sha256 or run.get("source_sha256") == source_sha256)
        and (not date or str(run.get("snapshot_updated_at", "")).startswith(date))
    ]
    filtered.sort(
        key=lambda run: str(run.get("snapshot_updated_at", "")), reverse=sort == "updated_desc"
    )
    start = (page - 1) * page_size
    return [
        {
            key: run.get(key)
            for key in (
                "run_id",
                "thread_id",
                "status",
                "inference_mode",
                "fault_profile",
                "demonstration_scenario",
                "modality",
                "source_format",
                "attempt",
                "revision",
                "model_calls",
                "vision_model_id",
                "text_model_id",
                "source_sha256",
                "prepared_sha256",
                "readiness_status",
                "preparation_policy_version",
                "snapshot_updated_at",
                "error",
            )
        }
        for run in filtered[start : start + page_size]
    ]


@app.post("/api/v1/runs", response_model=RunResponse, status_code=202)
async def create_run(
    request: Request,
    file: UploadFile = File(...),
    modality: str | None = Form(None),
    confirmed: bool = Form(False),
    fault_profile: str | None = Form(None),
    demonstration_scenario: str | None = Form(None),
    username: str = Depends(actor),
) -> dict[str, str]:
    csrf(request)
    if fault_profile and fault_profile != "none":
        from ..inference.mock import PROFILES

        if (
            settings.inference_mode != "MOCK"
            or not request.client
            or request.client.host != "127.0.0.1"
            or fault_profile not in PROFILES
        ):
            raise HTTPException(
                403, "Fault injection is restricted to loopback MOCK demonstrations"
            )
    if demonstration_scenario and not re.fullmatch(r"[a-z0-9_]{1,64}", demonstration_scenario):
        raise HTTPException(400, "Invalid demonstration scenario identifier")
    if modality not in {None, "XR"} or not confirmed:
        raise HTTPException(
            400, "Confirm permitted data use and provide a valid modality declaration"
        )
    content = await file.read(settings.max_upload_bytes + 1)
    await file.close()
    if not content or len(content) > settings.max_upload_bytes:
        raise HTTPException(413, "Upload is empty or exceeds the configured limit")
    upload_root = settings.data_root / "control-uploads"
    upload_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    upload = upload_root / f"{uuid.uuid4().hex}.upload"
    upload.write_bytes(content)
    upload.chmod(0o600)
    state = initial_state(
        str(upload),
        inference_mode=settings.inference_mode,
        workflow_version=settings.workflow_version,
        max_attempts=settings.max_attempts,
        max_total_model_calls=settings.max_total_model_calls,
        declared_modality=modality,
        synthetic_or_authorized=True,
        vision_model_id=settings.vision_model,
        text_model_id=settings.text_model,
    )
    state["fault_profile"] = fault_profile
    if demonstration_scenario:
        state["demonstration_scenario"] = demonstration_scenario
    run = state["run_id"]
    try:
        db.enqueue(run, "START", {"state": state})
    except QueueFull as exc:
        upload.unlink(missing_ok=True)
        raise HTTPException(429, str(exc)) from exc
    queued = public_state(dict(state))
    queued["status"] = "QUEUED"
    db.save_snapshot(queued, "QUEUED")
    db.security_event("UPLOAD_ACCEPTED", username, run, {"size_bytes": len(content)})
    db.security_event("RUN_CREATED", username, run)
    return {"run_id": run, "status": "QUEUED"}


@app.get("/api/v1/runs/{run}")
async def run_detail(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    job = db.job_for_run(state["run_id"])
    return {**state, "job_status": job["status"] if job else None, "disclaimer": DISCLAIMER}


@app.get("/api/v1/runs/{run}/timeline")
async def run_timeline(run: str, _: str = Depends(actor)) -> list[dict[str, Any]]:
    state = state_for(run)
    return audit.timeline(state["run_id"])


@app.get("/api/v1/runs/{run}/reviews")
async def run_reviews(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    with audit.connect() as connection:
        rows = connection.execute(
            "SELECT decision, reviewer, note, revision, resulting_state, decided_at FROM human_decision_history WHERE run_id=? ORDER BY decided_at",
            (state["run_id"],),
        ).fetchall()
    return {
        "issues": state.get("review_issues", [])[-40:],
        "decisions": [dict(row) for row in rows],
    }


@app.get("/api/v1/runs/{run}/audit")
async def run_audit(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    return {
        "run_id": state["run_id"],
        "events": audit.timeline(state["run_id"]),
        "workflow_version": state.get("workflow_version"),
        "prompt_version": state.get("prompt_version"),
        "policy_version": state.get("policy_version"),
        "source_sha256": state.get("source_sha256"),
        "prepared_sha256": state.get("prepared_sha256"),
        "export_manifest": state.get("export_manifest"),
    }


@app.get("/api/v1/runs/{run}/graph-inspector")
async def graph_inspector(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    nodes = [
        "ingest_validate",
        "phi_screen",
        "modality_gate",
        "imaging_readiness",
        "derived_image_safety_check",
        "generate_draft",
        "deterministic_contract_gate",
        "visual_consistency_review",
        "text_quality_review",
        "human_approval",
        "export_approved_draft",
    ]
    events = audit.timeline(state["run_id"])
    completed = list(dict.fromkeys(event["node"] for event in events if event["node"] in nodes))
    for status_key, node in (
        ("contract_status", "deterministic_contract_gate"),
        ("grounding_status", "visual_consistency_review"),
        ("quality_status", "text_quality_review"),
    ):
        if state.get(status_key) in {"PASS", "FAIL"} and node not in completed:
            completed.append(node)
    if (
        state.get("human_decision") or state.get("status") == "AWAITING_HUMAN_APPROVAL"
    ) and "human_approval" not in completed:
        completed.append("human_approval")
    completed.sort(key=nodes.index)
    current = state.get("current_node") or (completed[-1] if completed else nodes[0])
    with audit.connect() as connection:
        model_calls = connection.execute(
            "SELECT stage,model_id,latency_ms,status,output_sha256,created_at FROM model_calls WHERE run_id=? ORDER BY created_at",
            (state["run_id"],),
        ).fetchall()
    return {
        "run_id": state["run_id"],
        "thread_id": state["thread_id"],
        "current_node": current,
        "completed_nodes": completed,
        "pending_nodes": [node for node in nodes if node not in completed],
        "failed_edge": state.get("error"),
        "attempt": state.get("attempt", 0),
        "revision": state.get("revision", 0),
        "node_events": events,
        "preparation": {
            "status": state.get("readiness_status"),
            "receipt_id": state.get("readiness_receipt_id"),
            "policy_version": state.get("preparation_policy_version"),
            "operations": state.get("preparation_operations", []),
            "metrics": state.get("preparation_metrics", {}),
            "warnings": state.get("preparation_warnings", []),
            "source_sha256": state.get("source_sha256"),
            "prepared_sha256": state.get("prepared_sha256"),
        },
        "model_calls": [dict(row) for row in model_calls],
        "human_decision": state.get("human_decision"),
        "observability": "Local structured events, SQLite checkpoints, and audit receipts; no hosted tracing required",
    }


@app.get("/api/v1/runs/{run}/events")
async def run_events(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    return {"run": state, "events": audit.timeline(state["run_id"])[-100:], "polling_hint_ms": 3000}


@app.post("/api/v1/runs/{run}/cancel", response_model=RunResponse)
async def cancel_run(request: Request, run: str, username: str = Depends(actor)) -> dict[str, str]:
    csrf(request)
    state_for(run)
    try:
        status = db.request_cancel(run_id(run))
    except InvalidTransition as exc:
        raise HTTPException(409, str(exc)) from exc
    db.security_event("RUN_CANCELLED", username, run_id(run))
    return {"run_id": run_id(run), "status": status}


@app.post("/api/v1/runs/{run}/retry", response_model=RunResponse, status_code=202)
async def retry_run(request: Request, run: str, username: str = Depends(actor)) -> dict[str, str]:
    csrf(request)
    state = state_for(run)
    if state.get("status") != "FAILED" or not (state.get("error") or {}).get("retryable"):
        raise HTTPException(
            409,
            "Only retryable technical failures can be retried; gate outcomes cannot be overridden",
        )
    job = db.job_for_run(state["run_id"])
    if not job:
        raise HTTPException(404, "Run not found")
    payload = json.loads(job["payload_json"])
    original = payload.get("state", {}).get("source_path")
    if not original or not Path(original).is_file():
        raise HTTPException(409, "The original controlled upload is unavailable for retry")
    new_state = initial_state(
        original,
        inference_mode=settings.inference_mode,
        workflow_version=settings.workflow_version,
        max_attempts=settings.max_attempts,
        max_total_model_calls=settings.max_total_model_calls,
        declared_modality=state.get("declared_modality"),
        synthetic_or_authorized=True,
        vision_model_id=settings.vision_model,
        text_model_id=settings.text_model,
    )
    new_run = new_state["run_id"]
    db.enqueue(new_run, "START", {"state": new_state})
    queued = public_state(dict(new_state))
    queued["status"] = "QUEUED"
    db.save_snapshot(queued, "QUEUED")
    db.security_event("RUN_RETRIED", username, state["run_id"], {"new_run_id": new_run})
    return {"run_id": new_run, "status": "QUEUED"}


@app.get("/api/v1/runs/{run}/image")
async def run_image(run: str, _: str = Depends(actor)) -> FileResponse:
    state = state_for(run)
    artifact = state.get("prepared_artifact_id")
    if not artifact:
        raise HTTPException(404, "Derived image not found")
    validate_id(artifact)
    path = ArtifactStore(settings.data_root).derived_path(state["run_id"], artifact, ".png")
    if not path.is_file():
        raise HTTPException(404, "Derived image not found")
    return FileResponse(path, media_type="image/png")


@app.get("/api/v1/runs/{run}/source-preview")
async def source_preview(run: str, _: str = Depends(actor)) -> FileResponse:
    state = state_for(run)
    artifact = state.get("sanitized_artifact_id")
    if not artifact:
        raise HTTPException(404, "Sanitized source not found")
    validate_id(artifact)
    store = ArtifactStore(settings.data_root)
    path: Path
    if state.get("source_format") == "DICOM":
        from ..imaging.dicom_io import read_dicom
        from ..imaging.rendering import render_dicom, save_png

        dataset = read_dicom(store.derived_path(state["run_id"], artifact, ".dcm"))
        image, _metadata = render_dicom(dataset)
        path = store.derived_path(state["run_id"], artifact, ".png")
        save_png(image, path)
    else:
        path = store.derived_path(state["run_id"], artifact, ".png")
    if not path.is_file():
        raise HTTPException(404, "Sanitized source preview not found")
    return FileResponse(path, media_type="image/png")


@app.get("/api/v1/runs/{run}/comparison", response_class=HTMLResponse)
async def image_comparison(run: str, _: str = Depends(actor)) -> HTMLResponse:
    state = state_for(run)
    if not state.get("prepared_artifact_id"):
        raise HTTPException(404, "Prepared comparison unavailable")
    body = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Source and prepared image</title><style>body{{font-family:system-ui;background:#101b20;color:#eef;margin:0;padding:20px}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}}figure{{margin:0}}img{{max-width:100%;height:auto;background:#05090b}}figcaption{{margin:8px 0;font-size:14px}}</style></head><body><main><figure><figcaption>PHI-screened source preview</figcaption><img src='/api/v1/runs/{state["run_id"]}/source-preview' alt='PHI-screened source preview'></figure><figure><figcaption>Prepared model input</figcaption><img src='/api/v1/runs/{state["run_id"]}/image' alt='Prepared model input'></figure></main></body></html>"""
    return HTMLResponse(body)


@app.get("/api/v1/runs/{run}/preparation-receipt")
async def preparation_receipt(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    receipt = state.get("readiness_receipt_id")
    if not receipt:
        return {
            "status": "LEGACY_NO_PREPARATION_RECEIPT",
            "run_id": state["run_id"],
            "warnings": state.get("preparation_warnings", []),
        }
    validate_id(receipt)
    path = (
        ArtifactStore(settings.data_root).run_dir(state["run_id"], "runs")
        / f"preparation_{receipt}.json"
    )
    if not path.is_file():
        raise HTTPException(404, "Preparation receipt not found")
    return cast(dict[str, Any], json.loads(path.read_text()))


@app.get("/api/v1/runs/{run}/draft")
async def run_draft(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    return {
        "run_id": state["run_id"],
        "draft": state.get("draft"),
        "revision": state.get("revision", 0),
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/v1/runs/{run}/manifest")
async def run_manifest(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    return state.get("export_manifest") or {
        key: state.get(key)
        for key in (
            "run_id",
            "workflow_version",
            "prompt_version",
            "policy_version",
            "source_sha256",
            "prepared_sha256",
            "inference_mode",
            "vision_model_id",
            "text_model_id",
        )
    }


@app.post("/api/v1/runs/{run}/decision", response_model=RunResponse, status_code=202)
async def doctor_decision(
    request: Request, run: str, body: DecisionRequest, username: str = Depends(actor)
) -> dict[str, str]:
    csrf(request)
    state = state_for(run)
    job = db.job_for_run(state["run_id"])
    if (
        not job
        or job["status"] != "INTERRUPTED"
        or state.get("status") != "AWAITING_HUMAN_APPROVAL"
    ):
        raise HTTPException(409, "Run is not awaiting a doctor decision")
    decision = HumanDecision(decision=body.decision, reviewer_display_name=username, note=body.note)
    if decision.decision == "APPROVE" and any(
        state.get(key) != "PASS"
        for key in ("contract_status", "grounding_status", "quality_status")
    ):
        raise HTTPException(409, "Approval requires every gate to pass")
    db.requeue(state["run_id"], "DECISION", {"decision": decision.model_dump()})
    updated = {**state, "status": "DECISION_QUEUED"}
    db.save_snapshot(updated, "DECISION_QUEUED")
    db.security_event(
        "DOCTOR_DECISION_QUEUED",
        username,
        state["run_id"],
        {"decision": decision.decision, "revision": state.get("revision", 0)},
    )
    return {"run_id": state["run_id"], "status": "DECISION_QUEUED"}


@app.get("/api/v1/runs/{run}/exports")
async def list_exports(run: str, _: str = Depends(actor)) -> dict[str, Any]:
    state = state_for(run)
    manifest = state.get("export_manifest")
    if state.get("status") != "APPROVED_DRAFT_EXPORTED" or not manifest:
        return {"run_id": state["run_id"], "eligible": False, "exports": []}
    labels = {
        "report_json": "JSON report",
        "report_markdown": "Markdown report",
        "manifest": "Provenance manifest",
    }
    return {
        "run_id": state["run_id"],
        "eligible": True,
        "exports": [
            {"export_id": key, "filename": filename, "sha256": manifest["hashes"].get(filename)}
            for key, filename in manifest["files"].items()
        ],
        "labels": labels,
        "manifest": manifest,
    }


@app.get("/api/v1/runs/{run}/exports/{export_id}")
async def download_export(run: str, export_id: str, _: str = Depends(actor)) -> FileResponse:
    state = state_for(run)
    manifest = state.get("export_manifest")
    if (
        state.get("status") != "APPROVED_DRAFT_EXPORTED"
        or not manifest
        or export_id not in manifest.get("files", {})
    ):
        raise HTTPException(404, "Export not found")
    filename = manifest["files"][export_id]
    if Path(filename).name != filename:
        raise HTTPException(404, "Export not found")
    path = settings.data_root / "exports" / filename
    if not path.is_file():
        raise HTTPException(404, "Export not found")
    media_type = "application/json" if filename.endswith(".json") else "text/markdown"
    return FileResponse(path, media_type=media_type, filename=filename)


frontend = Path(__file__).resolve().parents[3] / "frontend" / "dist"
if frontend.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend / "assets")), name="assets")


@app.get("/{path:path}")
async def frontend_app(path: str) -> FileResponse:
    if path.startswith(("api/", "health/")) or path in {"docs", "redoc", "openapi.json"}:
        raise HTTPException(404, "Not found")
    index = frontend / "index.html"
    if not index.is_file():
        raise HTTPException(503, "Frontend is not built; run npm run build in frontend")
    return FileResponse(index, media_type="text/html")
