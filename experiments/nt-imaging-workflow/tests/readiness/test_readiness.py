from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import pytest
from langgraph.checkpoint.memory import InMemorySaver
from PIL import Image
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, ImplicitVRLittleEndian, generate_uid

from nt_imaging.artifacts import ArtifactStore
from nt_imaging.config import Settings
from nt_imaging.graph import build_graph
from nt_imaging.imaging.readiness import CODE_VERSION, PreparationError, prepare_artifact
from nt_imaging.nodes.readiness import derived_image_safety_check
from nt_imaging.state import initial_state


def dicom(
    path: Path,
    pixels: np.ndarray,
    photometric: str,
    *,
    slope: float = 1,
    intercept: float = 0,
    center: float | None = None,
    width: float | None = None,
    bits: int = 16,
    transfer_syntax: str = ExplicitVRLittleEndian,
    voi_lut: bool = False,
) -> None:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.1.1"
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = transfer_syntax
    ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    ds.SOPClassUID = meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.Modality = "DX"
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = photometric
    ds.BitsAllocated = bits
    ds.BitsStored = bits
    ds.HighBit = bits - 1
    ds.PixelRepresentation = 1 if pixels.dtype.kind == "i" else 0
    ds.RescaleSlope = slope
    ds.RescaleIntercept = intercept
    if center is not None:
        ds.WindowCenter = center
        ds.WindowWidth = width
    if voi_lut:
        lut = FileDataset(str(path), {})
        lut.LUTDescriptor = [256, 0, 8]
        lut.LUTData = np.arange(256, dtype="<u2").tobytes()
        ds.VOILUTSequence = [lut]
    encoded = (
        pixels.astype(np.int8 if pixels.dtype.kind == "i" and bits == 8 else np.uint8)
        if bits == 8
        else pixels
    )
    ds.PixelData = encoded.tobytes()
    ds.save_as(path, enforce_file_format=True)


def prepare(tmp_path: Path, pixels: np.ndarray, photometric: str = "MONOCHROME2", **kwargs):
    settings = Settings.from_env()
    store = ArtifactStore(settings.data_root)
    run_id = str(uuid.uuid4())
    artifact_id = uuid.uuid4().hex
    dicom(store.derived_path(run_id, artifact_id, ".dcm"), pixels, photometric, **kwargs)
    return prepare_artifact(
        store, run_id, artifact_id, "DICOM", Path(__file__).resolve().parents[2]
    )


def test_monochrome1_and_monochrome2(tmp_path: Path) -> None:
    pixels = np.array([[0, 128, 255] * 16] * 16, dtype=np.uint16)
    normal = prepare(tmp_path, pixels, bits=8)
    inverted = prepare(tmp_path, 255 - pixels, "MONOCHROME1", bits=8)
    assert normal["preparation_metrics"]["intensity_min"] == 0
    assert normal["preparation_metrics"]["intensity_max"] == 255
    assert inverted["preparation_metrics"]["intensity_min"] == 0
    assert inverted["preparation_metrics"]["intensity_max"] == 255
    assert "MONOCHROME1_INVERSION" in inverted["preparation_operations"]
    store = ArtifactStore(Settings.from_env().data_root)
    normal_image = Image.open(
        store.derived_path(normal["run_id"], normal["prepared_artifact_id"], ".png")
    )
    inverted_image = Image.open(
        store.derived_path(inverted["run_id"], inverted["prepared_artifact_id"], ".png")
    )
    assert np.array_equal(np.asarray(normal_image), np.asarray(inverted_image))


def test_rescale_then_voi_and_signed_pixels(tmp_path: Path) -> None:
    pixels = np.array([[-1024, 0, 1024] * 16] * 16, dtype=np.int16)
    receipt = prepare(tmp_path, pixels, center=0, width=2048)
    assert 120 <= receipt["preparation_metrics"]["intensity_p99"] <= 255
    assert any(op.startswith("MODALITY_LUT") for op in receipt["preparation_operations"])
    assert "VOI_WINDOW_FIRST" in receipt["preparation_operations"]
    signed = prepare(tmp_path, pixels)
    assert signed["preparation_metrics"]["signed"] is True
    assert any(op.startswith("SIGNED_THEORETICAL_SHIFT") for op in signed["preparation_operations"])


