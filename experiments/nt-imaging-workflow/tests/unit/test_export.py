from __future__ import annotations

import json
import os

import pytest

from nt_imaging.audit import AuditDB
from nt_imaging.config import Settings
from nt_imaging.constants import DRAFT_NOTICE
from nt_imaging.nodes.export import ExportSafetyError, export_approved_draft
from nt_imaging.state import initial_state


def export_state() -> dict:
    state = initial_state("/unused", inference_mode="MOCK")
    state.update(
        {
            "status": "AWAITING_HUMAN_APPROVAL",
            "phi_status": "CLEAR",
            "modality_status": "SUPPORTED",
            "contract_status": "PASS",
            "grounding_status": "PASS",
            "quality_status": "PASS",
            "attempt": 1,
            "source_sha256": "a" * 64,
            "prepared_sha256": "b" * 64,
            "readiness_status": "READY",
            "derived_phi_status": "CLEAR",
            "draft": {
                "technique": "Synthetic",
                "comparison": "No comparison supplied",
                "findings": [
                    {
                        "label": "Shape",
                        "status": "UNCERTAIN",
                        "anatomy": "Field",
                        "description": "Artificial.",
                    }
                ],
                "findings_text": "Artificial.",
                "impression": ["Demonstration."],
                "limitations": ["Synthetic only."],
                "draft_notice": DRAFT_NOTICE,
            },
            "human_decision": {
                "decision": "APPROVE",
                "reviewer_display_name": "Demo Reviewer",
                "note": "",
            },
        }
    )
    return state


def settings() -> Settings:
    return Settings.from_env()


def prepare(state: dict) -> None:
    AuditDB(settings().data_root / "nt_imaging.sqlite3").start_run(state)


def test_export_is_atomic_idempotent_and_hashed() -> None:
    state = export_state()
    prepare(state)
    first = export_approved_draft(state, settings())
    second = export_approved_draft(state, settings())
    assert first["export_manifest"]["hashes"] == second["export_manifest"]["hashes"]
    assert len(list((settings().data_root / "exports").glob(f"*{state['run_id']}*"))) == 3
    assert len(state["source_sha256"]) == 64
    audit = AuditDB(settings().data_root / "nt_imaging.sqlite3")
    with audit.connect() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM exports WHERE run_id=?", (state["run_id"],)
            ).fetchone()[0]
            == 1
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='APPROVED_DRAFT_EXPORTED'",
                (state["run_id"],),
            ).fetchone()[0]
            == 1
        )


@pytest.mark.parametrize(
    "gate",
    [
        "phi_status",
        "modality_status",
        "readiness_status",
        "derived_phi_status",
        "contract_status",
        "grounding_status",
        "quality_status",
    ],
)
def test_failed_gate_never_exports(gate: str) -> None:
    state = export_state()
    state[gate] = "FAIL" if gate not in {"phi_status", "modality_status"} else "BLOCKED"
    before = set((settings().data_root / "exports").glob(f"*{state['run_id']}*"))
    with pytest.raises(ExportSafetyError):
        export_approved_draft(state, settings())
    assert not set((settings().data_root / "exports").glob(f"*{state['run_id']}*")) - before


def test_rejection_and_exhaustion_never_export() -> None:
    state = export_state()
    state["human_decision"] = {
        "decision": "REJECT",
        "reviewer_display_name": "Reviewer",
        "note": "No",
    }
    with pytest.raises(ExportSafetyError):
        export_approved_draft(state, settings())
    state = export_state()
    state["attempt"] = 3
    with pytest.raises(ExportSafetyError):
        export_approved_draft(state, settings())


def test_export_detects_idempotency_mismatch() -> None:
    state = export_state()
    prepare(state)
    export_approved_draft(state, settings())
    state["human_decision"]["note"] = "Changed content under the same draft idempotency key"
    with pytest.raises(ExportSafetyError):
        export_approved_draft(state, settings())


def test_atomic_failure_cleans_temporary_files(monkeypatch: pytest.MonkeyPatch) -> None:
    state = export_state()
    prepare(state)
    monkeypatch.setattr(os, "replace", lambda *args: (_ for _ in ()).throw(OSError("simulated")))
    with pytest.raises(OSError):
        export_approved_draft(state, settings())
    root = settings().data_root / "exports"
    assert not list(root.glob("*.tmp"))


def test_manifest_excludes_secrets_and_phi_values() -> None:
    state = export_state()
    prepare(state)
    result = export_approved_draft(state, settings())
    serialized = json.dumps(result["export_manifest"])
    assert "api_key" not in serialized
    assert "SYNTHETIC^PERSON" not in serialized
