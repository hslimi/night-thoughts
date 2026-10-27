from __future__ import annotations

from typing import Any

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
    nodes = {
        "ingest_validate": lambda state: ingest_validate(state, settings),
        "phi_screen": lambda state: phi_screen(state, settings),
        "modality_gate": lambda state: modality_gate(state, settings),
        "imaging_readiness": lambda state: imaging_readiness(state, settings),
        "derived_image_safety_check": lambda state: derived_image_safety_check(state, settings),
        "generate_draft": lambda state: generate_draft(state, settings),
        "deterministic_contract_gate": lambda state: deterministic_contract_gate(state, settings),
        "visual_consistency_review": lambda state: visual_consistency_review(state, settings),
        "text_quality_review": lambda state: text_quality_review(state, settings),
        "human_approval": lambda state: human_approval(state, settings),
        "export_approved_draft": lambda state: export_approved_draft(state, settings),
        "quarantine": lambda state: quarantine(state, settings),
        "needs_review": lambda state: needs_review(state, settings),
        "fail_closed": lambda state: fail_closed(state, settings),
        "reject_draft": lambda state: reject_draft(state, settings),
    }
    for name, node in nodes.items():
        builder.add_node(name, node)
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
