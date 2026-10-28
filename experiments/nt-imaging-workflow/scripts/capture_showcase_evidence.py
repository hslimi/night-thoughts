from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, expect, sync_playwright

from nt_imaging.controlplane.auth import hash_password
from nt_imaging.controlplane.db import ControlDB

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "doctor-pipeline-user-guide"
REAL_BASE = "http://127.0.0.1:8003"
MOCK_BASE = "http://127.0.0.1:8002"


def credentials(data_root: Path) -> str:
    password = secrets.token_urlsafe(24)
    ControlDB(data_root / "controlplane.sqlite3").upsert_user(
        "demo-reviewer", hash_password(password)
    )
    return password


def login(page: Page, base: str, password: str) -> None:
    page.goto(base, wait_until="networkidle")
    page.locator("#username").fill("demo-reviewer")
    page.locator("#password").fill(password)
    page.get_by_role("button", name="Sign in securely").click()
    expect(page.get_by_role("heading", name="Review worklist")).to_be_visible(timeout=20_000)


def capture(page: Page, name: str, records: list[dict[str, Any]], mode: str) -> None:
    path = OUT / name
    page.screenshot(path=str(path), full_page=False)
    records.append(
        {
            "file": name,
            "viewport": page.viewport_size,
            "mode": mode,
            "full_page": False,
        }
    )


def open_run(page: Page, base: str, run_id: str, tab: str = "Monitor") -> None:
    page.goto(f"{base}/runs/{run_id}", wait_until="networkidle")
    expect(page.locator("h1").first).to_be_visible(timeout=20_000)
    if tab != "Monitor":
        page.get_by_role("tab", name=tab, exact=True).click()


