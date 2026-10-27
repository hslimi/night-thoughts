from __future__ import annotations

import pytest
from pydantic import ValidationError

from nt_imaging.constants import DRAFT_NOTICE
from nt_imaging.routing import (
    after_approval,
    after_contract,
    after_grounding,
    after_ingest,
    after_modality,
    after_phi,
    after_quality,
)
from nt_imaging.schemas import HumanDecision, ImagingDraft, ReviewResult
from nt_imaging.state import initial_state


def valid_draft() -> dict:
    return {
        "technique": "Synthetic image",
        "comparison": "No comparison supplied",
        "findings": [
            {
                "label": "Synthetic shape",
                "status": "UNCERTAIN",
                "anatomy": "Image field",
                "description": "Artificial shape.",
            }
        ],
        "findings_text": "Artificial shape.",
        "impression": ["Synthetic demonstration."],
        "limitations": ["Not clinically evaluated."],
        "draft_notice": DRAFT_NOTICE,
    }


def test_initial_state_has_unique_opaque_ids() -> None:
    first = initial_state("/tmp/ignored", inference_mode="MOCK")
    second = initial_state("/tmp/ignored", inference_mode="MOCK")
    assert first["run_id"] == first["thread_id"]
    assert first["run_id"] != second["run_id"]
    assert first["artifact_id"] != second["artifact_id"]
    assert first["attempt"] == 0


def test_all_conditional_routes() -> None:
    assert after_ingest({"status": "INGESTED"}) == "phi"
    assert after_ingest({"status": "QUARANTINED"}) == "quarantine"
    assert after_ingest({"status": "FAILED"}) == "review"
    assert after_phi({"phi_status": "CLEAR"}) == "modality"
    assert after_phi({"phi_status": "BLOCKED"}) == "quarantine"
    assert after_modality({"modality_status": "SUPPORTED"}) == "readiness"
    assert after_modality({"modality_status": "UNKNOWN"}) == "review"
    assert after_contract({"contract_status": "PASS"}) == "grounding"
    assert after_contract({"contract_status": "FAIL", "attempt": 1, "max_attempts": 2}) == "draft"
    assert after_contract({"contract_status": "FAIL", "attempt": 2, "max_attempts": 2}) == "review"
    assert after_grounding({"grounding_status": "PASS"}) == "quality"
    assert (
        after_grounding({"grounding_status": "FAIL", "attempt": 2, "max_attempts": 2}) == "review"
    )
    assert (
        after_quality(
            {"quality_status": "PASS", "grounding_status": "PASS", "contract_status": "PASS"}
        )
        == "approval"
    )
    assert (
        after_quality(
            {"quality_status": "PASS", "grounding_status": "FAIL", "attempt": 2, "max_attempts": 2}
        )
        == "review"
    )
    assert after_approval({"human_decision": {"decision": "REJECT"}}) == "rejected"


def test_grounding_failure_cannot_route_to_quality() -> None:
    assert after_grounding({"grounding_status": "FAIL", "attempt": 1, "max_attempts": 2}) == "draft"
    assert (
        after_quality(
            {
                "quality_status": "PASS",
                "grounding_status": "FAIL",
                "contract_status": "PASS",
                "attempt": 1,
                "max_attempts": 2,
            }
        )
        == "draft"
    )


def test_prose_is_not_a_verdict() -> None:
    with pytest.raises(ValidationError):
        ReviewResult.model_validate({"verdict": "not PASS", "issues": []})
    with pytest.raises(ValidationError):
        ReviewResult.model_validate(
            {
                "verdict": "PASS",
                "issues": [{"code": "X", "severity": "BLOCKING", "message": "failure"}],
            }
        )


def test_unknown_enums_and_unknown_fields_fail() -> None:
    draft = valid_draft()
    draft["findings"][0]["status"] = "MAYBE"
    with pytest.raises(ValidationError):
        ImagingDraft.model_validate(draft)
    with pytest.raises(ValidationError):
        ImagingDraft.model_validate({**valid_draft(), "unexpected": True})


def test_rejection_requires_note_and_name() -> None:
    with pytest.raises(ValidationError):
        HumanDecision(decision="REJECT", reviewer_display_name="Reviewer")
    with pytest.raises(ValidationError):
        HumanDecision(decision="APPROVE", reviewer_display_name="")
    assert (
        HumanDecision(decision="APPROVE", reviewer_display_name="Demo Reviewer").decision
        == "APPROVE"
    )
