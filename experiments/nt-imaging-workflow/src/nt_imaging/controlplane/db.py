from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast


def now() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime) -> str:
    return value.isoformat()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class QueueFull(RuntimeError):
    pass


class InvalidTransition(RuntimeError):
    pass


class ControlDB:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.migrate()

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=30000")
        return db

    def migrate(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY);
                INSERT OR IGNORE INTO schema_migrations VALUES (1);
                CREATE TABLE IF NOT EXISTS users(
                    username TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions(
                    token_hash TEXT PRIMARY KEY, username TEXT NOT NULL,
                    csrf_hash TEXT NOT NULL, created_at TEXT NOT NULL, last_seen TEXT NOT NULL,
                    absolute_expires TEXT NOT NULL, idle_expires TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS jobs(
                    job_id TEXT PRIMARY KEY, run_id TEXT UNIQUE NOT NULL, kind TEXT NOT NULL,
                    status TEXT NOT NULL, payload_json TEXT NOT NULL, cancel_requested INTEGER NOT NULL DEFAULT 0,
                    error_json TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, heartbeat_at TEXT
                );
                CREATE INDEX IF NOT EXISTS jobs_queue ON jobs(status, created_at);
                CREATE TABLE IF NOT EXISTS snapshots(
                    run_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, status TEXT NOT NULL,
                    state_json TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS security_events(
                    event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, username TEXT,
                    run_id TEXT, timestamp TEXT NOT NULL, metadata_json TEXT NOT NULL
                );
                """
            )

    def upsert_user(self, username: str, password_hash: str) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            db.execute(
                "INSERT INTO users VALUES (?,?,?,?) ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash, updated_at=excluded.updated_at",
                (username, password_hash, timestamp, timestamp),
            )
            db.execute("DELETE FROM sessions WHERE username=?", (username,))

    def user(self, username: str) -> sqlite3.Row | None:
        with self.connect() as db:
            return cast(
                sqlite3.Row | None,
                db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone(),
            )

    def create_session(
        self,
        username: str,
        raw_token: str,
        raw_csrf: str,
        absolute_minutes: int = 480,
        idle_minutes: int = 30,
    ) -> None:
        timestamp = now()
        with self.connect() as db:
            db.execute(
                "INSERT INTO sessions VALUES (?,?,?,?,?,?,?)",
                (
                    token_hash(raw_token),
                    username,
                    token_hash(raw_csrf),
                    iso(timestamp),
                    iso(timestamp),
                    iso(timestamp + timedelta(minutes=absolute_minutes)),
                    iso(timestamp + timedelta(minutes=idle_minutes)),
                ),
            )

    def session(self, raw_token: str) -> sqlite3.Row | None:
        if not raw_token:
            return None
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE token_hash=?", (token_hash(raw_token),)
            ).fetchone()
            if not row:
                return None
            current = now()
            if current >= datetime.fromisoformat(
                row["absolute_expires"]
            ) or current >= datetime.fromisoformat(row["idle_expires"]):
                db.execute("DELETE FROM sessions WHERE token_hash=?", (row["token_hash"],))
                return None
            idle = iso(current + timedelta(minutes=30))
            db.execute(
                "UPDATE sessions SET last_seen=?, idle_expires=? WHERE token_hash=?",
                (iso(current), idle, row["token_hash"]),
            )
            return cast(sqlite3.Row, row)

    def delete_session(self, raw_token: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash(raw_token),))

    def security_event(
        self,
        event_type: str,
        username: str | None = None,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO security_events VALUES (?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    event_type,
                    username,
                    run_id,
                    iso(now()),
                    json.dumps(metadata or {}, separators=(",", ":")),
                ),
            )

    def enqueue(self, run_id: str, kind: str, payload: dict[str, Any], max_queue: int = 8) -> str:
        job_id = str(uuid.uuid4())
        timestamp = iso(now())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            active = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE status IN ('QUEUED','RUNNING','EXPORTING')"
            ).fetchone()[0]
            if active >= max_queue:
                db.execute("ROLLBACK")
                raise QueueFull("The inference queue is full; retry later")
            db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    job_id,
                    run_id,
                    kind,
                    "QUEUED",
                    json.dumps(payload),
                    0,
                    None,
                    timestamp,
                    timestamp,
                    None,
                ),
            )
            db.execute("COMMIT")
        return job_id

    def claim(self) -> sqlite3.Row | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM jobs WHERE status='QUEUED' ORDER BY created_at LIMIT 1"
            ).fetchone()
            if not row:
                db.execute("COMMIT")
                return None
            timestamp = iso(now())
            if row["cancel_requested"]:
                db.execute(
                    "UPDATE jobs SET status='CANCELLED', updated_at=? WHERE job_id=?",
                    (timestamp, row["job_id"]),
                )
            else:
                db.execute(
                    "UPDATE jobs SET status='RUNNING', updated_at=?, heartbeat_at=? WHERE job_id=?",
                    (timestamp, timestamp, row["job_id"]),
                )
            db.execute("COMMIT")
            return cast(
                sqlite3.Row | None,
                db.execute("SELECT * FROM jobs WHERE job_id=?", (row["job_id"],)).fetchone(),
            )

    def requeue(self, run_id: str, kind: str, payload: dict[str, Any]) -> None:
        with self.connect() as db:
            result = db.execute(
                "UPDATE jobs SET kind=?, payload_json=?, status='QUEUED', cancel_requested=0, error_json=NULL, updated_at=? WHERE run_id=? AND status='INTERRUPTED'",
                (kind, json.dumps(payload), iso(now()), run_id),
            )
            if result.rowcount != 1:
                raise InvalidTransition("Run is not awaiting a doctor decision")

    def finish_job(
        self, job_id: str, status: str, state: dict[str, Any], error: dict[str, Any] | None = None
    ) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "UPDATE jobs SET status=?, error_json=?, updated_at=?, heartbeat_at=? WHERE job_id=?",
                (status, json.dumps(error) if error else None, timestamp, timestamp, job_id),
            )
            db.execute(
                "INSERT INTO snapshots VALUES (?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET status=excluded.status, state_json=excluded.state_json, updated_at=excluded.updated_at",
                (
                    state["run_id"],
                    state["thread_id"],
                    state["status"],
                    json.dumps(state),
                    timestamp,
                ),
            )
            db.execute("COMMIT")

    def save_snapshot(self, state: dict[str, Any], status: str | None = None) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            db.execute(
                "INSERT INTO snapshots VALUES (?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET status=excluded.status, state_json=excluded.state_json, updated_at=excluded.updated_at",
                (
                    state["run_id"],
                    state["thread_id"],
                    status or state["status"],
                    json.dumps(state),
                    timestamp,
                ),
            )

    def job_for_run(self, run_id: str) -> sqlite3.Row | None:
        with self.connect() as db:
            return cast(
                sqlite3.Row | None,
                db.execute("SELECT * FROM jobs WHERE run_id=?", (run_id,)).fetchone(),
            )

    def snapshot(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM snapshots WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            return None
        state = cast(dict[str, Any], json.loads(row["state_json"]))
        state["status"] = row["status"]
        state["snapshot_updated_at"] = row["updated_at"]
        return state

    def snapshots(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM snapshots ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            {
                **json.loads(row["state_json"]),
                "status": row["status"],
                "snapshot_updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def request_cancel(self, run_id: str) -> str:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = db.execute("SELECT * FROM jobs WHERE run_id=?", (run_id,)).fetchone()
            if not job:
                db.execute("ROLLBACK")
                raise InvalidTransition("Run not found")
            if job["status"] in {"COMPLETED", "EXPORTING", "CANCELLED"}:
                db.execute("ROLLBACK")
                raise InvalidTransition("Run cannot be cancelled in its current state")
            timestamp = iso(now())
            next_status = (
                "CANCELLED"
                if job["status"] in {"QUEUED", "INTERRUPTED", "FAILED"}
                else job["status"]
            )
            db.execute(
                "UPDATE jobs SET cancel_requested=1, status=?, updated_at=? WHERE run_id=?",
                (next_status, timestamp, run_id),
            )
            snapshot = db.execute(
                "SELECT state_json FROM snapshots WHERE run_id=?", (run_id,)
            ).fetchone()
            if snapshot:
                state = json.loads(snapshot["state_json"])
                state["status"] = "CANCELLED"
                db.execute(
                    "UPDATE snapshots SET status='CANCELLED', state_json=?, updated_at=? WHERE run_id=?",
                    (json.dumps(state), timestamp, run_id),
                )
            db.execute("COMMIT")
            return next_status

    def is_cancelled(self, run_id: str) -> bool:
        with self.connect() as db:
            row = db.execute(
                "SELECT cancel_requested FROM jobs WHERE run_id=?", (run_id,)
            ).fetchone()
            return bool(row and row["cancel_requested"])

    def heartbeat(self, job_id: str) -> None:
        with self.connect() as db:
            db.execute("UPDATE jobs SET heartbeat_at=? WHERE job_id=?", (iso(now()), job_id))
