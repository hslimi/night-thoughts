from __future__ import annotations

from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from nt_imaging.audit import AuditDB
from nt_imaging.config import Settings
from nt_imaging.graph import build_graph
from nt_imaging.state import initial_state


def start(path: Path, fault: str = "none", modality: str | None = "XR"):
    state = initial_state(
        str(path), inference_mode="MOCK", fault_profile=fault, declared_modality=modality
    )
    app = build_graph(InMemorySaver())
    config = {"configurable": {"thread_id": state["thread_id"]}}
    result = app.invoke(state, config=config)
    return app, config, state, result


def test_happy_path_interrupt_approval_and_idempotent_resume(clean_fixture: Path) -> None:
    app, config, _state, paused = start(clean_fixture)
    assert paused["__interrupt__"][0].value["type"] == "HUMAN_APPROVAL_REQUIRED"
    assert paused["quality_status"] == "PASS"
    resumed = app.invoke(
        Command(
            resume={"decision": "APPROVE", "reviewer_display_name": "Demo Reviewer", "note": ""}
        ),
        config=config,
    )
    assert resumed["status"] == "APPROVED_DRAFT_EXPORTED"
    exports = resumed["export_manifest"]["hashes"]
    again = app.invoke(
        Command(
            resume={"decision": "APPROVE", "reviewer_display_name": "Demo Reviewer", "note": ""}
        ),
        config=config,
    )
    assert again["export_manifest"]["hashes"] == exports
    root = Settings.from_env().data_root
    manifest = root / "runs" / _state["run_id"] / "run_manifest.json"
    assert manifest.is_file()
    assert _state["run_id"] in manifest.read_text()
    logs = (root / "logs" / "audit.jsonl").read_text()
    assert _state["run_id"] in logs
    assert '"inference_mode":"MOCK"' in logs


def test_rejection_has_no_export(clean_fixture: Path) -> None:
    app, config, _state, _paused = start(clean_fixture)
    result = app.invoke(
        Command(
            resume={
                "decision": "REJECT",
                "reviewer_display_name": "Demo Reviewer",
                "note": "Synthetic rejection",
            }
        ),
        config=config,
    )
    assert result["status"] == "HUMAN_REJECTED"
    assert result["export_manifest"] is None


@pytest.mark.parametrize(
    "fault",
    ["grounding_fail_once", "quality_fail_once", "malformed_draft_once", "contract_fail_once"],
)
def test_one_failure_recovers_with_bounded_regeneration(clean_fixture: Path, fault: str) -> None:
    *_unused, result = start(clean_fixture, fault)
    assert result["attempt"] == (1 if fault == "malformed_draft_once" else 2)
    assert result["grounding_status"] == "PASS"
    assert result["quality_status"] == "PASS"
    assert "__interrupt__" in result


@pytest.mark.parametrize("fault", ["grounding_fail_always", "quality_fail_always"])
def test_persistent_gate_failure_exhausts_without_export(clean_fixture: Path, fault: str) -> None:
    *_, result = start(clean_fixture, fault)
    assert result["status"] == "NEEDS_HUMAN_REVIEW"
    assert result["attempt"] == 2
    assert result["export_manifest"] is None


def test_malformed_always_terminates_closed(clean_fixture: Path) -> None:
    *_, result = start(clean_fixture, "malformed_draft_always")
    assert result["status"] == "MODEL_OUTPUT_INVALID"
    assert result["attempt"] == 1
    assert result["export_manifest"] is None


def test_phi_block_has_zero_model_calls(fixture_dir: Path) -> None:
    *_, state, result = start(fixture_dir / "chest_unexpected_text.png")
    assert result["status"] == "QUARANTINED"
    assert result["model_calls"] == 0
    assert result["attempt"] == 0
    audit = AuditDB(Settings.from_env().data_root / "nt_imaging.sqlite3")
    assert audit.model_call_count(state["run_id"]) == 0


@pytest.mark.parametrize("name", ["unsupported_ct.dcm", "multiframe.dcm"])
def test_unsupported_dicom_never_reaches_draft(fixture_dir: Path, name: str) -> None:
    *_, result = start(fixture_dir / name, modality=None)
    assert result["status"] in {"NEEDS_HUMAN_REVIEW", "QUARANTINED"}
    assert result["attempt"] == 0
    assert result["model_calls"] == 0


@pytest.mark.parametrize("fault", ["model_timeout", "model_unavailable"])
def test_provider_failure_is_safe(clean_fixture: Path, fault: str) -> None:
    *_, result = start(clean_fixture, fault)
    assert result["status"] == "FAILED"
    assert result["export_manifest"] is None


def test_same_input_twice_creates_independent_runs(clean_fixture: Path) -> None:
    *_, first_state, first = start(clean_fixture)
    *_, second_state, second = start(clean_fixture)
    assert first_state["run_id"] != second_state["run_id"]
    assert first_state["artifact_id"] != second_state["artifact_id"]
    assert first["source_sha256"] == second["source_sha256"]
