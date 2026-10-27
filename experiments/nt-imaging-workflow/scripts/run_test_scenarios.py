from __future__ import annotations

import json
import os
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from nt_imaging.cli import safe_summary
from nt_imaging.graph import build_graph
from nt_imaging.state import initial_state

if os.getenv("INFERENCE_MODE") != "MOCK":
    raise SystemExit("Fault-injection scenarios require explicit INFERENCE_MODE=MOCK")
print("MOCK FAULT-INJECTION TEST — workflow behavior only; not model-quality evidence.")
results = []
for name, fixture, decision in [
    ("approval", "chest_clean.png", "APPROVE"),
    ("rejection", "chest_clean.png", "REJECT"),
    ("phi_quarantine", "chest_unexpected_text.png", None),
    ("retry_exhaustion", "chest_clean.png", None),
]:
    state = initial_state(
        str(Path("fixtures/synthetic") / fixture),
        inference_mode="MOCK",
        fault_profile="grounding_fail_always" if name == "retry_exhaustion" else "none",
        declared_modality="XR",
    )
    with SqliteSaver.from_conn_string("var/scenarios.sqlite3") as saver:
        app = build_graph(saver)
        config = {"configurable": {"thread_id": state["thread_id"]}}
        result = app.invoke(state, config=config)
        exports_before = (
            list(Path("var/exports").glob(f"*{state['run_id']}*"))
            if Path("var/exports").exists()
            else []
        )
        if decision:
            result = app.invoke(
                Command(
                    resume={
                        "decision": decision,
                        "reviewer_display_name": "Demo Reviewer",
                        "note": "Synthetic scenario decision",
                    }
                ),
                config=config,
            )
        exports_after = (
            list(Path("var/exports").glob(f"*{state['run_id']}*"))
            if Path("var/exports").exists()
            else []
        )
    summary = safe_summary(result)
    summary["export_count"] = len(exports_after)
    summary["no_export"] = not exports_after
    results.append({"scenario": name, **summary})
    print(
        json.dumps(
            {
                "scenario": name,
                "status": result["status"],
                "export_count": len(exports_after),
                "run_id": state["run_id"],
            }
        )
    )
Path("var/runs").mkdir(parents=True, exist_ok=True)
Path("var/runs/mock_scenarios.json").write_text(json.dumps(results, indent=2) + "\n")
