from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..config import Config, GenericSourceConfig
from ..models import Listing
from ..parsing import guess_furnished, guess_property_type, guess_registration_possible, parse_available_from, parse_price
from .base import Scraper


class GenericScraper(Scraper):
    """A CSS-selector-configurable scraper for any other public listing site
    (housing board, university page, classifieds, etc). Configure it in
    config.yaml under sources.generic — see config.example.yaml.

    This deliberately does NOT support sites that require logging in (e.g.
    Facebook groups/Marketplace): scraping those needs stored session
    credentials, breaks their Terms of Service, and is fragile against
    anti-bot measures. If you have a *public*, no-login page (e.g. a public
    housing board, a city's student-housing listing page, a public RSS
    feed rendered as HTML), point this scraper at it instead.
    """

    def __init__(self, source_cfg: GenericSourceConfig):
        self.name = source_cfg.name
        self.cfg = source_cfg
        self.use_browser = source_cfg.use_browser

    def search_url(self, config: Config) -> str:
        return self.cfg.search_url

    def _select_text(self, card, selector: str | None) -> str | None:
        if not selector:
            return None
        el = card.select_one(selector)
        if el is None:
            return None
        return el.get_text(" ", strip=True)

    def parse(self, html: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[Listing] = []

        for card in soup.select(self.cfg.listing_selector):
            title = self._select_text(card, self.cfg.title_selector) or ""

            url = None
            if self.cfg.url_selector:
                el = card.select_one(self.cfg.url_selector)
                if el is not None:
                    url = el.get("href") or el.get_text(" ", strip=True)
            if url:
                url = urljoin(self.cfg.search_url, url)
            else:
                url = self.cfg.search_url

            price_text = self._select_text(card, self.cfg.price_selector) or ""
            full_text = card.get_text(" ", strip=True)

            listings.append(
                Listing(
                    source=self.name,
                    external_id=url,
                    title=(title or url)[:200],
                    url=url,
                    price_eur=parse_price(price_text) or parse_price(full_text),
                    property_type=guess_property_type(full_text),
                    furnished=guess_furnished(full_text),
                    available_from=parse_available_from(full_text),
                    registration_possible=guess_registration_possible(full_text),
                    description=full_text[:500],
                )
            )

        return listings


def build_generic_scrapers(config: Config) -> list[GenericScraper]:
    return [GenericScraper(g) for g in config.generic_sources if g.enabled]
