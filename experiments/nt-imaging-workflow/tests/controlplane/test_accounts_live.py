from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nt_imaging.config import Settings
from nt_imaging.controlplane.accounts import upsert_account
from nt_imaging.controlplane.api import db

from .conftest import csrf


def test_account_reset_without_service_restart(
    doctor_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NT_DOCTOR_USERNAME", "doctor")
    monkeypatch.setenv("NT_DOCTOR_PASSWORD", "new-password-123")
    with db.connect() as connection:
        before = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    assert before >= 1
    invalidated = upsert_account(reset=True, data_root=Settings.from_env().data_root)
    assert invalidated == before
    assert doctor_client.get("/api/v1/auth/me").status_code == 401
    response = doctor_client.post(
        "/api/v1/auth/login", json={"username": "doctor", "password": "new-password-123"}
    )
    assert response.status_code == 200
    assert doctor_client.get("/api/v1/auth/me").status_code == 200
    assert doctor_client.post("/api/v1/auth/logout", headers=csrf(doctor_client)).status_code == 200


def test_account_cli_rejects_obsolete_data_root() -> None:
    with pytest.raises(SystemExit, match="obsolete installation"):
        upsert_account(
            reset=True,
            data_root=Path("/Users/night-thoughts/healthcare/nt-imaging-workflow/var"),
        )
