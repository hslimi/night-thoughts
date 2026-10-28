from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..artifacts import ArtifactStore, sha256_bytes
from ..audit import AuditDB
from ..config import Settings
from ..controlplane.telemetry import model_call_completed, model_call_failed, model_call_started
from ..inference.structured import StructuredOutputError, parse_structured
from ..schemas import ReviewResult, safe_error
from .drafting import _issues, provider_for


def visual_consistency_review(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    if state.get("contract_status") != "PASS" or not state.get("draft"):
        return {
            "grounding_status": "FAIL",
            "error": safe_error(
                "GROUNDING_PREREQUISITE", "Visual review requires a passing deterministic gate"
            ),
        }
    return _review(state, settings, "VISUAL_CONSISTENCY")


def text_quality_review(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    if (
        state.get("grounding_status") != "PASS"
        or state.get("contract_status") != "PASS"
        or not state.get("draft")
    ):
        return {
            "quality_status": "PENDING",
            "error": safe_error(
                "QUALITY_PREREQUISITE",
                "Quality review cannot run when visual consistency has not passed",
            ),
        }
    return _review(state, settings, "TEXT_QUALITY")


def _review(state: dict[str, Any], settings: Settings, stage: str) -> dict[str, Any]:
    status_key = "grounding_status" if stage == "VISUAL_CONSISTENCY" else "quality_status"
    if state["model_calls"] >= state["max_total_model_calls"]:
        return {
            status_key: "FAIL",
            "status": "NEEDS_HUMAN_REVIEW",
            "error": safe_error("MODEL_CALL_BUDGET_EXHAUSTED", "Model-call budget exhausted"),
        }
    provider = provider_for(state, settings)
    prompt_name = (
        "visual_consistency_v1.txt" if stage == "VISUAL_CONSISTENCY" else "text_quality_v1.txt"
    )
    prompt = (Path(__file__).resolve().parents[3] / "prompts" / prompt_name).read_text()
    audit = AuditDB(settings.data_root / "nt_imaging.sqlite3")
    calls = 0
    call_started = time.monotonic()
    model_id = (
        state.get("vision_model_id")
        if stage == "VISUAL_CONSISTENCY"
        else state.get("text_model_id")
    ) or "unknown"
    try:
        calls = 1
        model_call_started(state, settings, stage, state["model_calls"] + calls, model_id)
        if stage == "VISUAL_CONSISTENCY":
            response = provider.visual_review(
                ArtifactStore(settings.data_root).derived_path(
                    state["run_id"], state["prepared_artifact_id"], ".png"
                ),
                prompt,
                state["draft"],
            )
        else:
            policy = json.loads(
                (
                    Path(__file__).resolve().parents[3] / "policies" / "cxr_quality_v1.json"
                ).read_text()
            )
            response = provider.quality_review(prompt, state["draft"], policy)
        output_hash = sha256_bytes(response.raw.encode())
        model_call_completed(
            state,
            settings,
            stage,
            state["model_calls"] + calls,
            response.model_id,
            response.latency_ms,
            output_hash,
        )
        result = parse_structured(response.raw, ReviewResult)
    except (StructuredOutputError, TimeoutError, RuntimeError, OSError, ValueError, KeyError):
        model_call_failed(
            state,
            settings,
            stage,
            state["model_calls"] + calls,
            model_id,
            int((time.monotonic() - call_started) * 1000),
            "REVIEW_OUTPUT_INVALID",
        )
        audit.event(
            state["run_id"],
            "visual_consistency_review" if stage == "VISUAL_CONSISTENCY" else "text_quality_review",
            "REVIEW_FAILED",
            workflow_version=state["workflow_version"],
            attempt=state["attempt"],
            reason_codes=["STRUCTURED_REVIEW_INVALID"],
        )
        return {
            status_key: "FAIL",
            "model_calls": state["model_calls"] + calls,
            "error": safe_error("REVIEW_OUTPUT_INVALID", "Model-assisted review failed closed"),
        }
    audit.model_call(
        state["run_id"],
        stage,
        response.model_id,
        response.latency_ms,
        "SUCCESS",
        sha256_bytes(response.raw.encode()),
    )
    issues = [
        {**issue.model_dump(), "stage": stage, "attempt": state["attempt"]}
        for issue in result.issues
    ]
    audit.event(
        state["run_id"],
        stage.lower(),
        f"{stage}_{result.verdict}",
        workflow_version=state["workflow_version"],
        attempt=state["attempt"],
        reason_codes=[i.code for i in result.issues],
    )
    return {
        status_key: result.verdict,
        "model_calls": state["model_calls"] + calls,
        "review_issues": _issues(state, issues),
        "error": None
        if result.verdict == "PASS"
        else safe_error(f"{stage}_FAILED", "Model-assisted review did not pass"),
    }