def test_voi_lut_implicit_syntax_and_orientation(tmp_path: Path) -> None:
    pixels = np.arange(48 * 48, dtype=np.uint16).reshape(48, 48) % 256
    pixels = pixels.astype(np.uint8)
    receipt = prepare(
        tmp_path,
        pixels,
        bits=8,
        transfer_syntax=ImplicitVRLittleEndian,
        voi_lut=True,
    )
    assert "VOI_LUT_FIRST" in receipt["preparation_operations"]
    assert receipt["preparation_metrics"]["source_transfer_syntax"] == ImplicitVRLittleEndian
    assert "PRESERVE_DECODED_ORIENTATION_NO_FLIP" in receipt["preparation_operations"]
    store = ArtifactStore(Settings.from_env().data_root)
    prepared = Image.open(
        store.derived_path(receipt["run_id"], receipt["prepared_artifact_id"], ".png")
    )
    assert np.array_equal(np.asarray(prepared), pixels)


def test_aspect_ratio_and_idempotency(tmp_path: Path) -> None:
    pixels = np.full((1024, 2048), 127, dtype=np.uint16)
    pixels[200:800, 300:900] = 220
    store = ArtifactStore(Settings.from_env().data_root)
    run_id = str(uuid.uuid4())
    artifact_id = uuid.uuid4().hex
    dicom(store.derived_path(run_id, artifact_id, ".dcm"), pixels, "MONOCHROME2", bits=8)
    root = Path(__file__).resolve().parents[2]
    first = prepare_artifact(store, run_id, artifact_id, "DICOM", root)
    second = prepare_artifact(store, run_id, artifact_id, "DICOM", root)
    assert first == second
    assert first["preparation_metrics"]["prepared_width"] == 1024
    assert first["preparation_metrics"]["prepared_height"] == 512
    assert first["prepared_artifact_id"] == second["prepared_artifact_id"]
    receipt_path = store.run_dir(run_id, "runs") / f"preparation_{first['receipt_id']}.json"
    receipt_path.write_text(receipt_path.read_text().replace(CODE_VERSION, "other-version"))
    with pytest.raises(PreparationError):
        prepare_artifact(store, run_id, artifact_id, "DICOM", root)
    receipt_path.write_text(receipt_path.read_text().replace("other-version", CODE_VERSION))
    prepared_path = store.derived_path(run_id, first["prepared_artifact_id"], ".png")
    Image.new("L", (16, 16), 0).save(prepared_path)
    with pytest.raises(PreparationError):
        prepare_artifact(store, run_id, artifact_id, "DICOM", root)


def test_uniform_input_fails_without_model_calls(tmp_path: Path) -> None:
    settings = Settings.from_env()
    store = ArtifactStore(settings.data_root)
    run_id = str(uuid.uuid4())
    artifact_id = uuid.uuid4().hex
    source = store.derived_path(run_id, artifact_id, ".png")
    Image.new("L", (64, 64), 0).save(source)
    state = initial_state(str(source), inference_mode="MOCK", declared_modality="XR")
    state.update({"run_id": run_id, "thread_id": run_id})
    app = build_graph(InMemorySaver())
    result = app.invoke(state, config={"configurable": {"thread_id": run_id}})
    assert result["status"] == "IMAGE_PREPARATION_FAILED"
    assert result["model_calls"] == 0
    assert result["export_manifest"] is None


def test_derived_phi_failure_blocks_drafting(tmp_path: Path) -> None:
    settings = Settings.from_env()
    state = initial_state("unused", inference_mode="MOCK")
    state.update(
        {
            "run_id": str(uuid.uuid4()),
            "thread_id": str(uuid.uuid4()),
            "sanitized_artifact_id": uuid.uuid4().hex,
            "source_format": "PNG",
            "phi_status": "CLEAR",
            "modality_status": "SUPPORTED",
            "source_path": "unused",
            "readiness_status": "READY",
            "prepared_artifact_id": uuid.uuid4().hex,
        }
    )
    state["thread_id"] = state["run_id"]
    store = ArtifactStore(settings.data_root)
    Image.new("L", (64, 64), 127).save(
        store.derived_path(state["run_id"], state["prepared_artifact_id"], ".png")
    )
    from unittest.mock import patch

    from nt_imaging.imaging.phi_ocr import OCRResult

    with patch(
        "nt_imaging.imaging.phi_ocr.screen_image_text",
        return_value=OCRResult(
            verdict="BLOCKED", reasons=["OCR_UNEXPECTED_TEXT"], engine="test", version="test"
        ),
    ):
        result = derived_image_safety_check(state, settings)
    assert result["status"] == "IMAGE_PREPARATION_FAILED"
    assert result["derived_phi_status"] == "BLOCKED"
