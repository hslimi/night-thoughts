from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect, sync_playwright

from nt_imaging.controlplane.auth import hash_password
from nt_imaging.controlplane.db import ControlDB

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "synthetic" / "chest_clean.png"
VIEWPORTS = [
    (320, 568),
    (360, 800),
    (375, 812),
    (390, 844),
    (412, 915),
    (768, 1024),
    (1024, 768),
    (1440, 900),
    (844, 390),
    (568, 320),
]


def layout_assertions(page: Page, width: int, label: str) -> dict[str, Any]:
    result = page.evaluate(
        """() => {
          const visible = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
          const controls = [...document.querySelectorAll('button,a,input,select,textarea')].filter(visible);
          const outside = controls.filter(el => { const r=el.getBoundingClientRect(); return r.right > innerWidth + 1 || r.left < -1; }).map(el => el.textContent || el.id || el.tagName);
          const small = [...document.querySelectorAll('.button,.mobile-menu-button,.modal-close,.row-action,.tab,.segmented-control button,.password-toggle')].filter(visible).filter(el => { const r=el.getBoundingClientRect(); return r.width < 40 || r.height < 40; }).map(el => el.textContent || el.getAttribute('aria-label'));
          return {documentWidth: document.documentElement.scrollWidth, viewportWidth: innerWidth, outside, small};
        }"""
    )
    assert result["documentWidth"] <= result["viewportWidth"] + 1, (label, result)
    assert not result["outside"], (label, result)
    if width < 600:
        assert not result["small"], (label, result)
    return {"label": label, **result}


def login(page: Page, base: str, password: str, *, wrong_first: bool = False) -> None:
    page.goto(base, wait_until="networkidle")
    page.locator("#username").fill("browser-check")
    if wrong_first:
        page.locator("#password").fill("incorrect demonstration password")
        page.get_by_role("button", name="Sign in securely").click()
        expect(page.get_by_text("Invalid username or password")).to_be_visible()
    page.locator("#password").fill(password)
    page.get_by_role("button", name="Sign in securely").click()
    expect(page.get_by_role("heading", name="Review worklist")).to_be_visible(timeout=20_000)


def create_run(page: Page) -> str:
    page.get_by_role("button", name="New synthetic run").click()
    page.locator("#artifact").set_input_files(str(FIXTURE))
    page.get_by_role(
        "checkbox", name="I confirm this is synthetic or authorized de-identified data."
    ).check()
    page.get_by_role("button", name="Create run", exact=True).click()
    page.wait_for_url("**/runs/*", timeout=20_000)
    expect(page.locator("h1").first).to_have_text("AWAITING HUMAN APPROVAL", timeout=30_000)
    return page.url.rsplit("/", 1)[-1]


def decide(page: Page, action: str, note: str = "") -> None:
    if note:
        page.locator("#decision-note").fill(note)
    page.get_by_role("button", name=action, exact=True).click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    bounds = dialog.bounding_box()
    assert bounds and bounds["x"] >= 0 and bounds["y"] >= 0
    assert bounds and bounds["x"] + bounds["width"] <= page.viewport_size["width"] + 1
    dialog.get_by_role("button", name="Confirm decision").click()


