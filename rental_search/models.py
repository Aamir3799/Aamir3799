from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Listing:
    """A single rental listing normalized from any source."""

    source: str
    external_id: str
    title: str
    url: str
    price_eur: Optional[float]
    city: str = ""
    property_type: Optional[str] = None  # "room" | "studio" | "apartment" | "house"
    furnished: Optional[bool] = None  # None = unknown, could not be determined
    available_from: Optional[date] = None
    registration_possible: Optional[bool] = None  # BRP/municipal address registration
    shared: Optional[bool] = None
    description: str = ""
    image_url: Optional[str] = None
    contact_name: Optional[str] = None  # landlord or agency name, if found on the listing page
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    @property
    def dedup_key(self) -> str:
        return f"{self.source}:{self.external_id}"
