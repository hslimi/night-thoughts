from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any, cast

from langgraph.errors import GraphInterrupt

from ..config import Settings
from .db import ControlDB


def event_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    value = cast(dict[str, Any], json.loads(json.dumps(state, default=str)))
    value.pop("source_path", None)
    value.pop("__interrupt__", None)
    return value


def emit(
    state: dict[str, Any],
    settings: Settings,
    event_type: str,
    node_name: str,
    *,
    duration_ms: int | None = None,
    model_call_sequence: int | None = None,
    payload: dict[str, Any] | None = None,
) -> int:
    safe_payload = {"snapshot": event_snapshot(state), **(payload or {})}
    return ControlDB(settings.data_root / "controlplane.sqlite3").record_event(
        event_type,
        state=state,
        node_name=node_name,
        duration_ms=duration_ms,
        model_call_sequence=model_call_sequence,
        payload=safe_payload,
    )


def model_call_started(
    state: dict[str, Any], settings: Settings, stage: str, sequence: int, model_id: str
) -> None:
    state = {**state, "current_model_call_sequence": sequence, "current_model_stage": stage}
    emit(
        state,
        settings,
        "MODEL_CALL_STARTED",
        stage.lower(),
        model_call_sequence=sequence,
        payload={"stage": stage, "model_id": model_id, "call_state": "RUNNING"},
    )


def model_call_completed(
    state: dict[str, Any],
    settings: Settings,
    stage: str,
    sequence: int,
    model_id: str,
    latency_ms: int,
    output_sha256: str,
) -> None:
    emit(
        state,
        settings,
        "MODEL_CALL_COMPLETED",
        stage.lower(),
        duration_ms=latency_ms,
        model_call_sequence=sequence,
        payload={
            "stage": stage,
            "model_id": model_id,
            "call_state": "COMPLETED",
            "output_sha256": output_sha256,
        },
    )


def model_call_failed(
    state: dict[str, Any],
    settings: Settings,
    stage: str,
    sequence: int,
    model_id: str,
    latency_ms: int,
    error_category: str,
) -> None:
    emit(
        state,
        settings,
        "MODEL_CALL_FAILED",
        stage.lower(),
        duration_ms=latency_ms,
        model_call_sequence=sequence,
        payload={
            "stage": stage,
            "model_id": model_id,
            "call_state": "FAILED",
            "error_category": error_category,
        },
    )


def track_node(
    name: str,
    function: Callable[[dict[str, Any]], dict[str, Any]],
    settings: Settings,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def tracked(state: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        state = {**state, "current_node": name}
        if name == "generate_draft":
            if state.get("revision", 0) > 0 and state.get("attempt", 0) == 0:
                emit(state, settings, "REVISION_STARTED", name)
            emit(
                state,
                settings,
                "ATTEMPT_STARTED",
                name,
                payload={"attempt": state.get("attempt", 0) + 1},
            )
        if name == "imaging_readiness":
            emit(state, settings, "PREPARATION_STARTED", name)
        if name == "export_approved_draft":
            emit(state, settings, "EXPORT_STARTED", name)
        emit(state, settings, "NODE_STARTED", name)
        try:
            result = function(state)
        except GraphInterrupt:
            interrupted = {**state, "status": "AWAITING_HUMAN_APPROVAL", "current_node": name}
            if state.get("revision", 0) > 0:
                emit(interrupted, settings, "REVISION_COMPLETED", name)
            emit(interrupted, settings, "HUMAN_APPROVAL_REQUIRED", name)
            raise
        except Exception as exc:
            failed = {
                **state,
                "status": "FAILED",
                "error": {"code": "NODE_EXECUTION_FAILED", "message": type(exc).__name__},
            }
            emit(
                failed,
                settings,
                "NODE_FAILED",
                name,
                duration_ms=int((time.monotonic() - started) * 1000),
                payload={"error_category": type(exc).__name__},
            )
            raise
        updated = {**state, **result, "current_node": name}
        duration = int((time.monotonic() - started) * 1000)
        failure_status = updated.get("status") in {
            "FAILED",
            "MODEL_OUTPUT_INVALID",
            "IMAGE_PREPARATION_FAILED",
        }
        emit(
            updated,
            settings,
            "NODE_FAILED" if failure_status else "NODE_COMPLETED",
            name,
            duration_ms=duration,
            payload={"error": updated.get("error")},
        )
        if name == "derived_image_safety_check":
            emit(
                updated,
                settings,
                "DERIVED_SAFETY_RESULT",
                name,
                payload={"derived_phi_status": updated.get("derived_phi_status")},
            )
        gate_fields = {
            "phi_screen": "phi_status",
            "modality_gate": "modality_status",
            "deterministic_contract_gate": "contract_status",
            "visual_consistency_review": "grounding_status",
            "text_quality_review": "quality_status",
        }
        if name in gate_fields:
            field = gate_fields[name]
            emit(
                updated,
                settings,
                "GATE_RESULT",
                name,
                payload={"gate": field, "result": updated.get(field)},
            )
        if name == "imaging_readiness":
            emit(
                updated,
                settings,
                "PREPARATION_COMPLETED",
                name,
                duration_ms=duration,
                payload={
                    "readiness_status": updated.get("readiness_status"),
                    "readiness_receipt_id": updated.get("readiness_receipt_id"),
                    "prepared_sha256": updated.get("prepared_sha256"),
                },
            )
        if (
            name == "generate_draft"
            and updated.get("error")
            and (updated["error"] or {}).get("code")
            in {"RETRY_EXHAUSTED", "MODEL_CALL_BUDGET_EXHAUSTED"}
        ):
            emit(updated, settings, "ATTEMPT_EXHAUSTED", name, payload=updated["error"])
        if name == "human_approval" and updated.get("status") == "REVISION_REQUESTED":
            decision = updated.get("human_decision") or {}
            emit(
                updated,
                settings,
                "REVISION_REQUESTED",
                name,
                payload={"note": decision.get("note", ""), "revision": updated.get("revision")},
            )
        if name == "human_approval" and updated.get("human_decision"):
            emit(
                updated,
                settings,
                "HUMAN_DECISION_RECORDED",
                name,
                payload=updated["human_decision"],
            )
        if name == "export_approved_draft":
            emit(
                updated,
                settings,
                "EXPORT_COMPLETED",
                name,
                duration_ms=duration,
                payload={"export_manifest": updated.get("export_manifest")},
            )
        if updated.get("status") in {
            "APPROVED_DRAFT_EXPORTED",
            "HUMAN_REJECTED",
            "QUARANTINED",
            "NEEDS_HUMAN_REVIEW",
            "CANCELLED",
            "FAILED",
            "MODEL_OUTPUT_INVALID",
            "IMAGE_PREPARATION_FAILED",
        } and name in {
            "export_approved_draft",
            "reject_draft",
            "quarantine",
            "needs_review",
            "fail_closed",
        }:
            emit(
                updated,
                settings,
                "RUN_FAILED" if failure_status else "RUN_COMPLETED",
                name,
                duration_ms=duration,
            )
        return result

    return tracked
