from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..constants import DRAFT_NOTICE
from .base import InferenceResponse

PROFILES = {
    "none",
    "malformed_draft_once",
    "malformed_draft_always",
    "contract_fail_once",
    "grounding_fail_once",
    "grounding_fail_always",
    "quality_fail_once",
    "quality_fail_always",
    "model_timeout",
    "model_unavailable",
    "slow_draft",
    "derived_phi_block",
}


class MockProvider:
    def __init__(self, fault_profile: str | None = None):
        self.fault_profile = fault_profile or "none"
        if self.fault_profile not in PROFILES:
            raise ValueError("Unknown mock fault profile")
        self.draft_calls = 0
        self.visual_calls = 0
        self.quality_calls = 0

    def _response(self, value: Any, model: str = "mock-synthetic-provider") -> InferenceResponse:
        started = time.monotonic()
        if self.fault_profile == "model_timeout":
            raise TimeoutError("Mock fault injection: model timeout")
        if self.fault_profile == "model_unavailable":
            raise RuntimeError("Mock fault injection: model unavailable")
        raw = value if isinstance(value, str) else json.dumps(value)
        return InferenceResponse(
            raw, model, int((time.monotonic() - started) * 1000), {"mock": True}
        )

    def _valid_draft(self) -> dict[str, Any]:
        return {
            "technique": "Single synthetic chest-like demonstration image.",
            "comparison": "No comparison supplied.",
            "findings": [
                {
                    "label": "Synthetic bilateral lung-shaped regions",
                    "status": "UNCERTAIN",
                    "anatomy": "Synthetic image field",
                    "description": "Two artificial bright regions are present in the generated fixture; no clinical interpretation is asserted.",
                }
            ],
            "findings_text": "The synthetic fixture contains artificial chest-like shapes. Visual observations are demonstration content only.",
            "impression": ["Synthetic draft generated solely to exercise workflow behavior."],
            "limitations": [
                "Artificial image; not a clinical radiograph and not evaluated for diagnostic use."
            ],
            "draft_notice": DRAFT_NOTICE,
        }

    def generate_draft(
        self, image_path: Path, prompt: str, prior_issues: list[dict[str, Any]]
    ) -> InferenceResponse:
        self.draft_calls += 1
        if self.fault_profile == "slow_draft":
            time.sleep(2)
        if self.fault_profile in {"malformed_draft_once", "malformed_draft_always"} and (
            self.fault_profile == "malformed_draft_always" or self.draft_calls == 1
        ):
            return self._response("{not valid JSON")
        draft = self._valid_draft()
        if self.fault_profile == "contract_fail_once" and self.draft_calls == 1:
            draft["comparison"] = "TBD"
        return self._response(draft)

    def repair_draft(self, malformed: str, validation_message: str) -> InferenceResponse:
        if self.fault_profile == "malformed_draft_always":
            return self._response("{still invalid")
        return self._response(self._valid_draft())

    def visual_review(
        self, image_path: Path, prompt: str, draft: dict[str, Any]
    ) -> InferenceResponse:
        self.visual_calls += 1
        fail = self.fault_profile == "grounding_fail_always" or (
            self.fault_profile == "grounding_fail_once" and self.visual_calls == 1
        )
        return self._response(
            {
                "verdict": "FAIL" if fail else "PASS",
                "issues": [
                    {
                        "code": "MOCK_VISUAL_MISMATCH",
                        "severity": "BLOCKING",
                        "message": "Injected synthetic visual-consistency failure.",
                    }
                ]
                if fail
                else [],
            }
        )

    def quality_review(
        self, prompt: str, draft: dict[str, Any], policy: dict[str, Any]
    ) -> InferenceResponse:
        self.quality_calls += 1
        fail = self.fault_profile == "quality_fail_always" or (
            self.fault_profile == "quality_fail_once" and self.quality_calls == 1
        )
        return self._response(
            {
                "verdict": "FAIL" if fail else "PASS",
                "issues": [
                    {
                        "code": "MOCK_QUALITY_FAILURE",
                        "severity": "BLOCKING",
                        "message": "Injected synthetic text-quality failure.",
                    }
                ]
                if fail
                else [],
            }
        )

    def capabilities(self) -> dict[str, Any]:
        return {"mode": "MOCK", "fault_profile": self.fault_profile, "synthetic": True}
