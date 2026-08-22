import os
from datetime import date

from rental_search.config import GenericSourceConfig
from rental_search.scrapers.generic import GenericScraper

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_generic.html")


def _load_fixture() -> str:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _make_scraper() -> GenericScraper:
    cfg = GenericSourceConfig(
        name="test-source",
        enabled=True,
        search_url="https://example.org/rooms",
        listing_selector=".listing-card",
        title_selector=".title",
        price_selector=".price",
        url_selector="a",
    )
    return GenericScraper(cfg)


def test_parses_all_cards():
    scraper = _make_scraper()
    listings = scraper.parse(_load_fixture())
    assert len(listings) == 3


def test_extracts_price_and_furnished():
    scraper = _make_scraper()
    listings = scraper.parse(_load_fixture())
    by_title = {l.title: l for l in listings}

    furnished_room = by_title["Furnished room near TU Eindhoven"]
    assert furnished_room.price_eur == 750
    assert furnished_room.furnished is True
    assert furnished_room.available_from == date(2026, 9, 1)
    assert furnished_room.registration_possible is True
    assert furnished_room.url == "https://example.org/rooms/1"

    unfurnished_studio = by_title["Unfurnished studio"]
    assert unfurnished_studio.price_eur == 1200
    assert unfurnished_studio.furnished is False
    assert unfurnished_studio.property_type == "studio"

    shared_room = by_title["Cozy shared room, direct beschikbaar"]
    assert shared_room.price_eur == 650
    assert shared_room.registration_possible is False
    assert shared_room.available_from == date.today()
