from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any

import httpx

from ..config import Settings, get_omlx_api_key
from .base import InferenceResponse


class OMLXProvider:
    def __init__(self, settings: Settings):
        if (
            settings.inference_mode != "REAL"
            or not settings.vision_model
            or not settings.text_model
        ):
            raise ValueError("Real provider requires REAL mode and discovered model IDs")
        if (
            not settings.omlx_base_url.startswith("http://127.0.0.1:")
            and not settings.omlx_base_url.startswith("http://localhost:")
            and not settings.omlx_base_url.startswith("https://")
        ):
            raise ValueError("oMLX HTTP endpoint must use loopback")
        self.settings = settings
        self.client = httpx.Client(
            base_url=settings.omlx_base_url,
            headers={"Authorization": f"Bearer {get_omlx_api_key()}"},
            timeout=httpx.Timeout(settings.model_timeout_seconds),
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
        )

    def _call(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        schema: dict[str, Any] | None = None,
    ) -> InferenceResponse:
        started = time.monotonic()
        response_format: dict[str, Any] = {"type": "json_object"}
        if schema is not None:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "WorkflowStructuredOutput",
                    "strict": True,
                    "schema": schema,
                },
            }
        response = self.client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": max_tokens,
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
                "response_format": response_format,
            },
        )
        if len(response.content) > 2_000_000:
            raise ValueError("Model response exceeds the size limit")
        response.raise_for_status()
        payload = response.json()
        raw = payload["choices"][0]["message"].get("content")
        if isinstance(raw, list):
            raw = "".join(str(item.get("text", "")) for item in raw if isinstance(item, dict))
        if not isinstance(raw, str) or not raw:
            raise ValueError("Model returned no structured text")
        return InferenceResponse(
            raw=raw,
            model_id=str(payload.get("model", model)),
            latency_ms=int((time.monotonic() - started) * 1000),
            usage=payload.get("usage", {}),
        )

    @staticmethod
    def _vision_messages(prompt: str, image_path: Path, extra: str = "") -> list[dict[str, Any]]:
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt + extra},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
                ],
            }
        ]

    def generate_draft(
        self, image_path: Path, prompt: str, prior_issues: list[dict[str, Any]]
    ) -> InferenceResponse:
        from ..schemas import ImagingDraft

        extra = ""
        if prior_issues:
            extra = "\nPrior actionable feedback (formatting only):\n" + "\n".join(
                f"- {issue.get('code', 'REVIEW_ISSUE')}: {str(issue.get('message', ''))[:400]}"
                for issue in prior_issues[-2:]
            )
        return self._call(
            self.settings.vision_model or "",
            self._vision_messages(extra + prompt, image_path),
            1800,
            ImagingDraft.model_json_schema(),
        )

    def repair_draft(self, malformed: str, validation_message: str) -> InferenceResponse:
        from ..schemas import ImagingDraft

        prompt = (
            "Repair only JSON syntax/schema formatting. Do not add clinical content or change uncertainty. Return only ImagingDraft JSON. Validation category: "
            + validation_message[:300]
            + "\nMalformed content:\n"
            + malformed[:20000]
        )
        return self._call(
            self.settings.vision_model or "",
            [{"role": "user", "content": prompt}],
            1800,
            ImagingDraft.model_json_schema(),
        )

    def visual_review(
        self, image_path: Path, prompt: str, draft: dict[str, Any]
    ) -> InferenceResponse:
        from ..schemas import ReviewResult

        return self._call(
            self.settings.vision_model or "",
            self._vision_messages(prompt, image_path, "\nDraft JSON:\n" + json.dumps(draft)),
            800,
            ReviewResult.model_json_schema(),
        )

    def quality_review(
        self, prompt: str, draft: dict[str, Any], policy: dict[str, Any]
    ) -> InferenceResponse:
        from ..schemas import ReviewResult

        content = (
            prompt + "\nPolicy JSON:\n" + json.dumps(policy) + "\nDraft JSON:\n" + json.dumps(draft)
        )
        return self._call(
            self.settings.text_model or "",
            [{"role": "user", "content": content}],
            800,
            ReviewResult.model_json_schema(),
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "mode": "REAL",
            "base_url": self.settings.omlx_base_url,
            "vision_model": self.settings.vision_model,
            "text_model": self.settings.text_model,
            "structured_output": "native_json_schema_with_pydantic_validation",
        }
