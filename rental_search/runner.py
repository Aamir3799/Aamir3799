from __future__ import annotations

import logging

from .config import Config
from .filters import matches
from .models import Listing
from .notifier import send_digest_email
from .scrapers.base import Scraper
from .scrapers.generic import build_generic_scrapers
from .scrapers.huurwoningen import HuurWoningenScraper
from .scrapers.kamernet import KamernetScraper
from .scrapers.pararius import ParariusScraper
from .storage import SeenListingsStore

logger = logging.getLogger(__name__)


def build_scrapers(config: Config) -> list[Scraper]:
    scrapers: list[Scraper] = []
    builtin = {
        "kamernet": KamernetScraper(),
        "pararius": ParariusScraper(),
        "huurwoningen": HuurWoningenScraper(),
    }
    for name, scraper in builtin.items():
        toggle = config.sources.get(name)
        if toggle and toggle.enabled:
            scraper.use_browser = toggle.use_browser
            scrapers.append(scraper)
    scrapers.extend(build_generic_scrapers(config))
    return scrapers


def run_once(config: Config, store: SeenListingsStore) -> list[Listing]:
    """Scrapes all enabled sources once, filters for new matches, records
    them as seen, and returns the list of new matching listings."""
    new_matches: list[Listing] = []

    for scraper in build_scrapers(config):
        try:
            listings = scraper.fetch_listings(config)
        except Exception:
            logger.exception("Scraper %s failed", scraper.name)
            continue

        logger.info("%s: fetched %d listing(s)", scraper.name, len(listings))

        for listing in listings:
            if not store.is_new(listing.dedup_key):
                continue
            store.mark_seen(listing.dedup_key, listing.source, listing.title, listing.url)

            ok, reasons = matches(listing, config.search)
            if ok:
                new_matches.append(listing)
            else:
                logger.debug("Skipped %s: %s", listing.url, "; ".join(reasons))

    return new_matches


def run_once_and_notify(config: Config, store: SeenListingsStore) -> list[Listing]:
    new_matches = run_once(config, store)
    if new_matches:
        logger.info("Found %d new matching listing(s)", len(new_matches))
        send_digest_email(config.email, new_matches)
    else:
        logger.info("No new matching listings this pass")
    return new_matches
