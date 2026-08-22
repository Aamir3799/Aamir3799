from __future__ import annotations

from datetime import timedelta

from .config import SearchConfig
from .models import Listing


def matches(listing: Listing, cfg: SearchConfig) -> tuple[bool, list[str]]:
    """Returns (matches, reasons_for_rejection). Unknown fields are given the
    benefit of the doubt rather than silently dropping a possibly-good listing."""

    reasons: list[str] = []

    if listing.price_eur is not None and listing.price_eur > cfg.max_price_eur:
        reasons.append(f"price €{listing.price_eur:.0f} > max €{cfg.max_price_eur:.0f}")

    if cfg.furnished_required and listing.furnished is False:
        reasons.append("listed as unfurnished")

    if cfg.property_types and listing.property_type:
        if listing.property_type not in cfg.property_types:
            reasons.append(f"property type '{listing.property_type}' not in wanted list")

    if cfg.city and listing.city:
        if cfg.city.lower() not in listing.city.lower():
            reasons.append(f"city '{listing.city}' does not match '{cfg.city}'")

    if listing.available_from and cfg.move_in_from:
        deadline = cfg.move_in_from + timedelta(days=cfg.move_in_flexibility_days)
        if listing.available_from > deadline:
            reasons.append(
                f"available_from {listing.available_from} is after {deadline}"
            )

    return (len(reasons) == 0, reasons)
