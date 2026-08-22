from __future__ import annotations

import logging
import time
from urllib import robotparser
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

_ROBOTS_CACHE: dict[str, robotparser.RobotFileParser] = {}


def _robots_allowed(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    rp = _ROBOTS_CACHE.get(base)
    if rp is None:
        rp = robotparser.RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        try:
            rp.read()
        except Exception:
            logger.warning("Could not read robots.txt for %s; proceeding cautiously", base)
        _ROBOTS_CACHE[base] = rp
    try:
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True


def build_user_agent(contact_email: str) -> str:
    return (
        "Mozilla/5.0 (compatible; RoomAlertBot/1.0; personal, non-commercial rental "
        f"search assistant; contact: {contact_email})"
    )


def fetch_html(
    url: str,
    *,
    contact_email: str,
    use_browser: bool = False,
    min_delay_seconds: float = 2.0,
    timeout_seconds: int = 20,
) -> str | None:
    """Fetch a page's HTML, respecting robots.txt and a polite request rate.

    Returns None (and logs a warning) if robots.txt disallows the URL for our
    user agent, or the fetch fails.
    """
    user_agent = build_user_agent(contact_email)

    if not _robots_allowed(url, user_agent):
        logger.warning("robots.txt disallows fetching %s for our bot — skipping", url)
        return None

    time.sleep(min_delay_seconds)

    try:
        if use_browser:
            return _fetch_with_browser(url, user_agent, timeout_seconds)
        resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout_seconds)
        resp.raise_for_status()
        return resp.text
    except Exception:
        logger.exception("Failed to fetch %s", url)
        return None


def _fetch_with_browser(url: str, user_agent: str, timeout_seconds: int) -> str:
    """Render a JS-heavy page with headless Chromium. Requires `playwright install`
    to have been run once (see README)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(user_agent=user_agent)
            page.goto(url, wait_until="networkidle", timeout=timeout_seconds * 1000)
            return page.content()
        finally:
            browser.close()
