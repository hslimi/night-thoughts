from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from pydicom.datadict import keyword_for_tag
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid

from ..artifacts import ArtifactStore, sha256_file
from ..audit import AuditDB, utc_now
from ..config import Settings
from ..constants import PHI_POLICY_VERSION
from ..imaging.dicom_io import DicomValidationError, read_dicom
from ..imaging.phi_ocr import OCRError, screen_image_text
from ..imaging.rendering import render_dicom, render_raster, save_png
from ..schemas import safe_error

IDENTIFYING_TAGS = {
    "PatientName",
    "PatientID",
    "IssuerOfPatientID",
    "OtherPatientIDs",
    "OtherPatientNames",
    "PatientBirthDate",
    "PatientBirthTime",
    "PatientSex",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "PatientMotherBirthName",
    "ResponsiblePerson",
    "ReferringPhysicianName",
    "ReferringPhysicianIdentification",
    "PerformingPhysicianName",
    "OperatorsName",
    "InstitutionName",
    "InstitutionAddress",
    "StationName",
    "InstitutionalDepartmentName",
    "PhysiciansOfRecord",
    "NameOfPhysiciansReadingStudy",
    "AccessionNumber",
    "StudyID",
    "StudyDate",
    "StudyTime",
    "SeriesDate",
    "SeriesTime",
    "AcquisitionDate",
    "AcquisitionTime",
    "ContentDate",
    "ContentTime",
    "InstanceCreationDate",
    "InstanceCreationTime",
    "RequestingPhysician",
    "ScheduledPerformingPhysicianName",
    "AdmissionID",
    "CurrentPatientLocation",
    "PatientState",
    "ClinicalTrialSubjectID",
}
DESCRIPTIVE_TAGS = {
    "StudyDescription",
    "SeriesDescription",
    "ProcedureCodeSequence",
    "AdmittingDiagnosesDescription",
    "MedicalAlerts",
    "Allergies",
    "AdditionalPatientHistory",
    "Occupation",
    "PatientComments",
    "ImageComments",
    "RequestedProcedureDescription",
    "ReasonForStudy",
}


