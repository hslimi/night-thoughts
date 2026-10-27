from __future__ import annotations

from typing import Any


def after_ingest(state: dict[str, Any]) -> str:
    if state.get("status") == "INGESTED":
        return "phi"
    return "quarantine" if state.get("status") == "QUARANTINED" else "review"


def after_phi(state: dict[str, Any]) -> str:
    return "modality" if state.get("phi_status") == "CLEAR" else "quarantine"


def after_modality(state: dict[str, Any]) -> str:
    return "readiness" if state.get("modality_status") == "SUPPORTED" else "review"


def after_readiness(state: dict[str, Any]) -> str:
    return (
        "safety"
        if state.get("readiness_status") == "READY" and state.get("prepared_artifact_id")
        else "review"
    )


def after_safety(state: dict[str, Any]) -> str:
    return (
        "draft"
        if state.get("derived_phi_status") == "CLEAR" and state.get("prepared_artifact_id")
        else "review"
    )


def after_draft(state: dict[str, Any]) -> str:
    if state.get("status") == "DRAFTING" and state.get("draft"):
        return "contract"
    return "review" if state.get("status") == "NEEDS_HUMAN_REVIEW" else "failed"


def after_contract(state: dict[str, Any]) -> str:
    if state.get("contract_status") == "PASS":
        return "grounding"
    return "draft" if state.get("attempt", 0) < state.get("max_attempts", 0) else "review"


def after_grounding(state: dict[str, Any]) -> str:
    if state.get("grounding_status") == "PASS":
        return "quality"
    return "draft" if state.get("attempt", 0) < state.get("max_attempts", 0) else "review"


def after_quality(state: dict[str, Any]) -> str:
    if (
        state.get("quality_status") == "PASS"
        and state.get("grounding_status") == "PASS"
        and state.get("contract_status") == "PASS"
    ):
        return "approval"
    return "draft" if state.get("attempt", 0) < state.get("max_attempts", 0) else "review"


def after_approval(state: dict[str, Any]) -> str:
    decision = state.get("human_decision") or {}
    if decision.get("decision") == "APPROVE" and state.get("status") == "AWAITING_HUMAN_APPROVAL":
        return "export"
    if (
        decision.get("decision") == "REQUEST_CHANGES"
        and state.get("status") == "REVISION_REQUESTED"
    ):
        return "draft"
    return "rejected" if decision.get("decision") == "REJECT" else "review"
