from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .security import append_json_log


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class AuditDB:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.migrate()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def migrate(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY);
                INSERT OR IGNORE INTO schema_migrations VALUES (1);
                CREATE TABLE IF NOT EXISTS runs(
                    run_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, status TEXT NOT NULL,
                    workflow_version TEXT NOT NULL, inference_mode TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts(
                    artifact_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, role TEXT NOT NULL,
                    sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL,
                    UNIQUE(run_id, role, sha256)
                );
                CREATE TABLE IF NOT EXISTS events(
                    event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, timestamp TEXT NOT NULL,
                    workflow_version TEXT NOT NULL, node TEXT NOT NULL, event_type TEXT NOT NULL,
                    attempt INTEGER NOT NULL, reason_codes TEXT NOT NULL, metadata TEXT NOT NULL,
                    previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS model_calls(
                    call_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, stage TEXT NOT NULL,
                    model_id TEXT NOT NULL, latency_ms INTEGER NOT NULL, status TEXT NOT NULL,
                    output_sha256 TEXT, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS human_decisions(
                    run_id TEXT PRIMARY KEY, decision TEXT NOT NULL, reviewer TEXT NOT NULL,
                    note TEXT NOT NULL, decided_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS human_decision_history(
                    event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, decision TEXT NOT NULL,
                    reviewer TEXT NOT NULL, note TEXT NOT NULL, revision INTEGER NOT NULL,
                    resulting_state TEXT NOT NULL, decided_at TEXT NOT NULL,
                    UNIQUE(run_id, revision, decision, decided_at)
                );
                CREATE TABLE IF NOT EXISTS exports(
                    idempotency_key TEXT PRIMARY KEY, run_id TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL, manifest TEXT NOT NULL, created_at TEXT NOT NULL
                );
                """
            )

    def start_run(self, state: dict[str, Any]) -> None:
        now = utc_now()
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO runs VALUES (?,?,?,?,?,?,?)",
                (
                    state["run_id"],
                    state["thread_id"],
                    state["status"],
                    state["workflow_version"],
                    state["inference_mode"],
                    now,
                    now,
                ),
            )

    def update_status(self, run_id: str, status: str) -> None:
        validate_run_id(run_id)
        with self.connect() as db:
            db.execute(
                "UPDATE runs SET status=?, updated_at=? WHERE run_id=?", (status, utc_now(), run_id)
            )

    def artifact(self, run_id: str, artifact_id: str, role: str, sha256: str, size: int) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO artifacts VALUES (?,?,?,?,?)",
                (artifact_id, run_id, role, sha256, size),
            )

    def event(
        self,
        run_id: str,
        node: str,
        event_type: str,
        *,
        workflow_version: str,
        attempt: int = 0,
        reason_codes: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        safe_metadata = metadata or {}
        serialized = json.dumps(safe_metadata, sort_keys=True, separators=(",", ":"))
        if any(
            key.lower() in {"api_key", "secret_key", "authorization", "token"}
            for key in safe_metadata
        ):
            raise ValueError("Secrets are not permitted in audit metadata")
        with self.connect() as db:
            previous = db.execute(
                "SELECT event_hash FROM events WHERE run_id=? ORDER BY rowid DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            previous_hash = previous[0] if previous else "0" * 64
            event_id = str(uuid.uuid4())
            timestamp = utc_now()
            body = {
                "event_id": event_id,
                "run_id": run_id,
                "timestamp": timestamp,
                "workflow_version": workflow_version,
                "node": node,
                "event_type": event_type,
                "attempt": attempt,
                "reason_codes": reason_codes or [],
                "metadata": safe_metadata,
                "previous_hash": previous_hash,
            }
            event_hash = hashlib.sha256(
                (previous_hash + json.dumps(body, sort_keys=True, separators=(",", ":"))).encode()
            ).hexdigest()
            db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    event_id,
                    run_id,
                    timestamp,
                    workflow_version,
                    node,
                    event_type,
                    attempt,
                    json.dumps(reason_codes or []),
                    serialized,
                    previous_hash,
                    event_hash,
                ),
            )
            mode_row = db.execute(
                "SELECT inference_mode FROM runs WHERE run_id=?", (run_id,)
            ).fetchone()
        append_json_log(
            self.path.parent / "logs" / "audit.jsonl",
            {
                **body,
                "event_hash": event_hash,
                "inference_mode": mode_row[0] if mode_row else "UNKNOWN",
            },
        )
        return event_id

    def model_call(
        self,
        run_id: str,
        stage: str,
        model_id: str,
        latency_ms: int,
        status: str,
        output_sha256: str | None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO model_calls VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    run_id,
                    stage,
                    model_id,
                    latency_ms,
                    status,
                    output_sha256,
                    utc_now(),
                ),
            )

    def model_call_count(self, run_id: str) -> int:
        with self.connect() as db:
            return int(
                db.execute("SELECT COUNT(*) FROM model_calls WHERE run_id=?", (run_id,)).fetchone()[
                    0
                ]
            )

    def timeline(self, run_id: str) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM events WHERE run_id=? ORDER BY rowid", (run_id,)
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "timestamp": row["timestamp"],
                "node": row["node"],
                "event_type": row["event_type"],
                "attempt": row["attempt"],
                "reason_codes": json.loads(row["reason_codes"]),
                "metadata": json.loads(row["metadata"]),
                "event_hash": row["event_hash"],
                "previous_hash": row["previous_hash"],
            }
            for row in rows
        ]


def validate_run_id(run_id: str) -> None:
    uuid.UUID(run_id)
