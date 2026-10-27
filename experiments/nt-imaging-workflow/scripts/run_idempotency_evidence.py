from __future__ import annotations

import os
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from nt_imaging.audit import AuditDB
from nt_imaging.constants import MOCK_LABEL
from nt_imaging.graph import build_graph
from nt_imaging.state import initial_state

if os.getenv("INFERENCE_MODE") != "MOCK":
    raise SystemExit("Replay evidence requires explicit INFERENCE_MODE=MOCK")
print(MOCK_LABEL)
root = Path(os.getenv("DATA_ROOT", "./var")).resolve()
root.mkdir(parents=True, exist_ok=True)
state = initial_state(
    str(Path("fixtures/synthetic/chest_clean.png").resolve()),
    inference_mode="MOCK",
    declared_modality="XR",
)
with SqliteSaver.from_conn_string(str(root / "replay.sqlite3")) as saver:
    app = build_graph(saver)
    config = {"configurable": {"thread_id": state["thread_id"]}}
    paused = app.invoke(state, config=config)
    assert "__interrupt__" in paused
    decision = {
        "decision": "APPROVE",
        "reviewer_display_name": "Demo Reviewer",
        "note": "Synthetic replay evidence",
    }
    first = app.invoke(Command(resume=decision), config=config)
    first_count = len(list((root / "exports").glob(f"*{state['run_id']}*")))
    second = app.invoke(Command(resume=decision), config=config)
    second_count = len(list((root / "exports").glob(f"*{state['run_id']}*")))
audit = AuditDB(root / "nt_imaging.sqlite3")
with audit.connect() as db:
    export_records = db.execute(
        "SELECT COUNT(*) FROM exports WHERE run_id=?", (state["run_id"],)
    ).fetchone()[0]
    export_events = db.execute(
        "SELECT COUNT(*) FROM events WHERE run_id=? AND event_type='APPROVED_DRAFT_EXPORTED'",
        (state["run_id"],),
    ).fetchone()[0]
assert first["status"] == second["status"] == "APPROVED_DRAFT_EXPORTED"
assert first_count == second_count == 3
assert export_records == export_events == 1
print(f"RUN_ID: {state['run_id']}")
print(f"FIRST_RESUME: {first['status']} files={first_count}")
print(f"REPLAY_RESUME: {second['status']} files={second_count}")
print(f"IDEMPOTENT_EXPORT_RECORDS: {export_records}")
print(f"EXPORT_AUDIT_EVENTS: {export_events}")
print("PASS: replay/resume produced no duplicate export side effects")
