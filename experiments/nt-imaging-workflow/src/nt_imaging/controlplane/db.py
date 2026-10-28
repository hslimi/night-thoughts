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


def fingerprint(value: Path | str) -> str:
    return hashlib.sha256(str(value).encode()).hexdigest()[:16]


class QueueFull(RuntimeError):
    pass


class InvalidTransition(RuntimeError):
    pass


class ControlDB:
    def __init__(self, path: Path):
        self.path = path
        self.last_invalidated_sessions = 0
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
                INSERT OR IGNORE INTO schema_migrations VALUES (2);
                INSERT OR IGNORE INTO schema_migrations VALUES (3);
                INSERT OR IGNORE INTO schema_migrations VALUES (4);
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
                CREATE TABLE IF NOT EXISTS app_events(
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    run_id TEXT,
                    thread_id TEXT,
                    job_id TEXT,
                    run_sequence INTEGER,
                    event_type TEXT NOT NULL,
                    run_status TEXT NOT NULL,
                    node_name TEXT,
                    attempt INTEGER NOT NULL DEFAULT 0,
                    revision INTEGER NOT NULL DEFAULT 0,
                    model_call_sequence INTEGER,
                    timestamp_utc TEXT NOT NULL,
                    duration_ms INTEGER,
                    payload_json TEXT NOT NULL,
                    workflow_version TEXT NOT NULL,
                    inference_mode TEXT NOT NULL,
                    UNIQUE(run_id,run_sequence)
                );
                CREATE INDEX IF NOT EXISTS app_events_run_sequence
                    ON app_events(run_id,run_sequence);
                CREATE INDEX IF NOT EXISTS app_events_type_time
                    ON app_events(event_type,timestamp_utc);
                CREATE TABLE IF NOT EXISTS workers(
                    worker_id TEXT PRIMARY KEY,
                    pid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    code_fingerprint TEXT NOT NULL,
                    data_fingerprint TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    last_heartbeat TEXT NOT NULL,
                    last_event_heartbeat TEXT
                );
                """
            )

    def _append_event(
        self,
        db: sqlite3.Connection,
        event_type: str,
        *,
        state: dict[str, Any] | None = None,
        run_id: str | None = None,
        thread_id: str | None = None,
        job_id: str | None = None,
        node_name: str | None = None,
        duration_ms: int | None = None,
        model_call_sequence: int | None = None,
        payload: dict[str, Any] | None = None,
        run_status: str | None = None,
        workflow_version: str | None = None,
        inference_mode: str | None = None,
    ) -> int:
        current = state or {}
        actual_run = run_id or current.get("run_id")
        run_sequence = None
        if actual_run:
            run_sequence = db.execute(
                "SELECT COALESCE(MAX(run_sequence),0)+1 FROM app_events WHERE run_id=?",
                (actual_run,),
            ).fetchone()[0]
        values = (
            str(uuid.uuid4()),
            actual_run,
            thread_id or current.get("thread_id"),
            job_id,
            run_sequence,
            event_type,
            run_status or current.get("status", "WORKER"),
            node_name,
            int(current.get("attempt", 0)),
            int(current.get("revision", 0)),
            model_call_sequence,
            iso(now()),
            duration_ms,
            json.dumps(payload or {}, default=str, separators=(",", ":")),
            workflow_version or current.get("workflow_version", "unknown"),
            inference_mode or current.get("inference_mode", "SYSTEM"),
        )
        cursor = db.execute(
            """INSERT INTO app_events(
                event_id,run_id,thread_id,job_id,run_sequence,event_type,run_status,
                node_name,attempt,revision,model_call_sequence,timestamp_utc,duration_ms,
                payload_json,workflow_version,inference_mode
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            values,
        )
        return int(cursor.lastrowid or 0)

    def record_event(
        self,
        event_type: str,
        *,
        state: dict[str, Any] | None = None,
        run_id: str | None = None,
        thread_id: str | None = None,
        job_id: str | None = None,
        node_name: str | None = None,
        duration_ms: int | None = None,
        model_call_sequence: int | None = None,
        payload: dict[str, Any] | None = None,
        run_status: str | None = None,
        workflow_version: str | None = None,
        inference_mode: str | None = None,
    ) -> int:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if state:
                timestamp = iso(now())
                db.execute(
                    "INSERT INTO snapshots VALUES (?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET status=excluded.status,state_json=excluded.state_json,updated_at=excluded.updated_at",
                    (
                        state["run_id"],
                        state["thread_id"],
                        state["status"],
                        json.dumps(state, default=str),
                        timestamp,
                    ),
                )
            sequence = self._append_event(
                db,
                event_type,
                state=state,
                run_id=run_id,
                thread_id=thread_id,
                job_id=job_id,
                node_name=node_name,
                duration_ms=duration_ms,
                model_call_sequence=model_call_sequence,
                payload=payload,
                run_status=run_status,
                workflow_version=workflow_version,
                inference_mode=inference_mode,
            )
            db.execute("COMMIT")
            return sequence

    def events(
        self, after: int = 0, run_id: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        with self.connect() as db:
            if run_id:
                rows = db.execute(
                    "SELECT * FROM app_events WHERE run_id=? AND sequence>? ORDER BY sequence LIMIT ?",
                    (run_id, after, limit),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM app_events WHERE sequence>? ORDER BY sequence LIMIT ?",
                    (after, limit),
                ).fetchall()
        return [self._event_dict(row) for row in rows]

    def run_events(self, run_id: str, after: int = 0, limit: int = 1000) -> list[dict[str, Any]]:
        return self.events(after=after, run_id=run_id, limit=limit)

    @staticmethod
    def _event_dict(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        value["payload"] = json.loads(value.pop("payload_json"))
        return value

    def latest_sequence(self) -> int:
        with self.connect() as db:
            return int(db.execute("SELECT COALESCE(MAX(sequence),0) FROM app_events").fetchone()[0])

    def event_gaps(self, run_id: str, after: int = 0) -> list[int]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT run_sequence FROM app_events WHERE run_id=? AND run_sequence>? ORDER BY run_sequence",
                (run_id, after),
            ).fetchall()
        sequences = [int(row[0]) for row in rows]
        if not sequences:
            return []
        expected = list(range(sequences[0], sequences[-1] + 1))
        return sorted(set(expected) - set(sequences))

    def run_sequence_for_event(self, sequence: int) -> int | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT run_sequence FROM app_events WHERE sequence=?", (sequence,)
            ).fetchone()
        return int(row[0]) if row and row[0] is not None else None

    def upsert_user(self, username: str, password_hash: str) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO users VALUES (?,?,?,?) ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash, updated_at=excluded.updated_at",
                (username, password_hash, timestamp, timestamp),
            )
            sessions = db.execute(
                "SELECT COUNT(*) FROM sessions WHERE username=?", (username,)
            ).fetchone()[0]
            db.execute("DELETE FROM sessions WHERE username=?", (username,))
            db.execute("COMMIT")
        self.last_invalidated_sessions = int(sessions)

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
        state = dict(payload.get("state") or self.snapshot(run_id) or {})
        state.update(
            {"run_id": run_id, "thread_id": state.get("thread_id", run_id), "status": "QUEUED"}
        )
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
            db.execute(
                "INSERT INTO snapshots VALUES (?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET status=excluded.status,state_json=excluded.state_json,updated_at=excluded.updated_at",
                (run_id, state["thread_id"], "QUEUED", json.dumps(state, default=str), timestamp),
            )
            self._append_event(
                db,
                "RUN_CREATED",
                state=state,
                job_id=job_id,
                node_name="queue",
                payload={
                    "kind": kind,
                    "snapshot": {k: v for k, v in state.items() if k != "source_path"},
                },
            )
            self._append_event(
                db,
                "RUN_QUEUED",
                state=state,
                job_id=job_id,
                node_name="queue",
                payload={
                    "queue_position": active + 1,
                    "snapshot": {k: v for k, v in state.items() if k != "source_path"},
                },
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
            snapshot_row = db.execute(
                "SELECT state_json FROM snapshots WHERE run_id=?", (row["run_id"],)
            ).fetchone()
            state = json.loads(snapshot_row["state_json"]) if snapshot_row else {}
            if row["cancel_requested"]:
                db.execute(
                    "UPDATE jobs SET status='CANCELLED',updated_at=? WHERE job_id=?",
                    (timestamp, row["job_id"]),
                )
                state["status"] = "CANCELLED"
                self._append_event(
                    db,
                    "RUN_CANCELLED",
                    state=state,
                    job_id=row["job_id"],
                    node_name="queue",
                )
            else:
                db.execute(
                    "UPDATE jobs SET status='RUNNING',updated_at=?,heartbeat_at=? WHERE job_id=?",
                    (timestamp, timestamp, row["job_id"]),
                )
                state["status"] = "RUNNING"
                db.execute(
                    "UPDATE snapshots SET status='RUNNING',state_json=?,updated_at=? WHERE run_id=?",
                    (json.dumps(state, default=str), timestamp, row["run_id"]),
                )
                self._append_event(
                    db,
                    "RUN_STARTED",
                    state=state,
                    job_id=row["job_id"],
                    node_name="queue",
                    payload={"snapshot": {k: v for k, v in state.items() if k != "source_path"}},
                )
            db.execute("COMMIT")
            return cast(
                sqlite3.Row | None,
                db.execute("SELECT * FROM jobs WHERE job_id=?", (row["job_id"],)).fetchone(),
            )

    def requeue(self, run_id: str, kind: str, payload: dict[str, Any]) -> None:
        with self.connect() as db:
            result = db.execute(
                "UPDATE jobs SET kind=?,payload_json=?,status='QUEUED',cancel_requested=0,error_json=NULL,updated_at=? WHERE run_id=? AND status='INTERRUPTED'",
                (kind, json.dumps(payload), iso(now()), run_id),
            )
            if result.rowcount != 1:
                raise InvalidTransition("Run is not awaiting a doctor decision")

    def finish_job(
        self,
        job_id: str,
        status: str,
        state: dict[str, Any],
        error: dict[str, Any] | None = None,
        event_type: str | None = None,
    ) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "UPDATE jobs SET status=?,error_json=?,updated_at=?,heartbeat_at=? WHERE job_id=?",
                (status, json.dumps(error) if error else None, timestamp, timestamp, job_id),
            )
            db.execute(
                "INSERT INTO snapshots VALUES (?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET status=excluded.status,state_json=excluded.state_json,updated_at=excluded.updated_at",
                (
                    state["run_id"],
                    state["thread_id"],
                    state["status"],
                    json.dumps(state, default=str),
                    timestamp,
                ),
            )
            if event_type:
                self._append_event(
                    db,
                    event_type,
                    state=state,
                    job_id=job_id,
                    node_name=state.get("current_node"),
                    payload={"job_status": status, "error": error},
                )
            db.execute("COMMIT")

    def save_snapshot(self, state: dict[str, Any], status: str | None = None) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            db.execute(
                "INSERT INTO snapshots VALUES (?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET status=excluded.status,state_json=excluded.state_json,updated_at=excluded.updated_at",
                (
                    state["run_id"],
                    state["thread_id"],
                    status or state["status"],
                    json.dumps(state, default=str),
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

    def queue_position(self, run_id: str) -> int | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT created_at FROM jobs WHERE run_id=? AND status='QUEUED'", (run_id,)
            ).fetchone()
            if not row:
                return None
            return int(
                db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE status='QUEUED' AND created_at<=?",
                    (row["created_at"],),
                ).fetchone()[0]
            )

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
                "UPDATE jobs SET cancel_requested=1,status=?,updated_at=? WHERE run_id=?",
                (next_status, timestamp, run_id),
            )
            snapshot = db.execute(
                "SELECT state_json FROM snapshots WHERE run_id=?", (run_id,)
            ).fetchone()
            state = (
                json.loads(snapshot["state_json"])
                if snapshot
                else {"run_id": run_id, "thread_id": run_id}
            )
            state["status"] = "CANCELLED"
            db.execute(
                "UPDATE snapshots SET status='CANCELLED',state_json=?,updated_at=? WHERE run_id=?",
                (json.dumps(state, default=str), timestamp, run_id),
            )
            self._append_event(
                db,
                "RUN_CANCELLED",
                state=state,
                job_id=job["job_id"],
                node_name=state.get("current_node", "queue"),
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

    def worker_started(self, worker_id: str, pid: int, code: str, data: str) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            db.execute(
                "INSERT INTO workers VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(worker_id) DO UPDATE SET pid=excluded.pid,status='RUNNING',code_fingerprint=excluded.code_fingerprint,data_fingerprint=excluded.data_fingerprint,started_at=excluded.started_at,last_heartbeat=excluded.last_heartbeat",
                (worker_id, pid, "RUNNING", code, data, timestamp, timestamp, None),
            )
        self.record_event(
            "WORKER_STARTED",
            run_status="RUNNING",
            node_name="worker",
            payload={
                "worker_id": worker_id,
                "pid": pid,
                "code_fingerprint": code,
                "data_fingerprint": data,
            },
        )

    def worker_heartbeat(self, worker_id: str, pid: int, code: str, data: str) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            previous = db.execute(
                "SELECT last_event_heartbeat FROM workers WHERE worker_id=?", (worker_id,)
            ).fetchone()
            db.execute(
                "UPDATE workers SET pid=?,status='RUNNING',code_fingerprint=?,data_fingerprint=?,last_heartbeat=? WHERE worker_id=?",
                (pid, code, data, timestamp, worker_id),
            )
            emit = (
                not previous
                or not previous[0]
                or (now() - datetime.fromisoformat(previous[0]) >= timedelta(seconds=15))
            )
            if emit:
                db.execute(
                    "UPDATE workers SET last_event_heartbeat=? WHERE worker_id=?",
                    (timestamp, worker_id),
                )
        if emit:
            self.record_event(
                "WORKER_HEARTBEAT",
                run_status="RUNNING",
                node_name="worker",
                payload={
                    "worker_id": worker_id,
                    "pid": pid,
                    "code_fingerprint": code,
                    "data_fingerprint": data,
                },
            )

    def worker_stopped(self, worker_id: str, pid: int, code: str, data: str) -> None:
        timestamp = iso(now())
        with self.connect() as db:
            db.execute(
                "UPDATE workers SET status='STOPPED',last_heartbeat=? WHERE worker_id=?",
                (timestamp, worker_id),
            )
        self.record_event(
            "WORKER_STOPPED",
            run_status="STOPPED",
            node_name="worker",
            payload={
                "worker_id": worker_id,
                "pid": pid,
                "code_fingerprint": code,
                "data_fingerprint": data,
            },
        )

    def worker_status(self) -> sqlite3.Row | None:
        with self.connect() as db:
            return cast(
                sqlite3.Row | None,
                db.execute("SELECT * FROM workers ORDER BY last_heartbeat DESC LIMIT 1").fetchone(),
            )
