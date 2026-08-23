from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional

import yaml

_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _substitute_env(value: Any) -> Any:
    if isinstance(value, str):
        def repl(m: re.Match) -> str:
            return os.environ.get(m.group(1), "")

        return _ENV_VAR_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(v) for v in value]
    return value


@dataclass
class SearchConfig:
    city: str = "Eindhoven"
    max_price_eur: float = 900.0
    furnished_required: bool = True
    property_types: list[str] = field(
        default_factory=lambda: ["room", "studio", "apartment", "house"]
    )
    move_in_from: Optional[date] = None
    move_in_flexibility_days: int = 14


@dataclass
class EmailConfig:
    enabled: bool = True
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    to_address: str = ""


@dataclass
class SourceToggle:
    enabled: bool = True
    use_browser: bool = False


@dataclass
class GenericSourceConfig:
    name: str
    enabled: bool = False
    search_url: str = ""
    listing_selector: str = ""
    title_selector: Optional[str] = None
    price_selector: Optional[str] = None
    url_selector: Optional[str] = None
    use_browser: bool = False


@dataclass
class Config:
    search: SearchConfig
    email: EmailConfig
    sources: dict[str, SourceToggle]
    generic_sources: list[GenericSourceConfig]
    poll_interval_minutes: int
    db_path: str
    contact_email: str


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    raw = _substitute_env(raw)

    search_raw = raw.get("search", {})
    search = SearchConfig(
        city=search_raw.get("city", "Eindhoven"),
        max_price_eur=float(search_raw.get("max_price_eur", 900)),
        furnished_required=bool(search_raw.get("furnished_required", True)),
        property_types=search_raw.get(
            "property_types", ["room", "studio", "apartment", "house"]
        ),
        move_in_from=_parse_date(search_raw.get("move_in_from")),
        move_in_flexibility_days=int(search_raw.get("move_in_flexibility_days", 14)),
    )

    email_raw = raw.get("notification", {}).get("email", {})
    email = EmailConfig(
        enabled=bool(email_raw.get("enabled", True)),
        smtp_host=email_raw.get("smtp_host", "smtp.gmail.com"),
        smtp_port=int(email_raw.get("smtp_port", 587)),
        smtp_user=email_raw.get("smtp_user", ""),
        smtp_password=email_raw.get("smtp_password", ""),
        to_address=email_raw.get("to_address", ""),
    )

    sources_raw = raw.get("sources", {})
    sources: dict[str, SourceToggle] = {}
    for name in ("kamernet", "pararius", "huurwoningen"):
        entry = sources_raw.get(name, {}) or {}
        sources[name] = SourceToggle(
            enabled=bool(entry.get("enabled", True)),
            use_browser=bool(entry.get("use_browser", False)),
        )

    generic_sources = [
        GenericSourceConfig(
            name=g["name"],
            enabled=bool(g.get("enabled", False)),
            search_url=g.get("search_url", ""),
            listing_selector=g.get("listing_selector", ""),
            title_selector=g.get("title_selector"),
            price_selector=g.get("price_selector"),
            url_selector=g.get("url_selector"),
            use_browser=bool(g.get("use_browser", False)),
        )
        for g in sources_raw.get("generic", []) or []
    ]

    return Config(
        search=search,
        email=email,
        sources=sources,
        generic_sources=generic_sources,
        poll_interval_minutes=int(raw.get("polling", {}).get("interval_minutes", 10)),
        db_path=raw.get("storage", {}).get("db_path", "data/seen_listings.sqlite3"),
        contact_email=raw.get("contact_email", email.to_address or "unknown@example.com"),
    )
