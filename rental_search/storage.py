from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

_SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_listings (
    dedup_key TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    first_seen_at TEXT NOT NULL
);
"""


class SeenListingsStore:
    """Tracks which listings we've already alerted on, so we never repeat an alert."""

    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def is_new(self, dedup_key: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_listings WHERE dedup_key = ?", (dedup_key,)
            ).fetchone()
            return row is None

    def mark_seen(self, dedup_key: str, source: str, title: str, url: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_listings (dedup_key, source, title, url, first_seen_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (dedup_key, source, title, url, datetime.now(timezone.utc).isoformat()),
            )
