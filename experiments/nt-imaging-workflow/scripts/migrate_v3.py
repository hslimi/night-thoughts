from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from nt_imaging.config import Settings
from nt_imaging.controlplane.db import ControlDB

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = Settings.from_env()
    db = ControlDB(settings.data_root / "controlplane.sqlite3")
    with db.connect() as connection:
        rows = connection.execute("SELECT run_id,state_json FROM snapshots").fetchall()
        migrated = 0
        for row in rows:
            state = json.loads(row["state_json"])
            if "preparation_policy_version" in state:
                continue
            state["sanitized_artifact_id"] = state.get("sanitized_artifact_id", "")
            state["readiness_status"] = "READY"
            state["readiness_receipt_id"] = None
            state["prepared_artifact_id"] = state.get("preprocessed_artifact_id")
            state["prepared_sha256"] = state.get("preprocessed_sha256")
            state["display_thumbnail_id"] = None
            state["preparation_policy_version"] = "legacy"
            state["preparation_operations"] = []
            state["preparation_metrics"] = state.pop("preprocess_metadata", {})
            state["preparation_warnings"] = ["LEGACY_NO_PREPARATION_RECEIPT"]
            state["derived_phi_status"] = "CLEAR"
            state.pop("preprocessed_artifact_id", None)
            state.pop("preprocessed_sha256", None)
            connection.execute(
                "UPDATE snapshots SET state_json=? WHERE run_id=?",
                (json.dumps(state), row["run_id"]),
            )
            migrated += 1
    record = {
        "migration": "v3-readiness",
        "timestamp": datetime.now(UTC).isoformat(),
        "snapshots_migrated": migrated,
        "legacy_display": "Legacy runs show READY with LEGACY_NO_PREPARATION_RECEIPT and no receipt download. Existing IDs/history are preserved.",
        "checkpoints": "Existing checkpoints remain intact. New readiness work requires a new run; legacy checkpoint fields are not reused as new derivatives.",
        "backup": "var/migration-backups/20261027T160203Z",
    }
    output = settings.data_root / "migration-backups" / "v3-migration.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
