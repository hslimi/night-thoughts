from __future__ import annotations

from pathlib import Path

import pytest

from nt_imaging.artifacts import ArtifactError, ArtifactStore, validate_id
from nt_imaging.config import Settings


@pytest.mark.parametrize("value", ["../../etc/passwd", "/etc/passwd", "file.png", "x;rm", ""])
def test_unsafe_ids_rejected(value: str) -> None:
    with pytest.raises(ArtifactError):
        validate_id(value)


def test_symlink_source_rejected(tmp_path: Path, clean_fixture: Path) -> None:
    link = tmp_path / "link.png"
    link.symlink_to(clean_fixture)
    store = ArtifactStore(Settings.from_env().data_root)
    with pytest.raises(ArtifactError):
        store.copy_source(link, "123e4567-e89b-12d3-a456-426614174000", "a" * 32)


def test_loopback_is_mandatory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DASHBOARD_HOST", "0.0.0.0")
    with pytest.raises(ValueError):
        Settings.from_env()
