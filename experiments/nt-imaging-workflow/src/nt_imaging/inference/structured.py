from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(ValueError):
    pass


def parse_structured(raw: str, schema: type[T]) -> T:
    if len(raw) > 200_000:
        raise StructuredOutputError("Structured output exceeds the size limit")
    text = raw.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        value = json.loads(text)
        return schema.model_validate(value)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise StructuredOutputError(
            "Model output did not match the required structured schema"
        ) from exc
