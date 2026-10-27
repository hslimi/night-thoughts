from __future__ import annotations

import os
from pathlib import Path

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from nt_imaging.artifacts import ArtifactStore
from nt_imaging.cli import safe_summary
from nt_imaging.config import Settings
from nt_imaging.graph import build_graph
from nt_imaging.schemas import ImagingDraft
from nt_imaging.state import initial_state

pytestmark = pytest.mark.real


def test_real_synthetic_workflow_reaches_interrupt_and_exports_after_approval() -> None:
    assert os.getenv("INFERENCE_MODE") == "REAL"
    settings = Settings.from_env()
    settings.ensure_directories()
    state = initial_state(
        str(Path("fixtures/synthetic/chest_clean.png").resolve()),
        inference_mode="REAL",
        workflow_version=settings.workflow_version,
        max_attempts=settings.max_attempts,
        max_total_model_calls=settings.max_total_model_calls,
        declared_modality="XR",
        vision_model_id=settings.vision_model,
        text_model_id=settings.text_model,
    )
    with SqliteSaver.from_conn_string(str(settings.data_root / "real_test.sqlite3")) as saver:
        app = build_graph(saver)
        config = {"configurable": {"thread_id": state["thread_id"]}}
        paused = app.invoke(state, config=config)
        assert "__interrupt__" in paused, safe_summary(paused)
        ImagingDraft.model_validate(paused["draft"])
        assert paused["grounding_status"] == "PASS"
        assert paused["quality_status"] == "PASS"
        resumed = app.invoke(
            Command(
                resume={
                    "decision": "APPROVE",
                    "reviewer_display_name": "Demo Reviewer",
                    "note": "Synthetic real-provider demonstration",
                }
            ),
            config=config,
        )
    assert resumed["status"] == "APPROVED_DRAFT_EXPORTED"
    assert resumed["export_manifest"]["vision_model_id"] == settings.vision_model
    assert resumed["export_manifest"]["text_model_id"] == settings.text_model
    ArtifactStore(settings.data_root).write_json(
        ArtifactStore(settings.data_root).run_dir(state["run_id"], "runs") / "real_evidence.json",
        safe_summary(resumed),
    )
