from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..artifacts import ArtifactStore, sha256_bytes
from ..audit import AuditDB
from ..config import Settings
from ..constants import DRAFT_NOTICE
from ..inference import get_provider
from ..inference.structured import StructuredOutputError, parse_structured
from ..schemas import ImagingDraft, contains_placeholder, safe_error

_PROVIDER_CACHE: dict[str, Any] = {}


def provider_for(state: dict[str, Any], settings: Settings) -> Any:
    run_id = state["run_id"]
    if run_id not in _PROVIDER_CACHE:
        if len(_PROVIDER_CACHE) >= 16:
            _PROVIDER_CACHE.pop(next(iter(_PROVIDER_CACHE)))
        _PROVIDER_CACHE[run_id] = get_provider(settings, state.get("fault_profile"))
    return _PROVIDER_CACHE[run_id]


def _concise_prior_issues(issues: list[dict[str, Any]]) -> list[dict[str, str]]:
    doctor = [issue for issue in issues if issue.get("stage") == "DOCTOR_REVISION"]
    selected = [*doctor[-1:], *issues[-2:]] if doctor else issues[-2:]
    return [
        {
            "code": str(issue.get("code", "REVIEW_ISSUE")),
            "message": str(issue.get("message", ""))[:400],
        }
        for issue in selected
    ]


