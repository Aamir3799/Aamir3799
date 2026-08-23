# Netherlands Rental Room Alert

Watches Dutch rental listing sites for new rooms/studios/apartments/houses in
**Eindhoven** under **€900/month**, **furnished**, and emails you the moment
a match appears — so you can be one of the first to react.

Your search criteria (see `config.example.yaml`):
- City: Eindhoven
- Max rent: €900/month
- Furnished only
- Room-sharing is fine (rooms in a shared house are included, not filtered out)
- Move-in from 2026-09-15 (also accepts listings available a bit later — see
  `move_in_flexibility_days`)
- Address registration (BRP/"inschrijving") is **not** used as a filter — it's
  just shown in the alert email for your information, since you don't need it

## What this does — and doesn't — do

- **Alerts you, it doesn't auto-apply.** You asked for alerts fast enough to
  apply yourself, not unattended auto-submission — this only sends an email
  the moment a new match is found, with a direct link.
- **It tries to include a phone number, email, or agency name directly in
  the alert.** For each match, it fetches the listing's own page (not just
  the search-results snippet) and looks for contact details, so you often
  don't have to click through at all. This is best-effort text scanning —
  if a page shows contact info in a way the scanner doesn't recognize, or
  hides it behind a "react"/"contact" button (see below), the alert says so
  and you'll need to open the link.
- **It can't bypass a site's own contact/registration wall.** Some sites
  (Kamernet especially) require *you* to have a free or paid account on
  *their* platform before you can message a landlord — no phone/email is
  shown on the page at all until you do. That's the platform's own rule and
  isn't something this tool can or should work around — it just gets you
  the link before most other people see it. Pararius and HuurWoningen
  listings are more often placed by agents who list a phone/email openly.
- **Facebook groups/Marketplace are intentionally not scraped.** They require
  a logged-in session, and automating that both breaks Meta's Terms of
  Service and is fragile against anti-bot detection. If you find a *public*
  (no-login) housing board or page, add it under `sources.generic` in
  `config.yaml` — that scraper works with any site via CSS selectors, no
  code changes needed.

## Important: selectors are unverified — check before relying on this

This code was written in a sandboxed environment with **no network access to
kamernet.nl, pararius.com, or huurwoningen.nl** — every attempt to reach them
was blocked at the proxy level, so their HTML structure could not be
inspected directly. The three site-specific scrapers were built using a
resilient technique (matching listing-detail URL patterns + extracting price/
date/furnished from surrounding text, rather than brittle hardcoded CSS class
names) plus a `selftest` command to check the result — but they are **not
guaranteed to work out of the box.**

**Before trusting this for real:**

```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml   # then edit config.yaml
python -m rental_search.main selftest
```

This fetches each source once and reports how many listings it parsed. If a
source reports 0:
1. Open that source's printed search URL in your own browser.
2. Check whether it actually shows listings for Eindhoven under €900 (the URL
   query-parameter format may need adjusting — it's a guess based on common
   patterns).
3. If the page looks JS-rendered (listings don't appear in "view source"),
   set `use_browser: true` for that source in `config.yaml` and run
   `playwright install chromium` once.
4. If listings are visible but still 0 parsed, open the relevant file in
   `rental_search/scrapers/` (e.g. `kamernet.py`) and adjust
   `DETAIL_URL_PATTERN` to match real listing URLs on that page (right-click
   a listing → Copy Link Address, compare to the regex).
5. Note: if `selftest` shows a "robots.txt disallows fetching" warning, that's
   the tool correctly refusing to scrape a page robots.txt says bots
   shouldn't touch — not a bug. If robots.txt itself fails to load (network
   hiccup), the tool also fails *closed* (skips that scan) rather than
   scraping without checking — try again on the next `watch` cycle.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
```

Edit `config.yaml`:
- `search.city`, `search.max_price_eur`, etc. are already set to your
  criteria — adjust if they change.
- `notification.email.to_address` — where alerts get sent.
- `notification.email.smtp_user` / `smtp_password` — the sending account's
  credentials. **Don't put your real password in the file** — set them as
  environment variables instead (the `${SMTP_USER}` syntax reads from the
  environment):

  ```bash
  export SMTP_USER="youraddress@gmail.com"
  export SMTP_PASSWORD="your-app-password"
  ```

  For Gmail: enable 2-Step Verification, then create an **App Password** at
  https://myaccount.google.com/apppasswords — use that as `SMTP_PASSWORD`,
  not your normal Gmail password.

## Running

```bash
# One scan, then exit:
python -m rental_search.main run

# Keep running, scanning every `polling.interval_minutes`:
python -m rental_search.main watch
```

For "always on" monitoring, run `watch` under a process manager, e.g. a
systemd service or `tmux`/`screen` session, or a cron job calling `run`
every few minutes.

## How it avoids duplicate alerts

Every listing is recorded by a unique key (source + listing URL) in a local
SQLite database (`data/seen_listings.sqlite3` by default). You'll only ever
be emailed about a given listing once.

## Adding another source

Any public (no-login) listing page can be added without touching code, under
`sources.generic` in `config.yaml`:

```yaml
sources:
  generic:
    - name: "some-other-site"
      enabled: true
      search_url: "https://example.org/rooms?city=eindhoven"
      listing_selector: ".listing-card"   # CSS selector for each listing "card"
      title_selector: ".title"
      price_selector: ".price"
      url_selector: "a"                   # element whose href is the listing link
```

Right-click a listing on the target page → "Inspect" in your browser to find
the right selectors.

## Running tests

```bash
pytest tests/ -q
```
