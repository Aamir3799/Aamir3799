from __future__ import annotations

import re

from ..config import Config
from ..models import Listing
from .base import Scraper, heuristic_parse

# NOTE: this environment's network egress is blocked to kamernet.nl, so this
# search URL and detail-URL pattern are BEST-EFFORT and unverified. Run
# `python -m rental_search.main selftest` on a machine with real internet
# access and check the "parsed N listings" count for this source. If it's 0,
# open the search_url() below in a browser, look at a listing's real URL,
# and update DETAIL_URL_PATTERN to match it.

DETAIL_URL_PATTERN = re.compile(r"/for-rent/(?:room|studio|apartment|house)[a-z0-9\-]*/", re.IGNORECASE)


def _city_slug(city: str) -> str:
    return city.strip().lower().replace(" ", "-")


class KamernetScraper(Scraper):
    name = "kamernet"

    def search_url(self, config: Config) -> str:
        slug = _city_slug(config.search.city)
        return (
            f"https://kamernet.nl/en/for-rent/rooms-{slug}"
            f"?maxRent={int(config.search.max_price_eur)}&furnishing=Furnished"
        )

    def parse(self, html: str) -> list[Listing]:
        listings = heuristic_parse(html, "https://kamernet.nl", DETAIL_URL_PATTERN, self.name)
        # Kamernet listings are inherently rooms in a shared home unless
        # stated otherwise, so mark shared=True when we could not tell.
        for listing in listings:
            if listing.shared is None:
                listing.shared = True
        return listings
