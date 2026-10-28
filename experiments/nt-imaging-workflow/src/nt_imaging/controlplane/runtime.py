from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from ..config import Settings
from .db import fingerprint

APPLICATION_VERSION = "4.0.0"


def code_fingerprint() -> str:
    root = Path(__file__).resolve().parents[3]
    digest = hashlib.sha256()
    for relative in (
        "pyproject.toml",
        "src/nt_imaging/graph.py",
        "src/nt_imaging/controlplane/api.py",
        "src/nt_imaging/controlplane/worker.py",
        "src/nt_imaging/controlplane/db.py",
        "src/nt_imaging/controlplane/telemetry.py",
    ):
        digest.update(relative.encode())
        digest.update((root / relative).read_bytes())
    return digest.hexdigest()[:16]


def instance_id(settings: Settings) -> str:
    path = settings.data_root / "runtime-instance-id"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        return path.read_text().strip()
    value = str(uuid.uuid4())
    temporary = path.with_suffix(".tmp")
    temporary.write_text(value + "\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    return value


def runtime_identity(settings: Settings) -> dict[str, str | int]:
    return {
        "application_version": APPLICATION_VERSION,
        "instance_id": instance_id(settings),
        "code_fingerprint": code_fingerprint(),
        "data_fingerprint": fingerprint(settings.data_root),
        "pid": os.getpid(),
    }
