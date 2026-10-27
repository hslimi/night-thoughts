from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class InferenceResponse:
    raw: str
    model_id: str
    latency_ms: int
    usage: dict[str, Any] = field(default_factory=dict)


class InferenceProvider(Protocol):
    def generate_draft(
        self, image_path: Path, prompt: str, prior_issues: list[dict[str, Any]]
    ) -> InferenceResponse: ...
    def repair_draft(self, malformed: str, validation_message: str) -> InferenceResponse: ...
    def visual_review(
        self, image_path: Path, prompt: str, draft: dict[str, Any]
    ) -> InferenceResponse: ...
    def quality_review(
        self, prompt: str, draft: dict[str, Any], policy: dict[str, Any]
    ) -> InferenceResponse: ...
    def capabilities(self) -> dict[str, Any]: ...


class ModelBudgetExceeded(RuntimeError):
    pass
