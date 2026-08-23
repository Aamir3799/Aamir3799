from datetime import date

from rental_search.config import SearchConfig
from rental_search.filters import matches
from rental_search.models import Listing


def _base_listing(**overrides) -> Listing:
    defaults = dict(
        source="test",
        external_id="1",
        title="A room",
        url="https://example.org/1",
        price_eur=800,
        city="Eindhoven",
        property_type="room",
        furnished=True,
        available_from=date(2026, 9, 10),
        registration_possible=None,
    )
    defaults.update(overrides)
    return Listing(**defaults)


def _cfg(**overrides) -> SearchConfig:
    defaults = dict(
        city="Eindhoven",
        max_price_eur=900,
        furnished_required=True,
        property_types=["room", "studio", "apartment", "house"],
        move_in_from=date(2026, 9, 15),
        move_in_flexibility_days=14,
    )
    defaults.update(overrides)
    return SearchConfig(**defaults)


def test_matches_when_within_budget_and_furnished():
    ok, reasons = matches(_base_listing(), _cfg())
    assert ok, reasons


def test_rejects_over_budget():
    ok, reasons = matches(_base_listing(price_eur=950), _cfg())
    assert not ok
    assert any("price" in r for r in reasons)


def test_rejects_unfurnished_when_required():
    ok, reasons = matches(_base_listing(furnished=False), _cfg())
    assert not ok
    assert any("unfurnished" in r for r in reasons)


def test_unknown_furnished_is_not_rejected():
    ok, reasons = matches(_base_listing(furnished=None), _cfg())
    assert ok, reasons


def test_rejects_wrong_property_type():
    ok, reasons = matches(_base_listing(property_type="office"), _cfg())
    assert not ok
    assert any("property type" in r for r in reasons)


def test_rejects_available_too_late():
    ok, reasons = matches(_base_listing(available_from=date(2026, 10, 15)), _cfg())
    assert not ok
    assert any("available_from" in r for r in reasons)


def test_accepts_available_within_flexibility_window():
    ok, reasons = matches(_base_listing(available_from=date(2026, 9, 25)), _cfg())
    assert ok, reasons


def test_registration_possible_never_filters():
    for reg in (True, False, None):
        ok, _ = matches(_base_listing(registration_possible=reg), _cfg())
        assert ok
