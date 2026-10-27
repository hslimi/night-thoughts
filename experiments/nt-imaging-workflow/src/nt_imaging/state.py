from __future__ import annotations

import uuid
from typing import Any, Literal, TypedDict, cast


class AgentState(TypedDict, total=False):
    run_id: str
    thread_id: str
    artifact_id: str
    workflow_version: str
    inference_mode: Literal["REAL", "MOCK"]
    fault_profile: str | None
    demonstration_scenario: str
    status: str
    error: dict[str, Any] | None
    source_path: str
    declared_modality: str | None
    synthetic_or_authorized: bool
    source_sha256: str
    sanitized_sha256: str | None
    source_format: str
    source_size_bytes: int
    phi_status: str
    phi_reasons: list[str]
    phi_receipt_id: str | None
    modality: str | None
    modality_source: str | None
    modality_status: str
    modality_reason: str | None
    sanitized_artifact_id: str
    readiness_status: str
    readiness_receipt_id: str | None
    prepared_artifact_id: str | None
    prepared_sha256: str | None
    display_thumbnail_id: str | None
    preparation_policy_version: str
    preparation_operations: list[str]
    preparation_metrics: dict[str, Any]
    preparation_warnings: list[str]
    derived_phi_status: str
    prompt_version: str
    policy_version: str
    vision_model_id: str | None
    text_model_id: str | None
    attempt: int
    revision: int
    max_revisions: int
    max_attempts: int
    max_total_model_calls: int
    model_calls: int
    draft: dict[str, Any] | None
    contract_status: str
    grounding_status: str
    quality_status: str
    review_issues: list[dict[str, Any]]
    human_decision: dict[str, Any] | None
    export_manifest: dict[str, Any] | None


def initial_state(
    source_path: str,
    *,
    inference_mode: str,
    workflow_version: str = "nt-cxr-draft-v1",
    max_attempts: int = 2,
    max_total_model_calls: int = 8,
    fault_profile: str | None = None,
    declared_modality: str | None = None,
    synthetic_or_authorized: bool = True,
    vision_model_id: str | None = None,
    text_model_id: str | None = None,
) -> AgentState:
    run_id = str(uuid.uuid4())
    return AgentState(
        run_id=run_id,
        thread_id=run_id,
        artifact_id=uuid.uuid4().hex,
        workflow_version=workflow_version,
        inference_mode=cast(Literal["REAL", "MOCK"], inference_mode),
        fault_profile=fault_profile,
        status="RECEIVED",
        error=None,
        source_path=source_path,
        declared_modality=declared_modality,
        synthetic_or_authorized=synthetic_or_authorized,
        source_sha256="",
        sanitized_sha256=None,
        source_format="",
        source_size_bytes=0,
        phi_status="PENDING",
        phi_reasons=[],
        phi_receipt_id=None,
        modality=None,
        modality_source=None,
        modality_status="PENDING",
        modality_reason=None,
        sanitized_artifact_id="",
        readiness_status="PENDING",
        readiness_receipt_id=None,
        prepared_artifact_id=None,
        prepared_sha256=None,
        display_thumbnail_id=None,
        preparation_policy_version="cxr-preparation-v2",
        preparation_operations=[],
        preparation_metrics={},
        preparation_warnings=[],
        derived_phi_status="PENDING",
        prompt_version="cxr-draft-v1",
        policy_version="cxr-quality-v1",
        vision_model_id=vision_model_id,
        text_model_id=text_model_id,
        attempt=0,
        revision=0,
        max_revisions=2,
        max_attempts=max_attempts,
        max_total_model_calls=max_total_model_calls,
        model_calls=0,
        draft=None,
        contract_status="PENDING",
        grounding_status="PENDING",
        quality_status="PENDING",
        review_issues=[],
        human_decision=None,
        export_manifest=None,
    )
