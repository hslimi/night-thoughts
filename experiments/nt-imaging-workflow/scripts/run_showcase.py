from __future__ import annotations

import argparse
import json
import secrets
import time
from pathlib import Path
from typing import Any

import httpx

from nt_imaging.controlplane.auth import hash_password
from nt_imaging.controlplane.db import ControlDB

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "synthetic"
FINAL_STATUSES = {
    "AWAITING_HUMAN_APPROVAL",
    "APPROVED_DRAFT_EXPORTED",
    "HUMAN_REJECTED",
    "NEEDS_HUMAN_REVIEW",
    "IMAGE_PREPARATION_FAILED",
    "MODEL_OUTPUT_INVALID",
    "QUARANTINED",
    "CANCELLED",
    "FAILED",
}


class Showcase:
    def __init__(self, base_url: str, data_root: Path, mode: str):
        self.base_url = base_url.rstrip("/")
        self.data_root = data_root
        self.mode = mode
        self.db = ControlDB(data_root / "controlplane.sqlite3")
        self.username = "showcase-runner"
        self.password = secrets.token_urlsafe(24)
        self.db.upsert_user(self.username, hash_password(self.password))
        self.client = httpx.Client(timeout=30)
        self.cookies = ""
        self.csrf = ""
        self.results: list[dict[str, Any]] = []

    def close(self) -> None:
        self.client.close()
        with self.db.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE username=?", (self.username,))
            connection.execute("DELETE FROM users WHERE username=?", (self.username,))

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = dict(kwargs.pop("headers", {}))
        if self.cookies:
            headers["Cookie"] = self.cookies
        if method != "GET" and path != "/api/v1/auth/login":
            headers["X-CSRF-Token"] = self.csrf
        return self.client.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)

    def login(self) -> None:
        response = self.client.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": self.username, "password": self.password},
        )
        response.raise_for_status()
        session = response.cookies.get("__Host-nt_session")
        self.csrf = response.cookies.get("__Host-nt_csrf") or ""
        assert session and self.csrf, "The local portal did not issue its expected session cookies"
        self.cookies = f"__Host-nt_session={session}; __Host-nt_csrf={self.csrf}"

    def detail(self, run_id: str) -> dict[str, Any]:
        response = self.request("GET", f"/api/v1/runs/{run_id}")
        response.raise_for_status()
        return response.json()

    def wait(self, run_id: str, timeout: float = 360) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = self.detail(run_id)
            if state["status"] in FINAL_STATUSES:
                return state
            time.sleep(0.25)
        raise TimeoutError(f"Run {run_id} did not reach a reviewable or terminal state")

    def create(
        self,
        scenario: str,
        fixture: str = "chest_clean.png",
        *,
        fault_profile: str | None = None,
        wait: bool = True,
    ) -> dict[str, Any]:
        path = FIXTURES / fixture
        media_type = "application/dicom" if path.suffix == ".dcm" else "image/png"
        data = {"modality": "XR", "confirmed": "true", "demonstration_scenario": scenario}
        if fault_profile:
            data["fault_profile"] = fault_profile
        response = self.request(
            "POST",
            "/api/v1/runs",
            data=data,
            files={"file": (path.name, path.read_bytes(), media_type)},
        )
        assert response.status_code == 202, (scenario, response.status_code, response.text)
        run_id = response.json()["run_id"]
        state = self.wait(run_id) if wait else self.detail(run_id)
        return {"scenario": scenario, "fixture": fixture, "run_id": run_id, "state": state}

    def decide(self, run_id: str, decision: str, note: str = "") -> dict[str, Any]:
        previous_revision = self.detail(run_id).get("revision", 0)
        response = self.request(
            "POST",
            f"/api/v1/runs/{run_id}/decision",
            json={"decision": decision, "note": note},
        )
        assert response.status_code == 202, (decision, response.status_code, response.text)
        deadline = time.monotonic() + 360
        while time.monotonic() < deadline:
            state = self.detail(run_id)
            finished = state.get("job_status") in {"COMPLETED", "FAILED", "CANCELLED"}
            interrupted = state.get("job_status") == "INTERRUPTED"
            if decision == "REQUEST_CHANGES":
                if (finished and state["status"] == "NEEDS_HUMAN_REVIEW") or (
                    interrupted and state.get("revision", 0) > previous_revision
                ):
                    return state
            elif finished and state["status"] != "AWAITING_HUMAN_APPROVAL":
                return state
            time.sleep(0.25)
        raise TimeoutError(f"Decision {decision} did not complete for run {run_id}")

    def exports(self, run_id: str) -> dict[str, Any]:
        response = self.request("GET", f"/api/v1/runs/{run_id}/exports")
        response.raise_for_status()
        return response.json()

    def save(self, item: dict[str, Any], expected: str, exportable: bool = False) -> None:
        state = item["state"]
        assert state["status"] == expected, (item["scenario"], state["status"], state.get("error"))
        exports = self.exports(item["run_id"])
        assert exports["eligible"] is exportable, (item["scenario"], exports)
        inspector = self.request("GET", f"/api/v1/runs/{item['run_id']}/graph-inspector")
        inspector.raise_for_status()
        graph = inspector.json()
        self.results.append(
            {
                "scenario": item["scenario"],
                "fixture_id": item["fixture"],
                "run_id": item["run_id"],
                "thread_id": state["thread_id"],
                "status": state["status"],
                "inference_mode": state["inference_mode"],
                "fault_profile": state.get("fault_profile"),
                "source_sha256": state.get("source_sha256"),
                "prepared_sha256": state.get("prepared_sha256"),
                "preparation_policy_version": state.get("preparation_policy_version"),
                "readiness_receipt_id": state.get("readiness_receipt_id"),
                "attempt": state.get("attempt"),
                "revision": state.get("revision"),
                "model_call_receipts": graph["model_calls"],
                "export_eligible": exports["eligible"],
                "export_count": len(exports["exports"]),
            }
        )
        print(
            json.dumps({"scenario": item["scenario"], "status": expected, "run_id": item["run_id"]})
        )

    def cancel(self, item: dict[str, Any]) -> None:
        response = self.request("POST", f"/api/v1/runs/{item['run_id']}/cancel")
        assert response.status_code == 200, response.text
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            item["state"] = self.detail(item["run_id"])
            if item["state"].get("job_status") == "CANCELLED":
                return
            time.sleep(0.1)
        raise TimeoutError(f"Run {item['run_id']} did not release its cancelled worker job")

    def run_mock(self) -> None:
        scenarios = [
            ("approved_png", "chest_clean.png", None, "APPROVE", "APPROVED_DRAFT_EXPORTED"),
            ("approved_mono1", "chest_mono1.dcm", None, "APPROVE", "APPROVED_DRAFT_EXPORTED"),
            ("rejected", "chest_clean.png", None, "REJECT", "HUMAN_REJECTED"),
            ("phi_quarantine", "chest_unexpected_text.png", None, None, "QUARANTINED"),
            ("unsupported_modality", "unsupported_ct.dcm", None, None, "NEEDS_HUMAN_REVIEW"),
            ("corrupt_upload", "mismatch.png", None, None, "NEEDS_HUMAN_REVIEW"),
            ("preparation_failure", "uniform.png", None, None, "IMAGE_PREPARATION_FAILED"),
            ("pixel_limit", "too_many_pixels.png", None, None, "NEEDS_HUMAN_REVIEW"),
            (
                "derived_safety_fault",
                "chest_clean.png",
                "derived_phi_block",
                None,
                "IMAGE_PREPARATION_FAILED",
            ),
            (
                "malformed_repaired",
                "chest_clean.png",
                "malformed_draft_once",
                "APPROVE",
                "APPROVED_DRAFT_EXPORTED",
            ),
            (
                "malformed_persistent",
                "chest_clean.png",
                "malformed_draft_always",
                None,
                "MODEL_OUTPUT_INVALID",
            ),
            (
                "contract_retry_success",
                "chest_clean.png",
                "contract_fail_once",
                "APPROVE",
                "APPROVED_DRAFT_EXPORTED",
            ),
            (
                "grounding_retry_success",
                "chest_clean.png",
                "grounding_fail_once",
                "APPROVE",
                "APPROVED_DRAFT_EXPORTED",
            ),
            (
                "grounding_retry_exhausted",
                "chest_clean.png",
                "grounding_fail_always",
                None,
                "NEEDS_HUMAN_REVIEW",
            ),
            (
                "quality_retry_success",
                "chest_clean.png",
                "quality_fail_once",
                "APPROVE",
                "APPROVED_DRAFT_EXPORTED",
            ),
            (
                "quality_retry_exhausted",
                "chest_clean.png",
                "quality_fail_always",
                None,
                "NEEDS_HUMAN_REVIEW",
            ),
            ("model_timeout", "chest_clean.png", "model_timeout", None, "FAILED"),
            ("model_unavailable", "chest_clean.png", "model_unavailable", None, "FAILED"),
        ]
        for scenario, fixture, profile, decision, expected in scenarios:
            item = self.create(scenario, fixture, fault_profile=profile)
            if decision:
                note = "Synthetic showcase rejection" if decision == "REJECT" else ""
                item["state"] = self.decide(item["run_id"], decision, note)
            self.save(item, expected, expected == "APPROVED_DRAFT_EXPORTED")

        revision = self.create("revision_then_approval")
        revision["state"] = self.decide(
            revision["run_id"], "REQUEST_CHANGES", "Clarify synthetic limitations"
        )
        assert revision["state"]["revision"] == 1
        revision["state"] = self.decide(revision["run_id"], "APPROVE")
        self.save(revision, "APPROVED_DRAFT_EXPORTED", True)

        exhausted = self.create("revision_limit_exhaustion")
        for index in range(3):
            exhausted["state"] = self.decide(
                exhausted["run_id"], "REQUEST_CHANGES", f"Synthetic revision request {index + 1}"
            )
        self.save(exhausted, "NEEDS_HUMAN_REVIEW")

        timeout = self.create("technical_retry_original", fault_profile="model_timeout")
        response = self.request("POST", f"/api/v1/runs/{timeout['run_id']}/retry")
        assert response.status_code == 202, response.text
        retried_id = response.json()["run_id"]
        retried = {
            "scenario": "technical_retry_success",
            "fixture": "chest_clean.png",
            "run_id": retried_id,
            "state": self.decide(retried_id, "APPROVE")
            if self.wait(retried_id)["status"] == "AWAITING_HUMAN_APPROVAL"
            else self.wait(retried_id),
        }
        self.save(retried, "APPROVED_DRAFT_EXPORTED", True)

        active = self.create("cancel_active", fault_profile="slow_draft", wait=False)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            current = self.detail(active["run_id"])
            if (
                current.get("job_status") == "RUNNING"
                and current.get("current_node") == "derived_image_safety_check"
            ):
                break
            time.sleep(0.1)
        else:
            raise AssertionError("Slow run did not enter active drafting")
        queued = self.create("cancel_queued", wait=False)
        assert queued["state"]["status"] == "QUEUED"
        self.cancel(queued)
        self.save(queued, "CANCELLED")
        self.cancel(active)
        self.save(active, "CANCELLED")

        saturation = self.create("queue_saturation_active", fault_profile="slow_draft", wait=False)
        queued_items = []
        for index in range(7):
            queued_items.append(self.create(f"queue_saturation_{index + 1}", wait=False))
        path = FIXTURES / "chest_clean.png"
        rejected = self.request(
            "POST",
            "/api/v1/runs",
            data={
                "modality": "XR",
                "confirmed": "true",
                "demonstration_scenario": "queue_full_rejected",
            },
            files={"file": (path.name, path.read_bytes(), "image/png")},
        )
        assert rejected.status_code == 429, rejected.text
        for item in queued_items:
            self.cancel(item)
            self.save(item, "CANCELLED")
        self.cancel(saturation)
        self.save(saturation, "CANCELLED")

    def run_real(self) -> None:
        scenarios = [
            ("real_png_awaiting", "chest_clean.png", None, "AWAITING_HUMAN_APPROVAL"),
            ("real_mono1_approved", "chest_mono1.dcm", "APPROVE", "APPROVED_DRAFT_EXPORTED"),
            (
                "real_signed_voi_revision",
                "chest_signed_voi.dcm",
                "REQUEST_CHANGES",
                "APPROVED_DRAFT_EXPORTED",
            ),
            ("real_rejected", "chest_clean.png", "REJECT", "HUMAN_REJECTED"),
            ("real_dx_approved", "chest_dx.dcm", "APPROVE", "APPROVED_DRAFT_EXPORTED"),
            ("real_png_approved", "chest_clean.png", "APPROVE", "APPROVED_DRAFT_EXPORTED"),
        ]
        for scenario, fixture, decision, expected in scenarios:
            item = self.create(scenario, fixture)
            if decision == "REQUEST_CHANGES":
                item["state"] = self.decide(
                    item["run_id"], decision, "Clarify limitations for this synthetic revision"
                )
                item["state"] = self.decide(item["run_id"], "APPROVE")
            elif decision:
                item["state"] = self.decide(
                    item["run_id"],
                    decision,
                    "Synthetic REAL rejection" if decision == "REJECT" else "",
                )
            self.save(item, expected, expected == "APPROVED_DRAFT_EXPORTED")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["REAL", "MOCK"], required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    showcase = Showcase(args.base_url, args.data_root.resolve(), args.mode)
    try:
        showcase.login()
        if args.mode == "REAL":
            showcase.run_real()
        else:
            showcase.run_mock()
    finally:
        showcase.close()
    report = {
        "label": "REAL oMLX inference"
        if args.mode == "REAL"
        else "MOCK / FAULT INJECTION — not model-quality evidence",
        "mode": args.mode,
        "base_url": args.base_url,
        "fixture_provenance": "Project-generated deterministic artificial pixels; no patient data; see fixtures/README.md",
        "run_count": len(showcase.results),
        "runs": showcase.results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {"mode": args.mode, "run_count": len(showcase.results), "output": str(args.output)}
        )
    )


if __name__ == "__main__":
    main()
