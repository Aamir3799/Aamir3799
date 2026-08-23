from __future__ import annotations

import re
from datetime import date
from typing import Optional

PRICE_RE = re.compile(r"€\s?([\d][\d.,]{0,8})")

_NL_MONTHS = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 11,
    "december": 12,
}
_EN_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}

_AVAILABLE_FROM_RE = re.compile(
    r"(?:vanaf|available from|beschikbaar vanaf)\s+(\d{1,2})[\s\-]+([a-zA-Z]+)[\s\-]+(\d{4})",
    re.IGNORECASE,
)
_IMMEDIATE_RE = re.compile(
    r"\b(direct beschikbaar|per direct|immediately|available now|asap)\b", re.IGNORECASE
)


def parse_price(text: str) -> Optional[float]:
    m = PRICE_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    # Dutch formatting uses "." as thousands separator and "," as decimal, e.g. "1.250,-"
    raw = raw.replace(".", "")
    raw = raw.split(",")[0]
    try:
        value = float(raw)
    except ValueError:
        return None
    if value < 50 or value > 10000:
        return None  # implausible, likely matched something unrelated to rent
    return value


def parse_available_from(text: str) -> Optional[date]:
    m = _AVAILABLE_FROM_RE.search(text)
    if m:
        day, month_name, year = m.groups()
        month = _NL_MONTHS.get(month_name.lower()) or _EN_MONTHS.get(month_name.lower())
        if month:
            try:
                return date(int(year), month, int(day))
            except ValueError:
                return None
        return None
    if _IMMEDIATE_RE.search(text):
        return date.today()
    return None


def guess_furnished(text: str) -> Optional[bool]:
    lowered = text.lower()
    if "ongemeubileerd" in lowered or "unfurnished" in lowered:
        return False
    if "kaal" in lowered:
        return False
    if "gemeubileerd" in lowered or "furnished" in lowered:
        return True
    return None


def guess_property_type(text: str) -> Optional[str]:
    lowered = text.lower()
    if "studio" in lowered:
        return "studio"
    if "appartement" in lowered or "apartment" in lowered:
        return "apartment"
    if re.search(r"\bhuis\b|\bwoning\b|\bhouse\b", lowered):
        return "house"
    if "kamer" in lowered or re.search(r"\broom\b", lowered):
        return "room"
    return None


def guess_registration_possible(text: str) -> Optional[bool]:
    lowered = text.lower()
    # Check negative phrasings first: "geen inschrijving mogelijk" contains
    # "inschrijving mogelijk" as a substring, so a positive-first check would
    # misclassify it.
    if "geen inschrijving" in lowered or "inschrijving niet mogelijk" in lowered or "no registration" in lowered:
        return False
    if "inschrijving mogelijk" in lowered or "registration possible" in lowered:
        return True
    return None
