from __future__ import annotations

import html
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import EmailConfig
from .models import Listing

logger = logging.getLogger(__name__)


def _format_contact_html(listing: Listing) -> str:
    if not (listing.contact_name or listing.contact_phone or listing.contact_email):
        return "<br>Contact: not found on the listing page — open the link above."

    parts = []
    if listing.contact_name:
        parts.append(html.escape(listing.contact_name))
    if listing.contact_phone:
        digits = "".join(c for c in listing.contact_phone if c.isdigit() or c == "+")
        parts.append(f"<a href='tel:{digits}'>{html.escape(listing.contact_phone)}</a>")
    if listing.contact_email:
        parts.append(f"<a href='mailto:{listing.contact_email}'>{html.escape(listing.contact_email)}</a>")
    return f"<br>Contact: {' &middot; '.join(parts)}"


def _format_listing_html(listing: Listing) -> str:
    price = f"€{listing.price_eur:.0f}/month" if listing.price_eur is not None else "price unknown"
    furnished = {True: "furnished", False: "NOT furnished", None: "furnished: unverified"}[listing.furnished]
    available = listing.available_from.isoformat() if listing.available_from else "date unverified"
    registration = {
        True: "registration possible",
        False: "no address registration",
        None: "registration: unknown",
    }[listing.registration_possible]
    return (
        f"<li><b><a href='{listing.url}'>{listing.title}</a></b><br>"
        f"{price} &middot; {furnished} &middot; available: {available} &middot; {registration} &middot; source: {listing.source}"
        f"{_format_contact_html(listing)}"
        f"</li>"
    )


def format_digest_html(listings: list[Listing]) -> str:
    items = "\n".join(_format_listing_html(l) for l in listings)
    return (
        "<html><body>"
        f"<p>{len(listings)} new matching listing(s) found:</p>"
        f"<ul>{items}</ul>"
        "<p><i>Some sites require you to make a free/paid account on their "
        "own platform to actually message the landlord — this alert just "
        "gets you there first.</i></p>"
        "</body></html>"
    )


def send_digest_email(cfg: EmailConfig, listings: list[Listing]) -> None:
    if not listings:
        return
    if not cfg.enabled:
        logger.info("Email notifications disabled; skipping send for %d listing(s)", len(listings))
        return
    if not cfg.smtp_user or not cfg.smtp_password or not cfg.to_address:
        logger.error(
            "Email notification requested but smtp_user/smtp_password/to_address "
            "are not configured — see config.example.yaml. Skipping send."
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Room alert] {len(listings)} new match(es)"
    msg["From"] = cfg.smtp_user
    msg["To"] = cfg.to_address
    msg.attach(MIMEText(format_digest_html(listings), "html"))

    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(cfg.smtp_user, cfg.smtp_password)
        server.sendmail(cfg.smtp_user, [cfg.to_address], msg.as_string())
    logger.info("Sent digest email with %d listing(s) to %s", len(listings), cfg.to_address)
