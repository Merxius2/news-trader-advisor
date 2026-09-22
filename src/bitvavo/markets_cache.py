"""Fetch and cache Bitvavo /markets (public endpoint, Phase 0)."""

from __future__ import annotations

import sqlite3

import httpx

from src.config_loader import BitvavoConfig
from src.storage.db import utc_now_iso


def fetch_markets(rest_url: str, quote: str = "EUR") -> list[dict]:
    url = f"{rest_url.rstrip('/')}/markets"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        markets = resp.json()
    return [m for m in markets if m.get("quote") == quote]


def refresh_markets_cache(conn: sqlite3.Connection, config: BitvavoConfig) -> int:
    markets = fetch_markets(config.rest_url, config.quote_currency)
    now = utc_now_iso()
    conn.execute("DELETE FROM bitvavo_markets_cache")
    for m in markets:
        conn.execute(
            """
            INSERT INTO bitvavo_markets_cache (market, base, quote, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                m["market"],
                m["base"],
                m["quote"],
                m.get("status", "unknown"),
                now,
            ),
        )
    conn.commit()
    return len(markets)
