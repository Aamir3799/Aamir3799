from datetime import date

from rental_search.models import Listing
from rental_search.notifier import format_digest_html


def _listing(**overrides) -> Listing:
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


def test_digest_includes_contact_details_when_found():
    listing = _listing(
        contact_name="Jansen Makelaardij",
        contact_phone="020-1234567",
        contact_email="info@jansenmakelaardij.nl",
    )
    html = format_digest_html([listing])
    assert "Jansen Makelaardij" in html
    assert "tel:0201234567" in html
    assert "mailto:info@jansenmakelaardij.nl" in html


def test_digest_falls_back_when_no_contact_found():
    listing = _listing()
    html = format_digest_html([listing])
    assert "not found on the listing page" in html