def exercise_happy_path(
    page: Page, base: str, width: int, height: int, password: str
) -> dict[str, Any]:
    login(page, base, password, wrong_first=(width, height) == (390, 844))
    checks = [layout_assertions(page, width, "dashboard")]
    if width < 701:
        page.get_by_role("button", name="Open navigation").click()
        expect(page.get_by_role("dialog", name="Main navigation")).to_be_visible()
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog", name="Main navigation")).to_have_count(0)
    run_id = create_run(page)
    checks.append(layout_assertions(page, width, "monitor"))
    expect(page.locator(".gate-card")).to_have_count(8)
    page.get_by_role("tab", name="Local graph", exact=True).click()
    expect(page.locator(".inspector-columns")).to_contain_text("imaging_readiness")
    page.get_by_role("tab", name="Doctor review", exact=True).click()
    page.get_by_role("button", name="Zoom in").first.click()
    page.get_by_role("button", name="Reset").first.click()
    checks.append(layout_assertions(page, width, "review"))
    decide(page, "Approve export")
    expect(page.locator("h1").first).to_have_text("APPROVED DRAFT EXPORTED", timeout=30_000)
    page.get_by_role("tab", name="Exports", exact=True).click()
    expect(page.get_by_role("link", name="Download")).to_have_count(3)
    with page.expect_download() as download_info:
        page.get_by_role("link", name="Download").first.click()
    download = download_info.value
    assert download.path() and download.path().stat().st_size > 0
    checks.append(layout_assertions(page, width, "exports"))
    return {"viewport": [width, height], "run_id": run_id, "checks": checks}


def exercise_interventions(page: Page, base: str, password: str) -> dict[str, Any]:
    login(page, base, password)
    revised = create_run(page)
    page.get_by_role("tab", name="Doctor review", exact=True).click()
    decide(page, "Request changes", "Synthetic request: clarify the demonstration limitations")
    expect(page.locator(".run-meta-strip")).to_contain_text("Revision 1", timeout=30_000)
    expect(page.locator(".revision-history")).to_contain_text("REQUEST CHANGES")
    decide(page, "Reject draft", "Synthetic rejection after reviewing the regenerated revision")
    expect(page.locator("h1").first).to_have_text("HUMAN REJECTED", timeout=30_000)
    page.get_by_role("tab", name="Exports", exact=True).click()
    expect(page.get_by_role("heading", name="No approved export")).to_be_visible()
    page.goto(base, wait_until="networkidle")
    cancelled = create_run(page)
    page.get_by_role("button", name="Cancel run", exact=True).click()
    expect(page.locator("h1").first).to_have_text("CANCELLED", timeout=20_000)
    page.get_by_role("tab", name="Exports", exact=True).click()
    expect(page.get_by_role("heading", name="No approved export")).to_be_visible()
    layout_assertions(page, 390, "interventions")
    return {"request_changes_then_reject": revised, "cancelled": cancelled}


def main() -> None:
    os.environ["DATA_ROOT"] = os.getenv("BROWSER_DATA_ROOT", str(ROOT / "var" / "guide-mock"))
    base = os.getenv("BROWSER_BASE_URL", "http://127.0.0.1:8002").rstrip("/")
    data_root = Path(os.environ["DATA_ROOT"]).resolve()
    db = ControlDB(data_root / "controlplane.sqlite3")
    username = "browser-check"
    password = secrets.token_urlsafe(24)
    db.upsert_user(username, hash_password(password))
    results: dict[str, Any] = {"base_url": base, "inference_mode": "MOCK", "viewports": []}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                headless=True,
            )
            for width, height in VIEWPORTS:
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    is_mobile=width < 600,
                    has_touch=width < 600,
                    accept_downloads=True,
                )
                page = context.new_page()
                results["viewports"].append(
                    exercise_happy_path(page, base, width, height, password)
                )
                context.close()
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                is_mobile=True,
                has_touch=True,
            )
            page = context.new_page()
            results["interventions"] = exercise_interventions(page, base, password)
            with db.connect() as connection:
                connection.execute("DELETE FROM sessions WHERE username=?", (username,))
            expect(
                page.get_by_text("Your session expired. Sign in again to continue.")
            ).to_be_visible(timeout=15_000)
            login(page, base, password)
            results["session_expiry_and_recovery"] = True
            context.close()
            browser.close()
    finally:
        with db.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE username=?", (username,))
            connection.execute("DELETE FROM users WHERE username=?", (username,))
    output = ROOT / "evidence" / "responsive" / "console-browser-tests.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"passed_viewports": len(results["viewports"]), "output": str(output)}))


if __name__ == "__main__":
    main()
