from __future__ import annotations

import argparse
import logging
import sys
import time

from .config import load_config
from .runner import build_scrapers, run_once_and_notify
from .storage import SeenListingsStore


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    store = SeenListingsStore(config.db_path)
    new_matches = run_once_and_notify(config, store)
    print(f"Done. {len(new_matches)} new matching listing(s) found.")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    store = SeenListingsStore(config.db_path)
    interval = config.poll_interval_minutes * 60
    print(f"Watching for new listings every {config.poll_interval_minutes} minute(s). Ctrl+C to stop.")
    while True:
        try:
            run_once_and_notify(config, store)
        except Exception:
            logging.getLogger(__name__).exception("Unexpected error during scan")
        time.sleep(interval)


def cmd_selftest(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    print(f"Search URLs for city='{config.search.city}', max_price={config.search.max_price_eur}:\n")
    ok = True
    for scraper in build_scrapers(config):
        url = scraper.search_url(config)
        print(f"- {scraper.name}: {url}")
        listings = scraper.fetch_listings(config)
        print(f"    -> parsed {len(listings)} listing(s)")
        if not listings:
            ok = False
    if not ok:
        print(
            "\nOne or more sources parsed 0 listings. This usually means the "
            "search URL or detail-URL pattern needs adjusting for that site's "
            "current markup — open the URL above in a browser and compare. "
            "See the scraper's source file for where to fix it."
        )
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Netherlands rental room/apartment alert bot")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Scan all sources once and email new matches").set_defaults(func=cmd_run)
    sub.add_parser("watch", help="Scan on a repeating schedule (see polling.interval_minutes)").set_defaults(func=cmd_watch)
    sub.add_parser("selftest", help="Fetch each source once and report how many listings parsed").set_defaults(func=cmd_selftest)

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
