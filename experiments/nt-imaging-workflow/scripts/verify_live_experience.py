from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect, sync_playwright

from nt_imaging.controlplane.auth import hash_password
from nt_imaging.controlplane.db import ControlDB

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8002"
OUT = ROOT / "docs" / "images" / "live-operations"
FIXTURE = ROOT / "fixtures" / "synthetic" / "chest_clean.png"


def login(page: Page, password: str) -> None:
    page.goto(BASE, wait_until="networkidle")
    page.locator("#username").fill("live-check")
    page.locator("#password").fill(password)
    page.get_by_role("button", name="Sign in securely").click()
    expect(page.get_by_role("heading", name="Review worklist")).to_be_visible()


def create(page: Page) -> str:
    page.get_by_role("button", name="New synthetic run").click()
    page.locator("#artifact").set_input_files(str(FIXTURE))
    page.get_by_role(
        "checkbox", name="I confirm this is synthetic or authorized de-identified data."
    ).check()
    page.get_by_role("button", name="Create run", exact=True).click()
    page.wait_for_url("**/runs/*")
    return page.url.rsplit("/", 1)[-1]


def decide(page: Page, action: str, note: str = "") -> None:
    page.get_by_role("tab", name="Doctor review", exact=True).click()
    if note:
        page.locator("#decision-note").fill(note)
    page.get_by_role("button", name=action, exact=True).click()
    page.get_by_role("button", name="Confirm decision", exact=True).click()


def no_overflow(page: Page) -> None:
    widths = page.evaluate(
        "() => ({document:document.documentElement.scrollWidth,viewport:innerWidth})"
    )
    assert widths["document"] <= widths["viewport"] + 1, widths


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(24)
    db = ControlDB(ROOT / "var" / "guide-mock" / "controlplane.sqlite3")
    db.upsert_user("live-check", hash_password(password))
    evidence: dict[str, Any] = {"mode": "MOCK / FAULT INJECTION", "checks": [], "screenshots": []}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                headless=True,
            )
            context = browser.new_context(
                viewport={"width": 1440, "height": 900}, accept_downloads=True
            )
            page = context.new_page()
            login(page, password)
            first = create(page)
            expect(page.locator("h1").first).to_have_text("AWAITING HUMAN APPROVAL", timeout=30_000)
            assert page.locator(".timeline-event").count() > 20
            assert page.locator(".compact-record").filter(has_text="DRAFT").count() > 0
            assert page.locator(".compact-record").filter(has_text="VISUAL_CONSISTENCY").count() > 0
            assert page.locator(".compact-record").filter(has_text="TEXT_QUALITY").count() > 0
            evidence["checks"].append({"live_node_and_model_call_events": first})
            page.screenshot(path=str(OUT / "01-live-run-desktop.png"), full_page=False)
            evidence["screenshots"].append("01-live-run-desktop.png")
            decide(page, "Approve export")
            expect(page.locator("h1").first).to_have_text("APPROVED DRAFT EXPORTED", timeout=30_000)
            evidence["checks"].append({"normal_approval": first})

            page.goto(BASE, wait_until="networkidle")
            revision = create(page)
            decide(
                page,
                "Request changes",
                "Clarify the synthetic limitations for live revision evidence",
            )
            expect(page.locator(".run-meta-strip")).to_contain_text("Revision 1", timeout=30_000)
            page.get_by_role("tab", name="Monitor", exact=True).click()
            expect(page.locator(".draft-diff")).to_be_visible()
            page.screenshot(path=str(OUT / "02-live-revision-desktop.png"), full_page=False)
            evidence["screenshots"].append("02-live-revision-desktop.png")
            evidence["checks"].append({"requested_revision": revision})
            decide(page, "Reject draft", "Reject the revised synthetic draft for live evidence")
            expect(page.locator("h1").first).to_have_text("HUMAN REJECTED", timeout=30_000)
            evidence["checks"].append({"rejection": revision})

            page.goto(f"{BASE}/debug", wait_until="networkidle")
            expect(page.get_by_role("heading", name="Execution diagnostics")).to_be_visible()
            page.get_by_role("tab", name="Trace waterfall", exact=True).click()
            expect(page.locator(".trace-waterfall")).to_be_visible()
            page.get_by_role("tab", name="Logs", exact=True).click()
            expect(page.locator(".debug-logs")).to_be_visible()
            page.get_by_role("tab", name="Diagnostics", exact=True).click()
            with page.expect_download() as pending:
                page.get_by_role("link", name="Download sanitized support bundle").click()
            assert pending.value.path() and pending.value.path().stat().st_size > 0
            page.screenshot(path=str(OUT / "03-debug-diagnostics-desktop.png"), full_page=False)
            evidence["screenshots"].append("03-debug-diagnostics-desktop.png")
            evidence["checks"].append({"debug_tabs_and_support_bundle": True})
            context.close()

            mobile = browser.new_context(
                viewport={"width": 390, "height": 844},
                is_mobile=True,
                has_touch=True,
                reduced_motion="reduce",
            )
            phone = mobile.new_page()
            login(phone, password)
            run_id = create(phone)
            expect(phone.locator("h1").first).to_have_text(
                "AWAITING HUMAN APPROVAL", timeout=30_000
            )
            no_overflow(phone)
            phone.screenshot(path=str(OUT / "04-live-review-mobile.png"), full_page=False)
            evidence["screenshots"].append("04-live-review-mobile.png")
            decide(phone, "Approve export")
            expect(phone.locator("h1").first).to_have_text(
                "APPROVED DRAFT EXPORTED", timeout=30_000
            )
            phone.get_by_role("tab", name="Exports", exact=True).click()
            no_overflow(phone)
            animation = (
                phone.locator(".active-node").first.evaluate(
                    "el => getComputedStyle(el).animationName"
                )
                if phone.locator(".active-node").count()
                else "none"
            )
            assert animation == "none"
            evidence["checks"].append({"mobile_approval": run_id, "reduced_motion": True})
            mobile.close()
            browser.close()
    finally:
        with db.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE username='live-check'")
            connection.execute("DELETE FROM users WHERE username='live-check'")
    output = ROOT / "evidence" / "live" / "browser-verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
