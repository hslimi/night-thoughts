from __future__ import annotations

import json
import secrets
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from nt_imaging.controlplane.auth import hash_password
from nt_imaging.controlplane.db import ControlDB

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "live-operations"
BASE = "http://127.0.0.1:8003"
RUN_ID = "31cdec99-4283-435a-9765-1cc163ae0b82"


def login(page, password: str) -> None:
    page.goto(BASE, wait_until="networkidle")
    page.locator("#username").fill("real-live")
    page.locator("#password").fill(password)
    page.get_by_role("button", name="Sign in securely").click()
    expect(page.get_by_role("heading", name="Review worklist")).to_be_visible()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(24)
    db = ControlDB(ROOT / "var" / "real-showcase" / "controlplane.sqlite3")
    db.upsert_user("real-live", hash_password(password))
    result = {"mode": "REAL", "screenshots": [], "video": None}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                headless=True,
            )
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            login(page, password)
            page.screenshot(path=str(OUT / "05-real-worklist.png"), full_page=False)
            result["screenshots"].append("05-real-worklist.png")
            page.goto(f"{BASE}/runs/{RUN_ID}", wait_until="networkidle")
            expect(page.locator("h1").first).to_have_text("AWAITING HUMAN APPROVAL")
            assert page.locator(".timeline-event").count() > 20
            page.screenshot(path=str(OUT / "06-real-live-workflow.png"), full_page=False)
            result["screenshots"].append("06-real-live-workflow.png")
            page.goto(f"{BASE}/debug", wait_until="networkidle")
            page.get_by_role("tab", name="Run inspector", exact=True).click()
            expect(page.locator(".debug-two-column")).to_be_visible()
            page.screenshot(path=str(OUT / "08-real-debug-inspector.png"), full_page=False)
            result["screenshots"].append("08-real-debug-inspector.png")

            phone = browser.new_context(
                viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
            ).new_page()
            login(phone, password)
            phone.goto(f"{BASE}/runs/{RUN_ID}", wait_until="networkidle")
            phone.get_by_role("tab", name="Doctor review", exact=True).click()
            phone.get_by_role("button", name="Approve export", exact=True).click()
            phone.get_by_role("button", name="Confirm decision", exact=True).click()
            expect(phone.locator("h1").first).to_have_text(
                "APPROVED DRAFT EXPORTED", timeout=60_000
            )
            phone.get_by_role("tab", name="Exports", exact=True).click()
            phone.screenshot(path=str(OUT / "07-real-export-mobile.png"), full_page=False)
            result["screenshots"].append("07-real-export-mobile.png")
            phone.close()

            video_context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                record_video_dir=str(OUT),
                record_video_size={"width": 1440, "height": 900},
            )
            video = video_context.new_page()
            login(video, password)
            video.get_by_role("button", name="New synthetic run").click()
            video.locator("#artifact").set_input_files(
                str(ROOT / "fixtures" / "synthetic" / "chest_clean.png")
            )
            video.get_by_role(
                "checkbox", name="I confirm this is synthetic or authorized de-identified data."
            ).check()
            video.get_by_role("button", name="Create run", exact=True).click()
            video.wait_for_url("**/runs/*")
            expect(video.locator("h1").first).to_have_text(
                "AWAITING HUMAN APPROVAL", timeout=90_000
            )
            video.get_by_role("tab", name="Doctor review", exact=True).click()
            video.get_by_role("button", name="Approve export", exact=True).click()
            video.get_by_role("button", name="Confirm decision", exact=True).click()
            expect(video.locator("h1").first).to_have_text(
                "APPROVED DRAFT EXPORTED", timeout=60_000
            )
            video.get_by_role("tab", name="Exports", exact=True).click()
            video.wait_for_timeout(1500)
            path = video.video.path() if video.video else None
            video_context.close()
            result["video"] = Path(path).name if path else None
            browser.close()
    finally:
        with db.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE username='real-live'")
            connection.execute("DELETE FROM users WHERE username='real-live'")
    (OUT / "real-live-capture.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
