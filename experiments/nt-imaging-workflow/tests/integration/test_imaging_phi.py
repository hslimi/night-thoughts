from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver

from nt_imaging.graph import build_graph
from nt_imaging.imaging.phi_ocr import OCRError
from nt_imaging.state import initial_state


def run(path: Path, modality: str | None = "XR") -> dict:
    state = initial_state(str(path), inference_mode="MOCK", declared_modality=modality)
    return build_graph(InMemorySaver()).invoke(
        state, config={"configurable": {"thread_id": state["thread_id"]}}
    )


def test_dicom_metadata_phi_quarantines(fixture_dir: Path) -> None:
    result = run(fixture_dir / "chest_phi.dcm", None)
    assert result["status"] == "QUARANTINED"
    assert "DICOM_IDENTIFYING_METADATA" in result["phi_reasons"]
    assert result["attempt"] == 0


def test_dicom_private_tag_quarantines(fixture_dir: Path) -> None:
    result = run(fixture_dir / "chest_private.dcm", None)
    assert result["status"] == "QUARANTINED"
    assert "DICOM_PRIVATE_TAG" in result["phi_reasons"]


def test_burned_in_text_quarantines(fixture_dir: Path) -> None:
    result = run(fixture_dir / "chest_burned_in.dcm", None)
    assert result["status"] == "QUARANTINED"
    assert "OCR_UNEXPECTED_TEXT" in result["phi_reasons"]


def test_allowed_marker_reaches_interrupt(fixture_dir: Path) -> None:
    result = run(fixture_dir / "chest_marker.dcm", None)
    assert "__interrupt__" in result


def test_ocr_failure_fails_closed(clean_fixture: Path) -> None:
    with patch("nt_imaging.nodes.phi.screen_image_text", side_effect=OCRError("synthetic failure")):
        result = run(clean_fixture)
    assert result["status"] == "QUARANTINED"
    assert "OCR_ENGINE_FAILURE" in result["phi_reasons"]


def test_missing_modality_declaration_never_drafts(clean_fixture: Path) -> None:
    result = run(clean_fixture, None)
    assert result["status"] == "NEEDS_HUMAN_REVIEW"
    assert result["attempt"] == 0


def test_malformed_and_magic_mismatch_fail_before_inference(fixture_dir: Path) -> None:
    for name in ("truncated.png", "mismatch.png"):
        result = run(fixture_dir / name)
        assert result["status"] == "NEEDS_HUMAN_REVIEW"
        assert result["attempt"] == 0


def test_pixel_limit_blocks_before_phi(fixture_dir: Path) -> None:
    result = run(fixture_dir / "too_many_pixels.png")
    assert result["status"] == "NEEDS_HUMAN_REVIEW"
    assert result["phi_status"] == "PENDING"
    assert result["attempt"] == 0


def test_stable_prepared_hash(clean_fixture: Path) -> None:
    first = run(clean_fixture)
    second = run(clean_fixture)
    assert len(first["prepared_sha256"]) == 64
    assert first["prepared_sha256"] == second["prepared_sha256"]
    assert first["preparation_metrics"]["prepared_width"] == 384
    assert first["prepared_artifact_id"] == second["prepared_artifact_id"]
