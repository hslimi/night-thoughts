from __future__ import annotations

import argparse
import json
import time
from typing import Any, cast

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from ..config import Settings
from ..graph import build_graph
from ..schemas import safe_error
from .db import ControlDB
from .runtime import runtime_identity


def public_state(values: dict[str, Any]) -> dict[str, Any]:
    state = cast(dict[str, Any], json.loads(json.dumps(values, default=str)))
    state.pop("source_path", None)
    state.pop("__interrupt__", None)
    return state


class Worker:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db = ControlDB(settings.data_root / "controlplane.sqlite3")
        self.identity = runtime_identity(settings)
        self.worker_id = str(self.identity["instance_id"])

    def heartbeat(self) -> None:
        self.db.worker_heartbeat(
            self.worker_id,
            int(self.identity["pid"]),
            str(self.identity["code_fingerprint"]),
            str(self.identity["data_fingerprint"]),
        )

    def recover(self) -> None:
        with self.db.connect() as db:
            rows = db.execute(
                "SELECT job_id,run_id FROM jobs WHERE status IN ('RUNNING','EXPORTING')"
            ).fetchall()
        for row in rows:
            snapshot = self.db.snapshot(row["run_id"])
            if snapshot and snapshot.get("export_manifest"):
                continue
            if snapshot:
                snapshot["status"] = "NEEDS_HUMAN_REVIEW"
                snapshot["error"] = safe_error(
                    "WORKER_RESTART_RECOVERY",
                    "Worker restarted; explicit technical retry is required",
                    retryable=True,
                )
                self.db.finish_job(
                    row["job_id"], "FAILED", snapshot, snapshot["error"], event_type="RUN_FAILED"
                )

    def run(self, once: bool = False) -> None:
        self.db.worker_started(
            self.worker_id,
            int(self.identity["pid"]),
            str(self.identity["code_fingerprint"]),
            str(self.identity["data_fingerprint"]),
        )
        last_heartbeat = 0.0
        try:
            self.recover()
            while True:
                if time.monotonic() - last_heartbeat >= 2:
                    self.heartbeat()
                    last_heartbeat = time.monotonic()
                job = self.db.claim()
                if not job:
                    if once:
                        return
                    time.sleep(0.5)
                    continue
                self.execute(job)
                if once:
                    return
        finally:
            self.db.worker_stopped(
                self.worker_id,
                int(self.identity["pid"]),
                str(self.identity["code_fingerprint"]),
                str(self.identity["data_fingerprint"]),
            )

    def execute(self, job: Any) -> None:
        run_id = job["run_id"]
        try:
            if self.db.is_cancelled(run_id):
                snapshot = self.db.snapshot(run_id) or json.loads(job["payload_json"])
                snapshot["status"] = "CANCELLED"
                self.db.finish_job(
                    job["job_id"], "CANCELLED", public_state(snapshot), event_type="RUN_CANCELLED"
                )
                return
            payload = json.loads(job["payload_json"])
            with SqliteSaver.from_conn_string(
                str(self.settings.data_root / "deployed-checkpoints.sqlite3")
            ) as saver:
                app = build_graph(saver)
                config = {"configurable": {"thread_id": run_id}}
                graph_input = (
                    payload["state"]
                    if job["kind"] == "START"
                    else Command(resume=payload["decision"])
                )
                result = (
                    dict(payload["state"])
                    if job["kind"] == "START"
                    else dict(self.db.snapshot(run_id) or {})
                )
                result.update({"run_id": run_id, "thread_id": run_id})
                for event in app.stream(graph_input, config=config, stream_mode="updates"):
                    for node, update in event.items():
                        if node == "__interrupt__":
                            result[node] = update
                            continue
                        result.update(update)
                        result["current_node"] = node
                        self.db.heartbeat(job["job_id"])
                        if self.db.is_cancelled(run_id):
                            raise RuntimeError("Cancellation requested before the next graph node")
                        self.db.save_snapshot(public_state(result), result.get("status", "RUNNING"))
            if self.db.is_cancelled(run_id):
                raise RuntimeError("Cancellation requested before workflow completion")
            paused = "__interrupt__" in result
            result = public_state(result)
            if paused:
                result["status"] = "AWAITING_HUMAN_APPROVAL"
                result["current_node"] = "human_approval"
                status = "INTERRUPTED"
            elif result.get("status") == "CANCELLED":
                status = "CANCELLED"
            elif result.get("status") in {"FAILED", "MODEL_OUTPUT_INVALID"}:
                status = "FAILED"
            else:
                status = "COMPLETED"
            self.db.finish_job(job["job_id"], status, result, result.get("error"))
        except Exception as exc:  # noqa: BLE001 - worker converts all execution failures to safe terminal state
            snapshot = self.db.snapshot(run_id)
            if not snapshot:
                payload = json.loads(job["payload_json"])
                snapshot = public_state(
                    payload.get(
                        "state", {"run_id": run_id, "thread_id": run_id, "status": "RECEIVED"}
                    )
                )
            if self.db.is_cancelled(run_id):
                snapshot["status"] = "CANCELLED"
                self.db.finish_job(job["job_id"], "CANCELLED", snapshot, event_type="RUN_CANCELLED")
                return
            snapshot["status"] = "FAILED"
            error = safe_error(
                "WORKER_EXECUTION_FAILED",
                f"Workflow execution failed safely ({type(exc).__name__})",
                retryable=True,
            )
            snapshot["error"] = error
            self.db.finish_job(
                job["job_id"], "FAILED", public_state(snapshot), error, event_type="RUN_FAILED"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    Worker(Settings.from_env()).run(once=args.once)


if __name__ == "__main__":
    main()
