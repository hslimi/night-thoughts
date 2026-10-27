from __future__ import annotations

from typing import Any

from langgraph.types import interrupt
from pydantic import ValidationError

from ..audit import AuditDB, utc_now
from ..config import Settings
from ..constants import DISCLAIMER
from ..schemas import HumanDecision, safe_error


def human_approval(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    response = interrupt(
        {
            "type": "HUMAN_APPROVAL_REQUIRED",
            "run_id": state["run_id"],
            "inference_mode": state["inference_mode"],
            "draft": state["draft"],
            "contract_status": state["contract_status"],
            "grounding_status": state["grounding_status"],
            "quality_status": state["quality_status"],
            "attempt": state["attempt"],
            "revision": state.get("revision", 0),
            "vision_model_id": state.get("vision_model_id"),
            "text_model_id": state.get("text_model_id"),
            "prompt_version": state["prompt_version"],
            "policy_version": state["policy_version"],
            "disclaimer": DISCLAIMER,
            "instructions": "Approve demonstration-draft export, reject with a note, or request bounded changes with a note. This is not clinical sign-off.",
            "response_schema": HumanDecision.model_json_schema(),
        }
    )
    try:
        decision = HumanDecision.model_validate(response)
    except ValidationError:
        return {
            "status": "NEEDS_HUMAN_REVIEW",
            "error": safe_error(
                "HUMAN_DECISION_INVALID", "A valid typed doctor decision is required"
            ),
        }
    revision = state.get("revision", 0)
    record = {
        **decision.model_dump(),
        "timestamp": utc_now(),
        "run_id": state["run_id"],
        "revision": revision,
    }
    resulting_state = "AWAITING_HUMAN_APPROVAL"
    audit = AuditDB(settings.data_root / "nt_imaging.sqlite3")
    if decision.decision == "APPROVE" and not all(
        state.get(key) == "PASS"
        for key in ("contract_status", "grounding_status", "quality_status")
    ):
        resulting_state = "NEEDS_HUMAN_REVIEW"
    elif decision.decision == "REQUEST_CHANGES":
        resulting_state = (
            "REVISION_REQUESTED"
            if revision < state.get("max_revisions", 2)
            else "NEEDS_HUMAN_REVIEW"
        )
    with audit.connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO human_decisions VALUES (?,?,?,?,?)",
            (
                state["run_id"],
                decision.decision,
                decision.reviewer_display_name,
                decision.note,
                record["timestamp"],
            ),
        )
        db.execute(
            "INSERT INTO human_decision_history VALUES (?,?,?,?,?,?,?,?)",
            (
                record["timestamp"] + state["run_id"],
                state["run_id"],
                decision.decision,
                decision.reviewer_display_name,
                decision.note,
                revision,
                resulting_state,
                record["timestamp"],
            ),
        )
    audit.event(
        state["run_id"],
        "human_approval",
        f"HUMAN_{decision.decision}",
        workflow_version=state["workflow_version"],
        attempt=state["attempt"],
        metadata={
            "decision": decision.decision,
            "revision": revision,
            "resulting_state": resulting_state,
        },
    )
    if resulting_state == "NEEDS_HUMAN_REVIEW":
        return {
            "status": resulting_state,
            "human_decision": record,
            "error": safe_error(
                "APPROVAL_GATE_MISMATCH"
                if decision.decision == "APPROVE"
                else "REVISION_EXHAUSTED",
                "The requested decision cannot proceed within workflow policy",
            ),
        }
    if resulting_state == "REVISION_REQUESTED":
        issue = {
            "code": "DOCTOR_REVISION_REQUEST",
            "severity": "NON_BLOCKING",
            "message": decision.note,
            "stage": "DOCTOR_REVISION",
            "attempt": state["attempt"],
            "revision": revision + 1,
        }
        return {
            "status": resulting_state,
            "human_decision": record,
            "attempt": 0,
            "revision": revision + 1,
            "draft": None,
            "contract_status": "PENDING",
            "grounding_status": "PENDING",
            "quality_status": "PENDING",
            "review_issues": [*state.get("review_issues", []), issue][-40:],
            "error": None,
        }
    return {"human_decision": record, "status": resulting_state, "error": None}
