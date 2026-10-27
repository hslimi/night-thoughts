from __future__ import annotations

from pathlib import Path
from typing import Any

from ..audit import AuditDB
from ..config import Settings
from ..imaging.dicom_io import DicomValidationError, read_dicom
from ..schemas import safe_error


def modality_gate(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    try:
        if state["source_format"] == "DICOM":
            dataset = read_dicom(Path(state["source_path"]))
            modality = str(dataset.Modality)
            source = "DICOM_METADATA_VALIDATED"
            reason = "Single-frame CR/DX with supported SOP Class and transfer syntax"
        elif state.get("declared_modality") == "XR":
            modality = "XR"
            source = "USER_DECLARED"
            reason = "User-declared chest radiograph; declaration is not a validated classifier"
        else:
            return _unsupported(
                state, settings, "XR declaration is required for PNG/JPEG", "UNKNOWN"
            )
    except (DicomValidationError, KeyError, OSError, ValueError):
        return _unsupported(
            state, settings, "Modality or image metadata could not be validated", "UNSUPPORTED"
        )
    result = {
        "modality": modality,
        "modality_source": source,
        "modality_status": "SUPPORTED",
        "modality_reason": reason,
        "error": None,
    }
    _audit(state, settings, "MODALITY_SUPPORTED", modality)
    return result


def _unsupported(
    state: dict[str, Any], settings: Settings, reason: str, status: str
) -> dict[str, Any]:
    _audit(state, settings, "MODALITY_UNSUPPORTED", status)
    return {
        "status": "NEEDS_HUMAN_REVIEW",
        "modality_status": status,
        "modality_reason": reason,
        "error": safe_error("MODALITY_UNSUPPORTED", reason),
    }


def _audit(state: dict[str, Any], settings: Settings, event: str, reason: str) -> None:
    AuditDB(settings.data_root / "nt_imaging.sqlite3").event(
        state["run_id"],
        "modality_gate",
        event,
        workflow_version=state["workflow_version"],
        reason_codes=[reason],
    )
