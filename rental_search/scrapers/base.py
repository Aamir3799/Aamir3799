from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..config import Config
from ..fetcher import fetch_html
from ..models import Listing
from ..parsing import (
    guess_furnished,
    guess_property_type,
    guess_registration_possible,
    parse_available_from,
    parse_price,
)

logger = logging.getLogger(__name__)


class Scraper(ABC):
    name: str
    use_browser: bool = False

    @abstractmethod
    def search_url(self, config: Config) -> str: ...

    @abstractmethod
    def parse(self, html: str) -> list[Listing]: ...

    def fetch_listings(self, config: Config) -> list[Listing]:
        url = self.search_url(config)
        html = fetch_html(
            url,
            contact_email=config.contact_email,
            use_browser=self.use_browser,
        )
        if not html:
            return []
        listings = self.parse(html)
        if not listings:
            logger.warning(
                "%s: parsed 0 listings from %s — the page structure may have "
                "changed, the search URL may be wrong, or the page needs "
                "JS rendering. Run `python -m rental_search.main selftest` "
                "and inspect the page manually to fix the selectors.",
                self.name,
                url,
            )
        return listings


def heuristic_parse(
    html: str, base_url: str, detail_url_pattern: re.Pattern, source: str
) -> list[Listing]:
    """Generic best-effort parser: finds links matching a listing-detail URL
    pattern, then extracts price/title/etc. from the surrounding card text.
    This is more resilient to CSS-class churn than hardcoded selectors,
    since detail URL slugs tend to be stable for SEO reasons."""
    soup = BeautifulSoup(html, "html.parser")
    seen_urls: set[str] = set()
    listings: list[Listing] = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not detail_url_pattern.search(href):
            continue
        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        card = a
        for _ in range(4):
            if card.parent is None:
                break
            card = card.parent
            if len(card.get_text(strip=True)) > 40:
                break

        text = card.get_text(" ", strip=True)
        title = a.get_text(" ", strip=True) or a.get("title") or a.get("aria-label") or full_url

        listings.append(
            Listing(
                source=source,
                external_id=full_url,
                title=title[:200],
                url=full_url,
                price_eur=parse_price(text),
                property_type=guess_property_type(text),
                furnished=guess_furnished(text),
                available_from=parse_available_from(text),
                registration_possible=guess_registration_possible(text),
                description=text[:500],
            )
        )

    return listings
