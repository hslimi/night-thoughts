from __future__ import annotations

from pathlib import Path
from typing import Any

from ..artifacts import ArtifactStore
from ..audit import AuditDB
from ..config import Settings
from ..controlplane.telemetry import emit
from ..imaging.readiness import PreparationError, prepare_artifact
from ..schemas import safe_error


def imaging_readiness(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    if state.get("phi_status") != "CLEAR" or state.get("modality_status") != "SUPPORTED":
        return {
            "status": "IMAGE_PREPARATION_FAILED",
            "readiness_status": "FAILED",
            "error": safe_error(
                "READINESS_PREREQUISITE", "PHI clearance and supported modality are required"
            ),
        }

    def report_progress(operation: str) -> None:
        emit(
            state,
            settings,
            "PREPARATION_OPERATION_COMPLETED",
            "imaging_readiness",
            payload={"operation": operation},
        )

    try:
        receipt = prepare_artifact(
            ArtifactStore(settings.data_root),
            state["run_id"],
            state["sanitized_artifact_id"],
            state["source_format"],
            Path(__file__).resolve().parents[3],
            progress=report_progress,
        )
    except (PreparationError, OSError, ValueError) as exc:
        AuditDB(settings.data_root / "nt_imaging.sqlite3").event(
            state["run_id"],
            "imaging_readiness",
            "IMAGE_PREPARATION_FAILED",
            workflow_version=state["workflow_version"],
            reason_codes=[str(exc)[:120]],
        )
        return {
            "status": "IMAGE_PREPARATION_FAILED",
            "readiness_status": "FAILED",
            "error": safe_error(
                "IMAGE_PREPARATION_FAILED",
                "Imaging Readiness Agent could not prepare a safe derivative",
            ),
        }
    AuditDB(settings.data_root / "nt_imaging.sqlite3").event(
        state["run_id"],
        "imaging_readiness",
        "IMAGE_READY",
        workflow_version=state["workflow_version"],
        metadata={
            "receipt_id": receipt["receipt_id"],
            "prepared_sha256": receipt["prepared_sha256"],
            "preparation_policy_version": receipt["preparation_policy_version"],
        },
    )
    return {
        "status": "IMAGE_READY",
        "readiness_status": "READY",
        "readiness_receipt_id": receipt["receipt_id"],
        "prepared_artifact_id": receipt["prepared_artifact_id"],
        "prepared_sha256": receipt["prepared_sha256"],
        "display_thumbnail_id": receipt["display_thumbnail_id"],
        "preparation_policy_version": receipt["preparation_policy_version"],
        "preparation_operations": receipt["preparation_operations"],
        "preparation_metrics": receipt["preparation_metrics"],
        "preparation_warnings": receipt["preparation_warnings"],
        "derived_phi_status": "PENDING",
        "error": None,
    }


def derived_image_safety_check(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    if state.get("readiness_status") != "READY" or not state.get("prepared_artifact_id"):
        return {
            "status": "IMAGE_PREPARATION_FAILED",
            "derived_phi_status": "BLOCKED",
            "error": safe_error(
                "DERIVED_SAFETY_PREREQUISITE", "A prepared derivative is required before drafting"
            ),
        }
    if state.get("inference_mode") == "MOCK" and state.get("fault_profile") == "derived_phi_block":
        return {
            "status": "IMAGE_PREPARATION_FAILED",
            "derived_phi_status": "BLOCKED",
            "error": safe_error(
                "DERIVED_PHI_SCREEN_BLOCKED", "Injected derived-image safety failure"
            ),
        }
    from ..imaging.phi_ocr import OCRError, screen_image_text

    try:
        path = ArtifactStore(settings.data_root).derived_path(
            state["run_id"], state["prepared_artifact_id"], ".png"
        )
        result = screen_image_text(path)
    except (OCRError, OSError, ValueError):
        return {
            "status": "IMAGE_PREPARATION_FAILED",
            "derived_phi_status": "BLOCKED",
            "error": safe_error(
                "DERIVED_PHI_SCREEN_FAILED", "Derived-image PHI screening failed closed"
            ),
        }
    if result.verdict != "CLEAR":
        return {
            "status": "IMAGE_PREPARATION_FAILED",
            "derived_phi_status": "BLOCKED",
            "error": safe_error(
                "DERIVED_PHI_SCREEN_BLOCKED", "Derived image contains unexpected text"
            ),
        }
    AuditDB(settings.data_root / "nt_imaging.sqlite3").event(
        state["run_id"],
        "derived_image_safety_check",
        "DERIVED_IMAGE_SAFE",
        workflow_version=state["workflow_version"],
        metadata={"prepared_sha256": state["prepared_sha256"]},
    )
    return {"derived_phi_status": "CLEAR", "status": "IMAGE_READY", "error": None}
