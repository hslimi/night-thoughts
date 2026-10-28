from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from nt_imaging.config import Settings
from nt_imaging.nodes.approval import human_approval
from nt_imaging.nodes.drafting import deterministic_contract_gate, generate_draft
from nt_imaging.nodes.export import export_approved_draft
from nt_imaging.nodes.ingest import ingest_validate
from nt_imaging.nodes.modality import modality_gate
from nt_imaging.nodes.phi import phi_screen
from nt_imaging.nodes.readiness import derived_image_safety_check, imaging_readiness
from nt_imaging.nodes.reviews import text_quality_review, visual_consistency_review
from nt_imaging.nodes.terminal import fail_closed, needs_review, quarantine, reject_draft
from nt_imaging.routing import (
    after_approval,
    after_contract,
    after_draft,
    after_grounding,
    after_ingest,
    after_modality,
    after_phi,
    after_quality,
    after_readiness,
    after_safety,
)
from nt_imaging.state import AgentState


def build_graph(checkpointer: Any = None) -> Any:
    settings = Settings.from_env()
    builder = StateGraph(AgentState)
    from nt_imaging.controlplane.telemetry import track_node

    nodes: dict[str, Callable[[dict[str, Any], Settings], dict[str, Any]]] = {
        "ingest_validate": ingest_validate,
        "phi_screen": phi_screen,
        "modality_gate": modality_gate,
        "imaging_readiness": imaging_readiness,
        "derived_image_safety_check": derived_image_safety_check,
        "generate_draft": generate_draft,
        "deterministic_contract_gate": deterministic_contract_gate,
        "visual_consistency_review": visual_consistency_review,
        "text_quality_review": text_quality_review,
        "human_approval": human_approval,
        "export_approved_draft": export_approved_draft,
        "quarantine": quarantine,
        "needs_review": needs_review,
        "fail_closed": fail_closed,
        "reject_draft": reject_draft,
    }
    for name, node in nodes.items():

        def wrapped(
            state: dict[str, Any],
            node: Callable[[dict[str, Any], Settings], dict[str, Any]] = node,
        ) -> dict[str, Any]:
            return node(state, settings)

        builder.add_node(name, cast(Any, track_node(name, wrapped, settings)))
    builder.add_edge(START, "ingest_validate")
    builder.add_conditional_edges(
        "ingest_validate",
        after_ingest,
        {"phi": "phi_screen", "quarantine": "quarantine", "review": "needs_review"},
    )
    builder.add_conditional_edges(
        "phi_screen", after_phi, {"modality": "modality_gate", "quarantine": "quarantine"}
    )
    builder.add_conditional_edges(
        "modality_gate",
        after_modality,
        {"readiness": "imaging_readiness", "review": "needs_review"},
    )
    builder.add_conditional_edges(
        "imaging_readiness",
        after_readiness,
        {"safety": "derived_image_safety_check", "review": "needs_review"},
    )
    builder.add_conditional_edges(
        "derived_image_safety_check",
        after_safety,
        {"draft": "generate_draft", "review": "needs_review"},
    )
    builder.add_conditional_edges(
        "generate_draft",
        after_draft,
        {
            "contract": "deterministic_contract_gate",
            "failed": "fail_closed",
            "review": "needs_review",
        },
    )
    builder.add_conditional_edges(
        "deterministic_contract_gate",
        after_contract,
        {
            "draft": "generate_draft",
            "review": "needs_review",
            "grounding": "visual_consistency_review",
        },
    )
    builder.add_conditional_edges(
        "visual_consistency_review",
        after_grounding,
        {"draft": "generate_draft", "review": "needs_review", "quality": "text_quality_review"},
    )
    builder.add_conditional_edges(
        "text_quality_review",
        after_quality,
        {"draft": "generate_draft", "review": "needs_review", "approval": "human_approval"},
    )
    builder.add_conditional_edges(
        "human_approval",
        after_approval,
        {
            "export": "export_approved_draft",
            "rejected": "reject_draft",
            "review": "needs_review",
            "draft": "generate_draft",
        },
    )
    for terminal in (
        "export_approved_draft",
        "quarantine",
        "needs_review",
        "fail_closed",
        "reject_draft",
    ):
        builder.add_edge(terminal, END)
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()