def generate_draft(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    attempt = state["attempt"] + 1
    reset = {
        "attempt": attempt,
        "draft": None,
        "contract_status": "PENDING",
        "grounding_status": "PENDING",
        "quality_status": "PENDING",
        "status": "DRAFTING",
        "human_decision": None,
        "export_manifest": None,
        "error": None,
    }
    if attempt > state["max_attempts"]:
        return {
            **reset,
            "status": "NEEDS_HUMAN_REVIEW",
            "error": safe_error("RETRY_EXHAUSTED", "Draft retry budget exhausted"),
        }
    if state["model_calls"] >= state["max_total_model_calls"]:
        return {
            **reset,
            "status": "NEEDS_HUMAN_REVIEW",
            "error": safe_error("MODEL_CALL_BUDGET_EXHAUSTED", "Model-call budget exhausted"),
        }
    if (
        state.get("readiness_status") != "READY"
        or state.get("derived_phi_status") != "CLEAR"
        or not state.get("prepared_artifact_id")
    ):
        return {
            **reset,
            "status": "IMAGE_PREPARATION_FAILED",
            "error": safe_error(
                "READINESS_PREREQUISITE", "A safe prepared derivative is required before drafting"
            ),
        }
    provider = provider_for(state, settings)
    prompt = (Path(__file__).resolve().parents[3] / "prompts" / "cxr_draft_v1.txt").read_text()
    calls = 0
    audit = AuditDB(settings.data_root / "nt_imaging.sqlite3")
    prior_issues = _concise_prior_issues(state.get("review_issues", []))
    try:
        calls += 1
        response = provider.generate_draft(
            ArtifactStore(settings.data_root).derived_path(
                state["run_id"], state["prepared_artifact_id"], ".png"
            ),
            prompt,
            prior_issues,
        )
        audit.model_call(
            state["run_id"],
            "DRAFT",
            response.model_id,
            response.latency_ms,
            "SUCCESS",
            sha256_bytes(response.raw.encode()),
        )
        try:
            draft = parse_structured(response.raw, ImagingDraft)
        except StructuredOutputError as validation_error:
            if calls > 1 or state["model_calls"] + calls >= state["max_total_model_calls"]:
                raise
            calls += 1
            repaired = provider.repair_draft(response.raw, str(validation_error))
            audit.model_call(
                state["run_id"],
                "DRAFT_SYNTAX_REPAIR",
                repaired.model_id,
                repaired.latency_ms,
                "SUCCESS",
                sha256_bytes(repaired.raw.encode()),
            )
            draft = parse_structured(repaired.raw, ImagingDraft)
    except (StructuredOutputError, TimeoutError, RuntimeError, OSError, ValueError) as exc:
        code = (
            "MODEL_TIMEOUT"
            if isinstance(exc, TimeoutError)
            else "MODEL_OUTPUT_INVALID"
            if isinstance(exc, StructuredOutputError)
            else "MODEL_UNAVAILABLE"
        )
        audit.event(
            state["run_id"],
            "generate_draft",
            "DRAFT_FAILED",
            workflow_version=state["workflow_version"],
            attempt=attempt,
            reason_codes=[code],
        )
        return {
            **reset,
            "model_calls": state["model_calls"] + calls,
            "status": "FAILED" if code != "MODEL_OUTPUT_INVALID" else "MODEL_OUTPUT_INVALID",
            "error": safe_error(
                code,
                "Draft generation failed closed",
                retryable=code in {"MODEL_TIMEOUT", "MODEL_UNAVAILABLE"},
            ),
        }
    audit.event(
        state["run_id"],
        "generate_draft",
        "DRAFT_GENERATED",
        workflow_version=state["workflow_version"],
        attempt=attempt,
        metadata={
            "output_sha256": sha256_bytes(draft.model_dump_json().encode()),
            "inference_mode": state["inference_mode"],
        },
    )
    return {
        **reset,
        "model_calls": state["model_calls"] + calls,
        "draft": draft.model_dump(mode="json"),
        "status": "DRAFTING",
    }


def deterministic_contract_gate(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    try:
        draft = ImagingDraft.model_validate(state.get("draft"))
    except ValidationError:
        return {
            "contract_status": "FAIL",
            "review_issues": _issues(
                state,
                [
                    {
                        "code": "SCHEMA_INVALID",
                        "message": "Draft schema is invalid",
                        "stage": "CONTRACT",
                    }
                ],
            ),
        }
    if not draft.findings or not draft.impression or not draft.limitations:
        issues.append(
            {"code": "REQUIRED_SECTION_EMPTY", "message": "Required report sections are empty"}
        )
    if draft.draft_notice != DRAFT_NOTICE:
        issues.append(
            {"code": "DRAFT_NOTICE_INVALID", "message": "Required draft notice is missing"}
        )
    strings = [
        draft.technique,
        draft.comparison,
        draft.findings_text,
        *draft.impression,
        *draft.limitations,
    ]
    strings += [
        item
        for finding in draft.findings
        for item in (finding.label, finding.description, finding.anatomy or "")
    ]
    if any(contains_placeholder(value) for value in strings):
        issues.append(
            {"code": "UNRESOLVED_PLACEHOLDER", "message": "Unresolved placeholders are prohibited"}
        )
    seen: set[str] = set()
    for finding in draft.findings:
        identity = re.sub(
            r"\W+", " ", f"{finding.label} {finding.anatomy or ''} {finding.description}".lower()
        ).strip()
        if identity in seen:
            issues.append(
                {
                    "code": "DUPLICATE_FINDING",
                    "message": "An obvious duplicate finding was detected",
                }
            )
        seen.add(identity)
        lower = finding.description.lower()
        if finding.status == "ABSENT" and re.search(
            r"\b(?:is present|are present|clearly seen)\b", lower
        ):
            issues.append(
                {
                    "code": "FINDING_STATUS_CONTRADICTION",
                    "message": "Finding status contradicts its description",
                }
            )
        if finding.status == "PRESENT" and re.search(
            r"\b(?:is absent|are absent|no evidence of)\b", lower
        ):
            issues.append(
                {
                    "code": "FINDING_STATUS_CONTRADICTION",
                    "message": "Finding status contradicts its description",
                }
            )
    if any(
        re.search(
            r"\b(?:patient was discharged|autonomously signed|treatment was administered)\b",
            value,
            re.IGNORECASE,
        )
        for value in strings
    ):
        issues.append(
            {
                "code": "AUTONOMOUS_CLINICAL_ACTION",
                "message": "Completed autonomous clinical actions are prohibited",
            }
        )
    status = "FAIL" if issues else "PASS"
    tagged = [
        {**issue, "severity": "BLOCKING", "stage": "CONTRACT", "attempt": state["attempt"]}
        for issue in issues
    ]
    AuditDB(settings.data_root / "nt_imaging.sqlite3").event(
        state["run_id"],
        "deterministic_contract_gate",
        f"CONTRACT_{status}",
        workflow_version=state["workflow_version"],
        attempt=state["attempt"],
        reason_codes=[i["code"] for i in issues],
    )
    return {"contract_status": status, "review_issues": _issues(state, tagged)}


def _issues(state: dict[str, Any], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [*state.get("review_issues", []), *new][-40:]
