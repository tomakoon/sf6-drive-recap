"""Authenticate with Buckler's Boot Camp via CAPCOM ID using Playwright.

Auth flow based on cfn-tracker (github.com/williamsjokvist/cfn-tracker):
1. Navigate to cid.capcom.com/ja/login
2. Handle age check if present
3. Fill email/password, submit
4. Wait for redirect away from auth.cid.capcom.com
5. Navigate to buckler loginep to finalize session
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext, Page

_STATE_DIR = Path(__file__).parent.parent / ".browser_state"
_STATE_FILE = _STATE_DIR / "state.json"
_DEBUG_DIR = Path(__file__).parent.parent / ".debug"

# URLs from cfn-tracker's proven auth flow
CAPCOM_LOGIN_URL = "https://cid.capcom.com/ja/login/?guidedBy=web"
BUCKLER_LOGINEP_URL = "https://www.streetfighter.com/6/buckler/auth/loginep?redirect_url=/"
BUCKLER_BASE_URL = "https://www.streetfighter.com/6/buckler"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _ensure_dirs():
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def _save_debug(page: Page, label: str):
    """Save screenshot + HTML for debugging."""
    try:
        page.screenshot(path=str(_DEBUG_DIR / f"{label}.png"), full_page=True)
        (_DEBUG_DIR / f"{label}.html").write_text(page.content())
    except Exception:
        pass


def get_authenticated_context(
    email: str,
    password: str,
    headless: bool = True,
) -> tuple:
    """
    Returns (playwright_instance, browser, context, cfn_name, short_id).
    cfn_name and short_id are extracted from the login response.
    """
    _ensure_dirs()
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)

    # Try reusing saved session
    if _STATE_FILE.exists():
        context = browser.new_context(storage_state=str(_STATE_FILE), user_agent=USER_AGENT)
        page = context.new_page()
        page.goto(BUCKLER_BASE_URL, wait_until="networkidle", timeout=30000)
        # Check if we're still logged in
        if "buckler" in page.url and "/auth/login" not in page.url:
            cfn_name, short_id = _extract_user_info(page)
            print(f"  Reusing saved session. CFN: {cfn_name or 'unknown'} (SID: {short_id})")
            page.close()
            return pw, browser, context, cfn_name, short_id
        print("  Saved session expired, re-authenticating...")
        page.close()
        context.close()

    # Fresh login following cfn-tracker's auth flow
    context = browser.new_context(user_agent=USER_AGENT)
    page = context.new_page()

    # Step 1: Go to CAPCOM ID login page
    print(f"  Navigating to CAPCOM ID login...")
    page.goto(CAPCOM_LOGIN_URL, wait_until="networkidle", timeout=30000)
    print(f"  Landed on: {page.url}")
    _save_debug(page, "01_capcom_login")

    # Step 2: Check if already authed (redirected to mypage)
    if "cid.capcom.com/ja/mypage" in page.url:
        print("  Already authenticated with CAPCOM ID.")
    else:
        # Step 3: Handle age check if present (from cfn-tracker)
        if "agecheck" in page.url:
            print("  Handling age check...")
            page.select_option("#country", "United States")
            page.select_option("#birthYear", "1990")
            page.select_option("#birthMonth", "6")
            page.select_option("#birthDay", "15")
            page.click('form button[type="submit"]')
            page.wait_for_load_state("networkidle")

        # Step 4: Fill login form
        print("  Filling login form...")
        page.fill('input[name="email"]', email)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        _save_debug(page, "02_after_submit")

        # Step 5: Wait for redirect away from auth.cid.capcom.com (cfn-tracker pattern)
        print("  Waiting for auth redirect...")
        for _ in range(30):
            if "auth.cid.capcom.com" not in page.url:
                break
            time.sleep(1)
        _save_debug(page, "03_after_redirect")

    # Step 6: Navigate to Buckler loginep to finalize session
    print("  Finalizing Buckler session...")
    page.goto(BUCKLER_LOGINEP_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_load_state("networkidle")
    _save_debug(page, "04_buckler_post_login")

    cfn_name, short_id = _extract_user_info(page)
    print(f"  Logged in. CFN: {cfn_name or 'unknown'} (SID: {short_id})")

    # Save session state
    context.storage_state(path=str(_STATE_FILE))
    page.close()
    return pw, browser, context, cfn_name, short_id


def _extract_user_info(page: Page) -> tuple[str | None, str | None]:
    """Extract CFN name and short_id from Buckler's login data API."""
    try:
        resp = page.evaluate(
            "fetch('/6/buckler/api/auth/getlogindata').then(r => r.json())"
        )
        if resp and "loginUser" in resp:
            user = resp["loginUser"]
            cfn = user.get("fighterId")
            sid = str(user.get("shortId", ""))
            return cfn, sid
    except Exception:
        pass
    return None, None
