from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from nt_imaging.config import Settings

ROOT = Path(__file__).resolve().parents[1]


def backup_sqlite(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)


def main() -> None:
    settings = Settings.from_env()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = settings.data_root / "migration-backups" / stamp
    root.mkdir(parents=True, exist_ok=False)
    for name in [
        "controlplane.sqlite3",
        "nt_imaging.sqlite3",
        "deployed-checkpoints.sqlite3",
        "checkpoints.sqlite3",
    ]:
        backup_sqlite(settings.data_root / name, root / name)
    settings_manifest = {
        "workflow_version": settings.workflow_version,
        "inference_mode": settings.inference_mode,
        "omlx_base_url": settings.omlx_base_url,
        "vision_model": settings.vision_model,
        "text_model": settings.text_model,
        "max_attempts": settings.max_attempts,
        "max_total_model_calls": settings.max_total_model_calls,
        "max_upload_bytes": settings.max_upload_bytes,
        "max_decoded_pixels": settings.max_decoded_pixels,
        "note": "No credentials or secret environment values are included in this backup.",
    }
    (root / "configuration.json").write_text(json.dumps(settings_manifest, indent=2) + "\n")
    manifests = root / "artifact-manifests"
    manifests.mkdir()
    for path in (settings.data_root / "runs").glob("*/run_manifest.json"):
        shutil.copy2(path, manifests / f"{path.parent.name}.json")
    (root / "BACKUP.json").write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(),
                "data_root_name": settings.data_root.name,
                "databases": "SQLite online backup API",
                "configuration": "Non-secret settings only",
            },
            indent=2,
        )
        + "\n"
    )
    print(root)


if __name__ == "__main__":
    main()
