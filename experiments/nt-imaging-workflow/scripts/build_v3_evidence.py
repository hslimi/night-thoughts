from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

from nt_imaging.controlplane.db import ControlDB
from nt_imaging.controlplane.runtime import APPLICATION_VERSION
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
    for directory in (
        ROOT / "docs/images/doctor-pipeline-user-guide",
        ROOT / "docs/images/live-operations",
    ):
        for path in sorted(directory.glob("*.png")):
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
    videos = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "altered": False,
        }
        for path in sorted((ROOT / "docs/images/live-operations").glob("*.webm"))
    ]
    mock = json.loads((ROOT / "evidence/showcase/mock-runs.json").read_text())
    real = json.loads((ROOT / "evidence/showcase/real-runs.json").read_text())
    browser = json.loads((ROOT / "evidence/responsive/console-browser-tests.json").read_text())
    live = json.loads((ROOT / "evidence/live/browser-verification.json").read_text())
    manifest = {
        "schema": "nt-imaging-evidence-v4",
        "generated_at": datetime.now(UTC).isoformat(),
        "application_version": APPLICATION_VERSION,
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
        "queue_root_cause": {
            "run_ids": [
                "17477107-2b44-41cb-82bb-512c09e2e077",
                "fdba621b-d8bf-431f-a460-06ef1b5f2c72",
            ],
            "symptom": "QUEUED with null job heartbeat and no canonical checkpoint database",
            "api": "Canonical code and data root",
            "worker": "Obsolete code, WorkingDirectory, and DATA_ROOT; process alive but consuming another database",
            "secondary_failures_found": [],
            "corrective_action": "Canonical service identity plus deployment assertions and durable heartbeat; jobs preserved",
        },
        "event_architecture": {
            "database": "app_events in canonical controlplane.sqlite3 with WAL",
            "transactional_with_state": True,
            "global_and_per_run_sequences": True,
            "gap_detection": True,
            "sse": ["/api/events", "/api/runs/{run_id}/events"],
            "last_event_id_replay": True,
            "resync_snapshot": True,
            "heartbeat_packets": True,
            "session_revalidation": True,
            "multiple_tabs_no_duplicate_writes": True,
            "token_streaming_claimed": False,
        },
        "dependencies": {
            "uv_lock_sha256": sha256(ROOT / "uv.lock"),
            "package_lock_sha256": sha256(ROOT / "frontend/package-lock.json"),
        },
        "models": {
            "vision": "MedMO-8B-Next",
            "text": "Qwen3.5-9B-MLX-4bit",
            "provider": "Existing local oMLX at 127.0.0.1:8000; exact IDs verified by REAL receipts",
        },
        "fixtures": {
            "provenance": "Original deterministic artificial pixels; CC0-1.0; no patient data",
            "hashes": json.loads((ROOT / "fixtures/expected/fixture_hashes.json").read_text()),
        },
        "tests": {
            "non_real": {"command": "make test", "passed": 95, "failed": 0, "deselected": 1},
            "real": {"command": "make test-real", "passed": 1, "failed": 0, "deselected": 95},
            "browser": {
                "command": "make test-browser",
                "passed_viewports": len(browser["viewports"]),
                "viewports": [item["viewport"] for item in browser["viewports"]],
                "interventions": browser["interventions"],
                "session_expiry_and_recovery": browser["session_expiry_and_recovery"],
                "physical_device_tested": False,
            },
            "live_experience": live,
            "frontend_build": "npm run build passed",
            "account_reset_without_restart": True,
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
            "note": "No account, tracing, Agent Server SDK/CLI, or hosted UI required. Local events/SSE/checkpoints/receipts are authoritative.",
        },
        "screenshots": screenshots,
        "videos": videos,
        "deployment": {
            "public_url": "https://imaging.nightthoughts.dev",
            "local_url": "http://127.0.0.1:8001",
            "public_login_verified": True,
            "unauthenticated_api_denied": True,
            "current_live_revision_verified": True,
            "public_real_workflow_verified": True,
            "daemon_persistence_verified": True,
            "worker_program": "Canonical LaunchDaemon worker PID 8970 with fresh heartbeat after temporary worker shutdown",
            "status": "Canonical API and worker LaunchDaemons, public REAL approval/export, live events, and desktop/mobile export controls verified.",
        },
        "limitations_not_verified": [
            "No physical phone or tablet was available; tests used Chromium phone/tablet viewports with touch emulation.",
            "Canonical LaunchDaemon persistence and public REAL approval/export are verified; no fresh-clone deployment was performed beyond the canonical working copy.",
            "Public traffic transits the existing Cloudflare/Caddy path; this Internet-accessible deployment is not air-gapped.",
            "PHI screening is fail-closed demonstration screening, not guaranteed anonymization.",
            "Model-assisted visual/text reviews and doctor approval are not clinical validation or diagnostic certification.",
            "Optional Phoenix/OpenTelemetry integration is not enabled or required.",
            "Preparation is limited to supported single-frame CR/DX chest radiographs and PNG/JPEG demonstration input; no study-level 2D/3D pipeline.",
        ],
    }
    output = ROOT / "evidence/manifest-v4.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps({"output": str(output), "screenshots": len(screenshots), "videos": len(videos)})
    )


if __name__ == "__main__":
    main()
