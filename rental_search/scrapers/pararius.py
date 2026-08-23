from __future__ import annotations

import re

from ..config import Config
from ..models import Listing
from .base import Scraper, heuristic_parse

# NOTE: unverified from this sandbox (network egress to pararius.com is
# blocked here) — see kamernet.py's note. Verify/adjust on a machine with
# real internet access before relying on this.

DETAIL_URL_PATTERN = re.compile(
    r"/(?:room|studio|apartment|house)-for-rent/[a-z0-9\-]+/", re.IGNORECASE
)


def _city_slug(city: str) -> str:
    return city.strip().lower().replace(" ", "-")


class ParariusScraper(Scraper):
    name = "pararius"

    def search_url(self, config: Config) -> str:
        slug = _city_slug(config.search.city)
        return (
            f"https://www.pararius.com/apartments/{slug}"
            f"/0-{int(config.search.max_price_eur)}/furnished"
        )

    def parse(self, html: str) -> list[Listing]:
        return heuristic_parse(html, "https://www.pararius.com", DETAIL_URL_PATTERN, self.name)
