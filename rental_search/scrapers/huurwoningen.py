from __future__ import annotations

import re

from ..config import Config
from ..models import Listing
from .base import Scraper, heuristic_parse

# NOTE: unverified from this sandbox (network egress to huurwoningen.nl is
# blocked here) — see kamernet.py's note. Verify/adjust on a machine with
# real internet access before relying on this. HuurWoningen skews towards
# whole apartments/houses rather than single rooms; expect fewer matches
# for a room-sharing search than Kamernet.

DETAIL_URL_PATTERN = re.compile(r"/huurwoningen/[a-z0-9\-]+/[a-z0-9\-]+/", re.IGNORECASE)


def _city_slug(city: str) -> str:
    return city.strip().lower().replace(" ", "-")


class HuurWoningenScraper(Scraper):
    name = "huurwoningen"

    def search_url(self, config: Config) -> str:
        slug = _city_slug(config.search.city)
        return f"https://www.huurwoningen.nl/in/{slug}/?price=0-{int(config.search.max_price_eur)}"

    def parse(self, html: str) -> list[Listing]:
        return heuristic_parse(html, "https://www.huurwoningen.nl", DETAIL_URL_PATTERN, self.name)
