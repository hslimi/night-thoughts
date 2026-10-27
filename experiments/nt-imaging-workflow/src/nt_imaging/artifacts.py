from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

SAFE_ID = re.compile(r"^(?:[a-f0-9]{32}|[0-9a-f-]{36})$")


class ArtifactError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_id(value: str) -> str:
    if not SAFE_ID.fullmatch(value):
        raise ArtifactError("Invalid opaque artifact or run identifier")
    return value


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def run_dir(self, run_id: str, kind: str = "artifacts") -> Path:
        validate_id(run_id)
        if kind not in {"incoming", "artifacts", "quarantine", "runs"}:
            raise ArtifactError("Unsupported artifact area")
        path = self.root / kind / run_id
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path, 0o700)
        return path

    def copy_source(self, source: Path, run_id: str, artifact_id: str) -> tuple[Path, str, int]:
        validate_id(run_id)
        validate_id(artifact_id)
        if source.is_symlink() or not source.is_file():
            raise ArtifactError("Source must be a regular, non-symlink file")
        destination = self.run_dir(run_id, "incoming") / f"{artifact_id}.source"
        with source.open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
        os.chmod(destination, 0o600)
        return destination, sha256_file(destination), destination.stat().st_size

    def source_path(self, run_id: str, artifact_id: str) -> Path:
        return self.run_dir(run_id, "incoming") / f"{validate_id(artifact_id)}.source"

    def derived_path(self, run_id: str, artifact_id: str, suffix: str) -> Path:
        if suffix not in {".png", ".dcm", ".json"}:
            raise ArtifactError("Unsupported derived artifact type")
        return self.run_dir(run_id) / f"{validate_id(artifact_id)}{suffix}"

    def write_json(self, path: Path, value: dict[str, Any]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
