from __future__ import annotations

import shutil
import uuid

from nt_imaging.artifacts import ArtifactStore
from nt_imaging.config import Settings
from nt_imaging.constants import DRAFT_NOTICE
from nt_imaging.nodes.drafting import deterministic_contract_gate, generate_draft
from nt_imaging.state import initial_state


def draft() -> dict:
    return {
        "technique": "Synthetic",
        "comparison": "No comparison supplied",
        "findings": [
            {
                "label": "Shape",
                "status": "PRESENT",
                "anatomy": "Field",
                "description": "Shape is present.",
            }
        ],
        "findings_text": "Shape.",
        "impression": ["Demo."],
        "limitations": ["Synthetic."],
        "draft_notice": DRAFT_NOTICE,
    }


def test_placeholder_duplicate_and_contradiction_fail() -> None:
    state = initial_state("unused", inference_mode="MOCK")
    value = draft()
    value["comparison"] = "TBD"
    value["findings"].append(value["findings"][0])
    value["findings"][0]["description"] = "Shape is absent."
    result = deterministic_contract_gate({**state, "draft": value}, Settings.from_env())
    codes = {issue["code"] for issue in result["review_issues"]}
    assert result["contract_status"] == "FAIL"
    assert {"UNRESOLVED_PLACEHOLDER", "DUPLICATE_FINDING", "FINDING_STATUS_CONTRADICTION"} <= codes


def test_regeneration_resets_downstream_statuses_and_attempt(clean_fixture) -> None:
    settings = Settings.from_env()
    state = initial_state(str(clean_fixture), inference_mode="MOCK")
    prepared_id = uuid.uuid4().hex
    prepared = ArtifactStore(settings.data_root).derived_path(state["run_id"], prepared_id, ".png")
    shutil.copyfile(clean_fixture, prepared)
    state.update(
        {
            "source_path": str(clean_fixture),
            "attempt": 0,
            "draft": draft(),
            "contract_status": "PASS",
            "grounding_status": "FAIL",
            "quality_status": "PASS",
            "readiness_status": "READY",
            "derived_phi_status": "CLEAR",
            "prepared_artifact_id": prepared_id,
        }
    )
    result = generate_draft(state, Settings.from_env())
    assert result["attempt"] == 1
    assert result["grounding_status"] == "PENDING"
    assert result["quality_status"] == "PENDING"
    assert result["contract_status"] == "PENDING"
