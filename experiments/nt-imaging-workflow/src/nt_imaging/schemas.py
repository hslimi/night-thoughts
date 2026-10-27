from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CleanString = str


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Finding(StrictModel):
    label: str = Field(min_length=1, max_length=120)
    status: Literal["PRESENT", "ABSENT", "UNCERTAIN"]
    anatomy: str | None = Field(default=None, max_length=120)
    description: str = Field(min_length=1, max_length=1000)


class ImagingDraft(StrictModel):
    technique: str = Field(min_length=1, max_length=500)
    comparison: str = Field(min_length=1, max_length=500)
    findings: list[Finding] = Field(min_length=1, max_length=20)
    findings_text: str = Field(min_length=1, max_length=6000)
    impression: list[str] = Field(min_length=1, max_length=20)
    limitations: list[str] = Field(min_length=1, max_length=20)
    draft_notice: Literal[
        "AI-ASSISTED DRAFT — RESEARCH AND DEMONSTRATION ONLY — NOT FOR CLINICAL USE"
    ]

    @field_validator("findings_text")
    @classmethod
    def nonempty_text(cls, value: str) -> str:
        if not value:
            raise ValueError("Findings text cannot be empty")
        return value

    @field_validator("impression", "limitations")
    @classmethod
    def bounded_items(cls, value: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 1000 for item in value):
            raise ValueError("List items must be non-empty and at most 1000 characters")
        return value


class ReviewIssue(StrictModel):
    code: str = Field(min_length=1, max_length=80)
    severity: Literal["BLOCKING", "NON_BLOCKING"]
    message: str = Field(min_length=1, max_length=1000)


class ReviewResult(StrictModel):
    verdict: Literal["PASS", "FAIL"]
    issues: list[ReviewIssue] = Field(max_length=30)

    @model_validator(mode="after")
    def blocking_issues_fail(self) -> ReviewResult:
        if self.verdict == "PASS" and any(i.severity == "BLOCKING" for i in self.issues):
            raise ValueError("PASS cannot contain blocking issues")
        return self


class HumanDecision(StrictModel):
    decision: Literal["APPROVE", "REJECT", "REQUEST_CHANGES"]
    reviewer_display_name: str = Field(min_length=1, max_length=80)
    note: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def rejection_note(self) -> HumanDecision:
        if self.decision in {"REJECT", "REQUEST_CHANGES"} and not self.note:
            raise ValueError("A note is required for rejection or change requests")
        return self


class WorkflowError(StrictModel):
    code: str
    message: str
    retryable: bool
    details: dict[str, Any] = Field(default_factory=dict)


class IngestDeclaration(StrictModel):
    modality: Literal["XR"] | None = None
    synthetic_or_authorized: Literal[True]


def safe_error(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return WorkflowError(code=code, message=message, retryable=retryable).model_dump()


def contains_placeholder(value: str) -> bool:
    return bool(
        re.search(r"(?:\bTBD\b|\bTODO\b|<placeholder>|\[insert|\bN/?A\b)", value, re.IGNORECASE)
    )
