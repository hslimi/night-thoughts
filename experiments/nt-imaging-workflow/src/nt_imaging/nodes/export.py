from __future__ import annotations

import hashlib
import html
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, cast

from ..artifacts import sha256_bytes, sha256_file
from ..audit import AuditDB, utc_now
from ..config import Settings
from ..constants import DISCLAIMER, MOCK_LABEL
from ..schemas import HumanDecision, ImagingDraft


class ExportSafetyError(RuntimeError):
    pass


def export_approved_draft(state: dict[str, Any], settings: Settings) -> dict[str, Any]:
    _assert_exportable(state)
    _assert_not_cancelled(state, settings)
    draft = ImagingDraft.model_validate(state["draft"])
    decision = HumanDecision.model_validate(
        {
            k: v
            for k, v in state["human_decision"].items()
            if k in {"decision", "reviewer_display_name", "note"}
        }
    )
    draft_sha = sha256_bytes(
        json.dumps(draft.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    )
    idempotency_key = hashlib.sha256(
        f"{state['run_id']}:{draft_sha}:{state['workflow_version']}".encode()
    ).hexdigest()
    created_at = utc_now()
    report = {
        "run_id": state["run_id"],
        "draft": draft.model_dump(mode="json"),
        "provenance": {
            "workflow_version": state["workflow_version"],
            "prompt_version": state["prompt_version"],
            "policy_version": state["policy_version"],
            "vision_model_id": state.get("vision_model_id"),
            "text_model_id": state.get("text_model_id"),
            "inference_mode": state["inference_mode"],
            "source_sha256": state["source_sha256"],
            "prepared_sha256": state["prepared_sha256"],
            "readiness_receipt_id": state.get("readiness_receipt_id"),
            "preparation_policy_version": state.get("preparation_policy_version"),
            "preparation_operations": state.get("preparation_operations", []),
            "preparation_metrics": state.get("preparation_metrics", {}),
            "preparation_warnings": state.get("preparation_warnings", []),
            "attempt": state["attempt"],
            "human_decision": decision.model_dump(),
            "created_at": created_at,
            "disclaimer": DISCLAIMER,
            "mock_label": MOCK_LABEL if state["inference_mode"] == "MOCK" else None,
        },
    }
    content_sha = sha256_bytes(
        json.dumps(_signature(report), sort_keys=True, separators=(",", ":")).encode()
    )
    audit = AuditDB(settings.data_root / "nt_imaging.sqlite3")
    existing = _existing(audit, idempotency_key)
    if existing:
        if existing["content_sha256"] != content_sha:
            raise ExportSafetyError("Export idempotency key is associated with different content")
        manifest = json.loads(existing["manifest"])
        _verify_existing_files(settings.data_root, manifest)
        return {"status": "APPROVED_DRAFT_EXPORTED", "export_manifest": manifest, "error": None}
    filenames = {
        "report_json": f"report_{state['run_id']}.json",
        "report_markdown": f"report_{state['run_id']}.md",
        "manifest": f"manifest_{state['run_id']}.json",
    }
    manifest = {
        "idempotency_key": idempotency_key,
        "run_id": state["run_id"],
        "created_at": created_at,
        "workflow_version": state["workflow_version"],
        "prompt_version": state["prompt_version"],
        "policy_version": state["policy_version"],
        "inference_mode": state["inference_mode"],
        "fault_profile": state.get("fault_profile"),
        "demonstration_scenario": state.get("demonstration_scenario"),
        "derived_phi_status": state.get("derived_phi_status"),
        "vision_model_id": state.get("vision_model_id"),
        "text_model_id": state.get("text_model_id"),
        "source_sha256": state["source_sha256"],
        "prepared_sha256": state["prepared_sha256"],
        "readiness_receipt_id": state.get("readiness_receipt_id"),
        "preparation_policy_version": state.get("preparation_policy_version"),
        "preparation_operations": state.get("preparation_operations", []),
        "preparation_metrics": state.get("preparation_metrics", {}),
        "preparation_warnings": state.get("preparation_warnings", []),
        "draft_sha256": draft_sha,
        "files": filenames,
        "hashes": {},
        "disclaimer": DISCLAIMER,
        "mock_label": MOCK_LABEL if state["inference_mode"] == "MOCK" else None,
    }
    manifest["hashes"][filenames["report_json"]] = sha256_bytes(
        (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    )
    manifest["hashes"][filenames["report_markdown"]] = sha256_bytes(_markdown(report).encode())
    _atomic_export(settings.data_root / "exports", filenames, report, manifest)
    try:
        with audit.connect() as db:
            db.execute(
                "INSERT INTO exports VALUES (?,?,?,?,?)",
                (idempotency_key, state["run_id"], content_sha, json.dumps(manifest), created_at),
            )
    except sqlite3.IntegrityError as exc:
        raise ExportSafetyError(
            "Concurrent export with the same idempotency key was detected"
        ) from exc
    audit.update_status(state["run_id"], "APPROVED_DRAFT_EXPORTED")
    audit.event(
        state["run_id"],
        "export_approved_draft",
        "APPROVED_DRAFT_EXPORTED",
        workflow_version=state["workflow_version"],
        attempt=state["attempt"],
        metadata={"idempotency_key": idempotency_key, "hashes": manifest["hashes"]},
    )
    return {"status": "APPROVED_DRAFT_EXPORTED", "export_manifest": manifest, "error": None}


def _assert_exportable(state: dict[str, Any]) -> None:
    required = {
        "phi_status": "CLEAR",
        "modality_status": "SUPPORTED",
        "contract_status": "PASS",
        "grounding_status": "PASS",
        "quality_status": "PASS",
        "readiness_status": "READY",
        "derived_phi_status": "CLEAR",
    }
    if any(state.get(key) != value for key, value in required.items()):
        raise ExportSafetyError("Export blocked: every required gate must pass")
    if state.get("status") in {
        "HUMAN_REJECTED",
        "NEEDS_HUMAN_REVIEW",
        "QUARANTINED",
        "IMAGE_PREPARATION_FAILED",
        "FAILED",
        "MODEL_OUTPUT_INVALID",
    }:
        raise ExportSafetyError("Export blocked by terminal workflow status")
    if state.get("attempt", 0) < 1 or state["attempt"] > state["max_attempts"]:
        raise ExportSafetyError("Export blocked: attempt budget is invalid")
    decision = HumanDecision.model_validate(
        {
            k: v
            for k, v in (state.get("human_decision") or {}).items()
            if k in {"decision", "reviewer_display_name", "note"}
        }
    )
    if decision.decision != "APPROVE":
        raise ExportSafetyError("Export blocked: typed human approval is required")
    ImagingDraft.model_validate(state.get("draft"))


def _assert_not_cancelled(state: dict[str, Any], settings: Settings) -> None:
    path = settings.data_root / "controlplane.sqlite3"
    if path.exists():
        from ..controlplane.db import ControlDB

        if ControlDB(path).is_cancelled(state["run_id"]):
            raise ExportSafetyError("Export blocked: the doctor cancelled this run")


def _existing(audit: AuditDB, key: str) -> sqlite3.Row | None:
    with audit.connect() as db:
        return cast(
            sqlite3.Row | None,
            db.execute("SELECT * FROM exports WHERE idempotency_key=?", (key,)).fetchone(),
        )


def _signature(report: dict[str, Any]) -> dict[str, Any]:
    value = cast(dict[str, Any], json.loads(json.dumps(report)))
    value["provenance"]["created_at"] = ""
    value["provenance"]["human_decision"].pop("timestamp", None)
    return value


def _markdown(report: dict[str, Any]) -> str:
    draft = ImagingDraft.model_validate(report["draft"])

    def esc(value: str) -> str:
        return html.escape(value, quote=False)

    lines = ["# AI-ASSISTED DRAFT — NOT FOR CLINICAL USE", "", f"> **{DISCLAIMER}**", ""]
    if report["provenance"]["inference_mode"] == "MOCK":
        lines += [f"> **{MOCK_LABEL}**", ""]
    lines += [
        "## Technique",
        esc(draft.technique),
        "",
        "## Comparison",
        esc(draft.comparison),
        "",
        "## Findings",
        esc(draft.findings_text),
        "",
    ]
    for finding in draft.findings:
        lines.append(f"- **{esc(finding.label)} ({finding.status})**: {esc(finding.description)}")
    lines += [
        "",
        "## Impression",
        *[f"- {esc(item)}" for item in draft.impression],
        "",
        "## Limitations",
        *[f"- {esc(item)}" for item in draft.limitations],
        "",
        f"Run ID: `{report['run_id']}`",
        "",
    ]
    return "\n".join(lines)


def _atomic_export(
    root: Path, names: dict[str, str], report: dict[str, Any], manifest: dict[str, Any]
) -> None:
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    contents = {
        names["report_json"]: json.dumps(report, indent=2, sort_keys=True) + "\n",
        names["report_markdown"]: _markdown(report),
        names["manifest"]: json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    }
    temps: list[Path] = []
    try:
        for name, content in contents.items():
            temp = root / f".{name}.tmp"
            with temp.open("x", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp, 0o600)
            temps.append(temp)
        for name in contents:
            os.replace(root / f".{name}.tmp", root / name)
            temps.remove(root / f".{name}.tmp")
    finally:
        for temp in temps:
            temp.unlink(missing_ok=True)


def _verify_existing_files(root: Path, manifest: dict[str, Any]) -> None:
    for name, expected in manifest["hashes"].items():
        path = root / "exports" / Path(name).name
        if not path.is_file() or sha256_file(path) != expected:
            raise ExportSafetyError(
                "Existing idempotent export is missing or does not match its recorded hash"
            )
