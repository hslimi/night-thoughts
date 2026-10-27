from __future__ import annotations

import pytest

from nt_imaging.inference.structured import StructuredOutputError, parse_structured
from nt_imaging.schemas import ReviewResult


def test_json_fence_is_supported_but_prose_verdict_is_not() -> None:
    result = parse_structured('```json\n{"verdict":"PASS","issues":[]}\n```', ReviewResult)
    assert result.verdict == "PASS"
    with pytest.raises(StructuredOutputError):
        parse_structured("The verdict is not PASS", ReviewResult)
    with pytest.raises(StructuredOutputError):
        parse_structured('{"verdict":"PASS","issues":[],"extra":true}', ReviewResult)
