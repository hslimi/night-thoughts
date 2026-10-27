from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    inference_mode: str
    workflow_version: str
    max_attempts: int
    max_total_model_calls: int
    omlx_base_url: str
    vision_model: str | None
    text_model: str | None
    data_root: Path
    max_upload_bytes: int
    max_decoded_pixels: int
    model_timeout_seconds: float
    dashboard_host: str
    dashboard_port: int

    @classmethod
    def from_env(cls) -> Settings:
        mode = os.getenv("INFERENCE_MODE", "REAL").upper()
        if mode not in {"REAL", "MOCK"}:
            raise ConfigurationError("INFERENCE_MODE must be REAL or MOCK")
        vision = os.getenv("OMLX_VISION_MODEL") or None
        text = os.getenv("OMLX_TEXT_MODEL") or None
        if mode == "REAL" and (not vision or not text):
            raise ConfigurationError("Real mode requires OMLX_VISION_MODEL and OMLX_TEXT_MODEL")
        fault = os.getenv("FAULT_PROFILE")
        if mode == "REAL" and fault and fault != "none":
            raise ConfigurationError("Fault profiles are allowed only in explicit mock mode")
        host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
        if host != "127.0.0.1":
            raise ConfigurationError("The demonstration dashboard must bind to 127.0.0.1")
        root = Path(os.getenv("DATA_ROOT", "./var")).expanduser().resolve()
        return cls(
            inference_mode=mode,
            workflow_version=os.getenv("WORKFLOW_VERSION", "nt-cxr-draft-v1"),
            max_attempts=int(os.getenv("MAX_ATTEMPTS", "2")),
            max_total_model_calls=int(os.getenv("MAX_TOTAL_MODEL_CALLS", "8")),
            omlx_base_url=os.getenv("OMLX_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/"),
            vision_model=vision,
            text_model=text,
            data_root=root,
            max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", "26214400")),
            max_decoded_pixels=int(os.getenv("MAX_DECODED_PIXELS", "25000000")),
            model_timeout_seconds=float(os.getenv("MODEL_TIMEOUT_SECONDS", "300")),
            dashboard_host=host,
            dashboard_port=int(os.getenv("DASHBOARD_PORT", "8001")),
        )

    def ensure_directories(self) -> None:
        for child in ("incoming", "quarantine", "artifacts", "runs", "exports", "logs"):
            (self.data_root / child).mkdir(parents=True, exist_ok=True, mode=0o700)


def get_omlx_api_key() -> str:
    import json

    key = os.getenv("OMLX_API_KEY")
    if key:
        return key
    path = Path.home() / ".omlx" / "settings.json"
    try:
        settings = json.loads(path.read_text())
        key = settings["auth"]["api_key"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ConfigurationError(
            "Set OMLX_API_KEY or configure the existing oMLX inference API key"
        ) from exc
    if not isinstance(key, str) or not key:
        raise ConfigurationError("No oMLX inference API key is available")
    return key
