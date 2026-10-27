from __future__ import annotations

from typing import Any

from ..audit import AuditDB
from ..config import Settings


def quarantine(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    return _terminal(state, settings, "QUARANTINED", "quarantine")


def needs_review(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    status = (
        "IMAGE_PREPARATION_FAILED"
        if state.get("status") == "IMAGE_PREPARATION_FAILED"
        else "NEEDS_HUMAN_REVIEW"
    )
    return _terminal(state, settings, status, "needs_review")


def fail_closed(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    status = "FAILED" if state.get("status") == "FAILED" else "MODEL_OUTPUT_INVALID"
    return _terminal(state, settings, status, "fail_closed")


def reject_draft(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    return _terminal(state, settings, "HUMAN_REJECTED", "reject_draft")


def _terminal(state: dict[str, Any], settings: Settings, status: str, node: str) -> dict[str, Any]:
    audit = AuditDB(settings.data_root / "nt_imaging.sqlite3")
    audit.update_status(state["run_id"], status)
    audit.event(
        state["run_id"],
        node,
        status,
        workflow_version=state["workflow_version"],
        attempt=state.get("attempt", 0),
    )
    return {"status": status}