def create_run(page: Page) -> str:
    page.goto(REAL_BASE, wait_until="networkidle")
    page.get_by_role("button", name="New synthetic run").click()
    page.locator("#artifact").set_input_files(
        str(ROOT / "fixtures" / "synthetic" / "chest_clean.png")
    )
    page.get_by_role(
        "checkbox", name="I confirm this is synthetic or authorized de-identified data."
    ).check()
    page.get_by_role("button", name="Create run", exact=True).click()
    page.wait_for_url("**/runs/*")
    expect(page.locator("h1").first).to_have_text("AWAITING HUMAN APPROVAL", timeout=60_000)
    return page.url.rsplit("/", 1)[-1]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    real_password = credentials(ROOT / "var" / "real-showcase")
    mock_password = credentials(ROOT / "var" / "guide-mock")
    real_report = json.loads((ROOT / "evidence" / "showcase" / "real-runs.json").read_text())
    mock_report = json.loads((ROOT / "evidence" / "showcase" / "mock-runs.json").read_text())
    real_ids = {item["scenario"]: item["run_id"] for item in real_report["runs"]}
    mock_ids = {item["scenario"]: item["run_id"] for item in mock_report["runs"]}
    records: list[dict[str, Any]] = []
    omissions: list[dict[str, str]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
        )
        desktop = browser.new_context(viewport={"width": 1440, "height": 900})
        page = desktop.new_page()
        page.goto(REAL_BASE, wait_until="networkidle")
        expect(page.get_by_role("heading", name="Welcome back")).to_be_visible()
        capture(page, "01-login-desktop.png", records, "REAL")
        login(page, REAL_BASE, real_password)
        capture(page, "02-dashboard-desktop.png", records, "REAL")
        page.get_by_role("button", name="New synthetic run").click()
        page.locator("#artifact").set_input_files(
            str(ROOT / "fixtures" / "synthetic" / "chest_clean.png")
        )
        page.get_by_role(
            "checkbox", name="I confirm this is synthetic or authorized de-identified data."
        ).check()
        capture(page, "03-new-run-upload.png", records, "REAL")
        page.keyboard.press("Escape")

        awaiting = real_ids["real_png_awaiting"]
        open_run(page, REAL_BASE, awaiting)
        capture(page, "04-run-monitoring.png", records, "REAL")
        page.locator(".workflow-steps").scroll_into_view_if_needed()
        capture(page, "05-gate-timeline.png", records, "REAL")
        open_run(page, REAL_BASE, awaiting, "Doctor review")
        capture(page, "06-awaiting-doctor-review.png", records, "REAL")
        page.locator(".preparation-panel").scroll_into_view_if_needed()
        capture(page, "07-review-workspace-desktop.png", records, "REAL")
        capture(page, "31-source-prepared-comparison.png", records, "REAL")
        page.locator("#decision-note").fill("Clarify limitations for the synthetic revised draft")
        page.get_by_role("button", name="Request changes", exact=True).click()
        capture(page, "11-request-changes.png", records, "REAL")
        page.get_by_role("button", name="Go back", exact=True).click()

        mobile = browser.new_context(
            viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
        )
        phone = mobile.new_page()
        phone.goto(REAL_BASE, wait_until="networkidle")
        capture(phone, "21-login-mobile.png", records, "REAL")
        login(phone, REAL_BASE, real_password)
        phone.get_by_role("button", name="Open navigation").click()
        capture(phone, "22-navigation-mobile.png", records, "REAL")
        phone.get_by_role("button", name="Close navigation").click()
        capture(phone, "23-dashboard-mobile.png", records, "REAL")
        open_run(phone, REAL_BASE, awaiting)
        capture(phone, "24-run-monitoring-mobile.png", records, "REAL")
        open_run(phone, REAL_BASE, awaiting, "Doctor review")
        phone.locator("#decision-note").fill("Clarify limitations for the synthetic revised draft")
        phone.get_by_role("button", name="Request changes", exact=True).click()
        capture(phone, "29-request-changes-mobile.png", records, "REAL")
        phone.get_by_role("button", name="Confirm decision", exact=True).click()
        expect(phone.locator(".run-meta-strip")).to_contain_text("Revision 1", timeout=90_000)
        expect(phone.locator("h1").first).to_have_text("AWAITING HUMAN APPROVAL", timeout=90_000)

        open_run(page, REAL_BASE, awaiting, "Doctor review")
        expect(page.locator(".run-meta-strip")).to_contain_text("Revision 1")
        capture(page, "12-revised-draft.png", records, "REAL")
        open_run(page, REAL_BASE, awaiting, "Local graph")
        capture(page, "32-local-graph-inspector.png", records, "REAL")

        open_run(phone, REAL_BASE, awaiting, "Doctor review")
        phone.locator(".image-panel").scroll_into_view_if_needed()
        capture(phone, "25-image-review-mobile.png", records, "REAL")
        phone.locator(".draft-panel").scroll_into_view_if_needed()
        capture(phone, "26-draft-review-mobile.png", records, "REAL")
        phone.get_by_role("button", name="Approve export", exact=True).click()
        capture(phone, "27-approve-mobile.png", records, "REAL")
        phone.get_by_role("button", name="Confirm decision", exact=True).click()
        expect(phone.locator("h1").first).to_have_text("APPROVED DRAFT EXPORTED", timeout=60_000)
        phone.get_by_role("tab", name="Exports", exact=True).click()
        capture(phone, "30-export-mobile.png", records, "REAL")

        approved = create_run(page)
        open_run(page, REAL_BASE, approved, "Doctor review")
        page.get_by_role("button", name="Approve export", exact=True).click()
        capture(page, "08-approve-confirmation.png", records, "REAL")
        page.get_by_role("button", name="Confirm decision", exact=True).click()
        expect(page.locator("h1").first).to_have_text("APPROVED DRAFT EXPORTED", timeout=60_000)
        page.get_by_role("tab", name="Exports", exact=True).click()
        capture(page, "09-approved-export.png", records, "REAL")
        page.get_by_role("tab", name="Audit & provenance", exact=True).click()
        capture(page, "18-audit-timeline.png", records, "REAL")

        rejected = create_run(page)
        open_run(page, REAL_BASE, rejected, "Doctor review")
        page.locator("#decision-note").fill("Synthetic rejection for the evidence scenario")
        page.get_by_role("button", name="Reject draft", exact=True).click()
        capture(page, "10-reject-dialog.png", records, "REAL")
        page.get_by_role("button", name="Go back", exact=True).click()
        open_run(phone, REAL_BASE, rejected, "Doctor review")
        phone.locator("#decision-note").fill("Synthetic rejection for the evidence scenario")
        phone.get_by_role("button", name="Reject draft", exact=True).click()
        capture(phone, "28-reject-mobile.png", records, "REAL")
        phone.get_by_role("button", name="Confirm decision", exact=True).click()
        expect(phone.locator("h1").first).to_have_text("HUMAN REJECTED", timeout=60_000)

        phone.close()
        mobile.close()
        page.goto(REAL_BASE, wait_until="networkidle")
        with ControlDB(
            ROOT / "var" / "real-showcase" / "controlplane.sqlite3"
        ).connect() as connection:
            connection.execute("DELETE FROM sessions WHERE username='demo-reviewer'")
        expect(page.get_by_text("Your session expired. Sign in again to continue.")).to_be_visible(
            timeout=15_000
        )
        capture(page, "19-session-expired.png", records, "REAL")
        desktop.close()

        fault = browser.new_context(viewport={"width": 1440, "height": 900})
        mock = fault.new_page()
        login(mock, MOCK_BASE, mock_password)
        for name, scenario in [
            ("13-phi-quarantine.png", "phi_quarantine"),
            ("14-unsupported-modality.png", "unsupported_modality"),
            ("15-grounding-retry.png", "grounding_retry_success"),
            ("16-retry-exhausted-no-export.png", "grounding_retry_exhausted"),
            ("17-cancelled-run.png", "cancel_active"),
            ("33-preparation-failure.png", "preparation_failure"),
            ("34-model-service-failure.png", "model_timeout"),
        ]:
            open_run(mock, MOCK_BASE, mock_ids[scenario])
            capture(mock, name, records, "MOCK / FAULT INJECTION")
        fault.close()

        public = browser.new_context(viewport={"width": 1440, "height": 900})
        try:
            public_page = public.new_page()
            public_page.goto(
                "https://imaging.nightthoughts.dev", wait_until="networkidle", timeout=30_000
            )
            expect(public_page.get_by_role("heading", name="Welcome back")).to_be_visible()
            capture(public_page, "20-public-login.png", records, "PUBLIC DEPLOYMENT")
        except PlaywrightError as exc:  # screenshot omissions are reported, never substituted
            omissions.append({"file": "20-public-login.png", "reason": type(exc).__name__})
        public.close()
        browser.close()

    for data_root in (ROOT / "var" / "real-showcase", ROOT / "var" / "guide-mock"):
        with ControlDB(data_root / "controlplane.sqlite3").connect() as connection:
            connection.execute("DELETE FROM sessions WHERE username='demo-reviewer'")
            connection.execute("DELETE FROM users WHERE username='demo-reviewer'")
    manifest = {"screenshots": records, "omissions": omissions}
    (OUT / "capture-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"captured": len(records), "omissions": omissions}))


if __name__ == "__main__":
    main()
