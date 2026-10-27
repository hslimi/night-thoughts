from __future__ import annotations

from ..config import Settings
from .base import InferenceProvider
from .mock import MockProvider
from .omlx import OMLXProvider


def get_provider(settings: Settings, fault_profile: str | None = None) -> InferenceProvider:
    if settings.inference_mode == "MOCK":
        return MockProvider(fault_profile or settings_value("FAULT_PROFILE"))
    if fault_profile and fault_profile != "none":
        raise ValueError("Fault injection cannot be enabled in real mode")
    return OMLXProvider(settings)


def settings_value(name: str) -> str | None:
    import os

    return os.getenv(name)