def phi_screen(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    store = ArtifactStore(settings.data_root)
    source = Path(state["source_path"])
    derived_id = uuid.uuid4().hex
    reasons: list[str] = []
    actions: dict[str, int] = {}
    dataset: Dataset | None = None
    try:
        if state["source_format"] == "DICOM":
            dataset = read_dicom(source, validate_scope=False)
            reasons.extend(_screen_dicom(dataset))
            actions["identifying_or_descriptive_fields"] = len(reasons)
            if reasons:
                raise PHIBlocked(reasons)
            derived = store.derived_path(state["run_id"], derived_id, ".dcm")
            _replace_internal_uids(dataset)
            actions["internal_uids_replaced"] = 3
            dataset.save_as(derived, enforce_file_format=True)
            os.chmod(derived, 0o600)
            checked = read_dicom(derived, validate_scope=False)
            image, _ = render_dicom(checked)
            ocr_path = store.derived_path(state["run_id"], uuid.uuid4().hex, ".png")
            save_png(image, ocr_path)
            suffix = ".dcm"
        else:
            derived = store.derived_path(state["run_id"], derived_id, ".png")
            image, _ = render_raster(source)
            save_png(image, derived)
            os.chmod(derived, 0o600)
            actions["raster_metadata_removed"] = 1
            ocr_path = derived
            suffix = ".png"
        try:
            ocr = screen_image_text(ocr_path)
            reasons.extend(ocr.reasons)
        except OCRError:
            reasons.append("OCR_ENGINE_FAILURE")
            ocr = None
        if reasons:
            raise PHIBlocked(reasons)
    except (PHIBlocked, DicomValidationError, OSError, ValueError):
        if not reasons:
            reasons = [
                "DICOM_POLICY_FAILURE"
                if state["source_format"] == "DICOM"
                else "IMAGE_SCREEN_FAILURE"
            ]
        receipt_id = _receipt(
            state,
            settings,
            derived_id,
            source,
            derived if "derived" in locals() else None,
            "BLOCKED",
            reasons,
            actions,
            None,
        )
        _audit(state, settings, "PHI_BLOCKED", reasons)
        return {
            "status": "QUARANTINED",
            "phi_status": "BLOCKED",
            "phi_reasons": reasons,
            "phi_receipt_id": receipt_id,
            "error": safe_error("PHI_SCREEN_BLOCKED", "Input failed PHI screening"),
        }
    sanitized_hash = sha256_file(derived)
    receipt_id = _receipt(state, settings, derived_id, source, derived, "CLEAR", [], actions, ocr)
    AuditDB(settings.data_root / "nt_imaging.sqlite3").artifact(
        state["run_id"], derived_id, "PHI_SCREENED", sanitized_hash, derived.stat().st_size
    )
    _audit(state, settings, "PHI_CLEAR", [])
    return {
        "status": "INGESTED",
        "source_path": str(derived),
        "sanitized_artifact_id": derived_id,
        "source_format": state["source_format"],
        "sanitized_sha256": sanitized_hash,
        "phi_status": "CLEAR",
        "phi_reasons": [],
        "phi_receipt_id": receipt_id,
        "error": None,
    }


class PHIBlocked(ValueError):
    pass


def _screen_dicom(dataset: Dataset) -> list[str]:
    reasons: set[str] = set()
    for element in dataset:
        if element.tag.is_private:
            reasons.add("DICOM_PRIVATE_TAG")
        if element.VR == "SQ":
            reasons.add("DICOM_NESTED_SEQUENCE")
        if 0x6000 <= element.tag.group <= 0x60FF and element.tag.group % 2 == 0:
            reasons.add("DICOM_OVERLAY")
        keyword = keyword_for_tag(element.tag)
        if keyword in IDENTIFYING_TAGS and element.value not in (None, ""):
            reasons.add("DICOM_IDENTIFYING_METADATA")
        if keyword in DESCRIPTIVE_TAGS and element.value not in (None, ""):
            reasons.add("DICOM_DESCRIPTIVE_METADATA")
        if element.VR in {"DA", "DT", "TM", "PN"} and element.value not in (None, ""):
            reasons.add("DICOM_IDENTIFYING_OR_TEMPORAL_VALUE")
    return sorted(reasons)


def _replace_internal_uids(dataset: Dataset) -> None:
    dataset.SOPInstanceUID = generate_uid()
    dataset.file_meta.MediaStorageSOPInstanceUID = dataset.SOPInstanceUID
    dataset.StudyInstanceUID = generate_uid()
    dataset.SeriesInstanceUID = generate_uid()
    dataset.pop("PatientIdentityRemoved", None)


def _receipt(
    state: dict[str, Any],
    settings: Settings,
    derived_id: str,
    source: Path,
    derived: Path | None,
    verdict: str,
    reasons: list[str],
    actions: dict[str, int],
    ocr: Any,
) -> str:
    receipt_id = uuid.uuid4().hex
    store = ArtifactStore(settings.data_root)
    path = (
        store.run_dir(state["run_id"], "quarantine" if verdict == "BLOCKED" else "runs")
        / f"phi_{receipt_id}.json"
    )
    store.write_json(
        path,
        {
            "receipt_id": receipt_id,
            "run_id": state["run_id"],
            "artifact_id": state["artifact_id"],
            "policy_version": PHI_POLICY_VERSION,
            "source_sha256": state["source_sha256"],
            "derived_sha256": sha256_file(derived) if derived and derived.exists() else None,
            "action_counts": actions,
            "reason_codes": reasons,
            "ocr": None
            if ocr is None
            else {
                "engine": ocr.engine,
                "version": ocr.version,
                "language": ocr.language,
                "recognition_level": ocr.recognition_level,
                "minimum_confidence": ocr.minimum_confidence,
            },
            "verdict": verdict,
            "timestamp": utc_now(),
            "marker": "PHI_SCREENED",
        },
    )
    return receipt_id


def _audit(state: dict[str, Any], settings: Settings, event: str, reasons: list[str]) -> None:
    AuditDB(settings.data_root / "nt_imaging.sqlite3").event(
        state["run_id"],
        "phi_screen",
        event,
        workflow_version=state["workflow_version"],
        reason_codes=reasons,
    )
