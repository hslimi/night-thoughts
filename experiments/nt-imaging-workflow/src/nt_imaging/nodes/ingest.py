from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from ..artifacts import ArtifactError, ArtifactStore
from ..audit import AuditDB, utc_now
from ..config import Settings
from ..imaging.dicom_io import looks_like_dicom
from ..schemas import safe_error


def ingest_validate(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    audit = AuditDB(settings.data_root / "nt_imaging.sqlite3")
    audit.start_run(state)
    source = Path(state["source_path"])
    if not state.get("synthetic_or_authorized"):
        return _fail(
            state,
            settings,
            "DATA_USE_NOT_CONFIRMED",
            "Synthetic or authorized data use was not confirmed",
            "QUARANTINED",
        )
    if source.is_symlink() or not source.is_file():
        return _fail(
            state,
            settings,
            "INVALID_SOURCE",
            "Source must be a regular non-symlink file",
            "NEEDS_HUMAN_REVIEW",
        )
    size = source.stat().st_size
    if size > settings.max_upload_bytes:
        return _fail(
            state,
            settings,
            "UPLOAD_TOO_LARGE",
            "Input exceeds the configured byte limit",
            "NEEDS_HUMAN_REVIEW",
        )
    try:
        with source.open("rb") as handle:
            header = handle.read(256)
        if looks_like_dicom(header):
            source_format = "DICOM"
        elif header.startswith(b"\x89PNG\r\n\x1a\n"):
            source_format = "PNG"
            _check_raster(source, settings)
        elif header.startswith(b"\xff\xd8\xff"):
            source_format = "JPEG"
            _check_raster(source, settings)
        else:
            raise ArtifactError("Content is not a supported PNG, JPEG, or DICOM file")
        stored, digest, stored_size = ArtifactStore(settings.data_root).copy_source(
            source, state["run_id"], state["artifact_id"]
        )
    except (ArtifactError, OSError, ValueError) as exc:
        code = str(exc) if isinstance(exc, ArtifactError) else "Malformed or unreadable input"
        return _fail(state, settings, "INGEST_INVALID", code, "NEEDS_HUMAN_REVIEW")
    audit.artifact(state["run_id"], state["artifact_id"], "SOURCE", digest, stored_size)
    result = {
        "status": "INGESTED",
        "source_path": str(stored),
        "source_sha256": digest,
        "source_size_bytes": stored_size,
        "source_format": source_format,
        "error": None,
    }
    store = ArtifactStore(settings.data_root)
    store.write_json(
        store.run_dir(state["run_id"], "runs") / "run_manifest.json",
        {
            "run_id": state["run_id"],
            "thread_id": state["thread_id"],
            "artifact_id": state["artifact_id"],
            "workflow_version": state["workflow_version"],
            "inference_mode": state["inference_mode"],
            "source_sha256": digest,
            "source_format": source_format,
            "source_size_bytes": stored_size,
            "created_at": utc_now(),
        },
    )
    audit.event(
        state["run_id"],
        "ingest_validate",
        "INGESTED",
        workflow_version=state["workflow_version"],
        metadata={"source_format": source_format, "source_sha256": digest},
    )
    return result


def _check_raster(path: Path, settings: Settings) -> None:
    try:
        with Image.open(path) as image:
            if image.format not in {"PNG", "JPEG"}:
                raise ArtifactError("Image content does not match a supported format")
            if image.width * image.height > settings.max_decoded_pixels:
                raise ArtifactError("Decoded image exceeds the configured pixel limit")
            image.verify()
    except ArtifactError:
        raise
    except Exception as exc:
        raise ArtifactError("Malformed or truncated image") from exc


def _fail(
    state: dict[str, Any], settings: Settings, code: str, message: str, status: str
) -> dict[str, Any]:
    AuditDB(settings.data_root / "nt_imaging.sqlite3").event(
        state["run_id"],
        "ingest_validate",
        "INPUT_REJECTED",
        workflow_version=state["workflow_version"],
        reason_codes=[code],
    )
    return {
        "status": status,
        "error": safe_error(code, message),
        "phi_status": "BLOCKED" if status == "QUARANTINED" else "PENDING",
    }
