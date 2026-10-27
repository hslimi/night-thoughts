from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REAL_REQUESTED = os.getenv("RUN_REAL_TESTS") == "1"
TEST_VAR = ROOT / "var" / ("real-pytest" if REAL_REQUESTED else "pytest")
shutil.rmtree(TEST_VAR, ignore_errors=True)
os.environ["INFERENCE_MODE"] = "REAL" if REAL_REQUESTED else "MOCK"
os.environ["DATA_ROOT"] = str(TEST_VAR)
os.environ["MAX_ATTEMPTS"] = "2"
os.environ["MAX_TOTAL_MODEL_CALLS"] = "8"


@pytest.fixture
def fixture_dir() -> Path:
    return ROOT / "fixtures" / "synthetic"


@pytest.fixture
def clean_fixture(fixture_dir: Path) -> Path:
    return fixture_dir / "chest_clean.png"
