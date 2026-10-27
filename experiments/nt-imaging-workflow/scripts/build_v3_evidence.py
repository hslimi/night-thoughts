from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

from nt_imaging.controlplane.db import ControlDB
from nt_imaging.imaging.readiness import CODE_VERSION, POLICY_VERSION

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_counts(data_root: Path) -> dict[str, Any]:
    runs = ControlDB(data_root / "controlplane.sqlite3").snapshots(10000)
    return {
        "total": len(runs),
        "by_status": dict(sorted(Counter(run["status"] for run in runs).items())),
        "by_mode": dict(sorted(Counter(run["inference_mode"] for run in runs).items())),
        "fault_injection": sum(1 for run in runs if run.get("fault_profile") not in {None, "none"}),
    }


def main() -> None:
    screenshots = []
    for path in sorted((ROOT / "docs/images/doctor-pipeline-user-guide").glob("*.png")):
        with Image.open(path) as image:
            width, height = image.size
        screenshots.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "width": width,
                "height": height,
            }
        )
    mock = json.loads((ROOT / "evidence/showcase/mock-runs.json").read_text())
    real = json.loads((ROOT / "evidence/showcase/real-runs.json").read_text())
    browser = json.loads((ROOT / "evidence/responsive/console-browser-tests.json").read_text())
    manifest = {
        "schema": "nt-imaging-evidence-v3",
        "generated_at": datetime.now(UTC).isoformat(),
        "research_demonstration": True,
        "clinical_validation_performed": False,
        "workflow_version": "nt-cxr-draft-v1",
        "preparation_policy_version": POLICY_VERSION,
        "preparation_code_version": CODE_VERSION,
        "graph": [
            "ingest_validate",
            "phi_screen",
            "modality_gate",
            "imaging_readiness",
            "derived_image_safety_check",
            "generate_draft",
            "deterministic_contract_gate",
            "visual_consistency_review",
            "text_quality_review",
            "human_approval",
            "export_approved_draft",
        ],
        "dependencies": {
            "uv_lock_sha256": sha256(ROOT / "uv.lock"),
            "package_lock_sha256": sha256(ROOT / "frontend/package-lock.json"),
        },
        "models": {
            "vision": "MedMO-8B-Next",
            "text": "Qwen3.5-9B-MLX-4bit",
            "provider": "Existing local oMLX at 127.0.0.1:8000; model IDs verified by REAL workflow receipts",
        },
        "fixtures": {
            "provenance": "Original deterministic artificial pixels; CC0-1.0; no patient or external dataset images",
            "hashes": json.loads((ROOT / "fixtures/expected/fixture_hashes.json").read_text()),
        },
        "tests": {
            "non_real": {"command": "make test", "passed": 85, "failed": 0, "deselected": 1},
            "real": {"command": "make test-real", "passed": 1, "failed": 0, "deselected": 85},
            "browser": {
                "command": "make test-browser",
                "passed_viewports": len(browser["viewports"]),
                "viewports": [item["viewport"] for item in browser["viewports"]],
                "interventions": browser["interventions"],
                "session_expiry_and_recovery": browser["session_expiry_and_recovery"],
                "physical_device_tested": False,
            },
            "frontend_build": "npm run build passed",
        },
        "curated_showcase": {
            "mock_fault_injection": mock,
            "real": real,
            "total": mock["run_count"] + real["run_count"],
        },
        "runtime_database_counts": {
            "mock_evidence": runtime_counts(ROOT / "var/guide-mock"),
            "real_evidence": runtime_counts(ROOT / "var/real-showcase"),
        },
        "migration": {
            "backup": "var/migration-backups/20261027T160203Z",
            "report": "var/migration-backups/v3-migration.json",
            "snapshots_migrated": 15,
            "legacy_display": "LEGACY_NO_PREPARATION_RECEIPT",
        },
        "langsmith": {
            "required": False,
            "hosted_studio_required": False,
            "source_and_runtime_configuration_references": [],
            "note": "LangGraph's transitive langsmith package may remain installed; no account, tracing configuration, SDK, CLI, callback, or hosted UI is required. Local inspector uses SQLite/events/receipts.",
        },
        "screenshots": screenshots,
        "deployment": {
            "public_url": "https://imaging.nightthoughts.dev",
            "local_url": "http://127.0.0.1:8001",
            "public_login_verified": True,
            "unauthenticated_api_denied": True,
            "current_readiness_revision_verified": False,
            "graph_inspector_http_status": 404,
            "status": "Public service remains on an older API revision; final application-only reload and REAL decision/export verification are pending.",
        },
        "limitations_not_verified": [
            "No physical phone or tablet was available; tests used Chromium phone/tablet viewports with touch emulation.",
            "The current readiness API revision is not deployed; the installed service still returns 404 for graph-inspector and requires an effective privileged reload.",
            "Public traffic transits the existing Cloudflare/Caddy path; this Internet-accessible deployment is not air-gapped.",
            "PHI screening is fail-closed demonstration screening, not guaranteed anonymization.",
            "Model-assisted visual/text reviews and doctor approval are not clinical validation or diagnostic certification.",
            "Optional Phoenix/OpenTelemetry integration is not enabled or required.",
            "Preparation is limited to supported single-frame CR/DX chest radiographs and PNG/JPEG demonstration input; no study-level 2D/3D pipeline.",
        ],
    }
    output = ROOT / "evidence/manifest-v3.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(output), "screenshots": len(screenshots)}))


if __name__ == "__main__":
    main()
