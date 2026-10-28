from __future__ import annotations

import secrets
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from nt_imaging.controlplane.auth import hash_password
from nt_imaging.controlplane.db import ControlDB

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "doctor-pipeline-user-guide"
BASE = "http://127.0.0.1:8003"


def main() -> None:
    password = secrets.token_urlsafe(24)
    db = ControlDB(ROOT / "var" / "real-showcase" / "controlplane.sqlite3")
    db.upsert_user("demo-reviewer", hash_password(password))
    real = __import__("json").loads((ROOT / "evidence/showcase/real-runs.json").read_text())
    approved = next(
        item["run_id"] for item in real["runs"] if item["scenario"] == "real_png_approved"
    )
    revised = next(
        item["run_id"] for item in real["runs"] if item["scenario"] == "real_png_awaiting"
    )
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                headless=True,
            )
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(BASE, wait_until="networkidle")
            page.locator("#username").fill("demo-reviewer")
            page.locator("#password").fill(password)
            page.get_by_role("button", name="Sign in securely").click()
            expect(page.get_by_role("heading", name="Review worklist")).to_be_visible()
            page.get_by_role("button", name="New synthetic run").click()
            page.locator("#artifact").set_input_files(
                str(ROOT / "fixtures/synthetic/chest_clean.png")
            )
            page.get_by_role(
                "checkbox", name="I confirm this is synthetic or authorized de-identified data."
            ).check()
            page.get_by_role("button", name="Create run", exact=True).click()
            page.wait_for_url("**/runs/*")
            expect(page.locator("h1").first).to_have_text("AWAITING HUMAN APPROVAL", timeout=60_000)
            page.get_by_role("tab", name="Doctor review", exact=True).click()
            page.wait_for_function(
                "[...document.images].filter(i => i.offsetParent !== null).every(i => i.complete && i.naturalWidth > 0)"
            )
            page.screenshot(path=str(OUT / "06-awaiting-doctor-review.png"), full_page=False)
            page.locator("#decision-note").fill(
                "Clarify limitations for the revised synthetic evidence draft"
            )
            page.get_by_role("button", name="Request changes", exact=True).click()
            page.get_by_role("button", name="Confirm decision", exact=True).click()
            expect(page.locator(".run-meta-strip")).to_contain_text("Revision 1", timeout=90_000)
            expect(page.locator("h1").first).to_have_text("AWAITING HUMAN APPROVAL", timeout=90_000)
            page.wait_for_function(
                "[...document.images].filter(i => i.offsetParent !== null).every(i => i.complete && i.naturalWidth > 0)"
            )
            page.screenshot(path=str(OUT / "12-revised-draft.png"), full_page=False)

            page.goto(f"{BASE}/runs/{approved}", wait_until="networkidle")
            page.get_by_role("tab", name="Audit & provenance", exact=True).click()
            expect(page.locator(".audit-event").first).to_be_visible(timeout=20_000)
            page.screenshot(path=str(OUT / "18-audit-timeline.png"), full_page=False)
            page.goto(f"{BASE}/runs/{revised}", wait_until="networkidle")
            page.get_by_role("tab", name="Local graph", exact=True).click()
            expect(page.locator(".receipt").first).to_be_visible(timeout=20_000)
            page.screenshot(path=str(OUT / "32-local-graph-inspector.png"), full_page=False)
            browser.close()
    finally:
        with db.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE username='demo-reviewer'")
            connection.execute("DELETE FROM users WHERE username='demo-reviewer'")


if __name__ == "__main__":
    main()
