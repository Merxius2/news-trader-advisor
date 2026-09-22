"""SQLite schema migrations."""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 2

MIGRATIONS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        summary TEXT NOT NULL DEFAULT '',
        source TEXT NOT NULL,
        published_at TEXT,
        content_hash TEXT NOT NULL,
        fetched_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash);
    CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
    """,
    """
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL REFERENCES articles(id),
        model TEXT NOT NULL,
        raw_response TEXT NOT NULL,
        parsed_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_analyses_article_id ON analyses(article_id);
    """,
    """
    CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        analysis_id INTEGER NOT NULL REFERENCES analyses(id),
        market TEXT NOT NULL,
        action TEXT NOT NULL,
        confidence REAL NOT NULL,
        rationale TEXT NOT NULL,
        event_type TEXT NOT NULL DEFAULT 'other',
        visible INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_suggestions_market ON suggestions(market);
    CREATE INDEX IF NOT EXISTS idx_suggestions_created_at ON suggestions(created_at);
    """,
    """
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL,
        event_type TEXT NOT NULL DEFAULT 'system',
        message TEXT NOT NULL,
        metadata_json TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON activity_log(timestamp);
    """,
    """
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        articles_processed INTEGER NOT NULL DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bitvavo_markets_cache (
        market TEXT PRIMARY KEY,
        base TEXT NOT NULL,
        quote TEXT NOT NULL,
        status TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bitvavo_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        account_total_eur REAL,
        synced_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bitvavo_balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        available REAL NOT NULL,
        in_order REAL NOT NULL DEFAULT 0,
        eur_value REAL,
        synced_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bitvavo_trades (
        trade_id TEXT PRIMARY KEY,
        market TEXT NOT NULL,
        side TEXT NOT NULL,
        price REAL NOT NULL,
        amount REAL NOT NULL,
        fee REAL NOT NULL DEFAULT 0,
        timestamp TEXT NOT NULL,
        client_order_id TEXT,
        is_trader_tagged INTEGER NOT NULL DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS trader_config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        allocation_eur REAL NOT NULL,
        reserve_eur REAL NOT NULL,
        isolation_mode TEXT NOT NULL,
        attribution_start TEXT,
        subaccount_id TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS trader_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        cash_eur REAL NOT NULL,
        portfolio_eur REAL NOT NULL,
        realized_pnl REAL NOT NULL DEFAULT 0,
        unrealized_pnl REAL NOT NULL DEFAULT 0,
        deployed_eur REAL NOT NULL DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS trader_positions (
        market TEXT PRIMARY KEY,
        qty REAL NOT NULL,
        avg_cost_eur REAL NOT NULL,
        opened_at TEXT NOT NULL,
        last_sync TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS trader_fills (
        fill_id TEXT PRIMARY KEY,
        order_id TEXT,
        client_order_id TEXT,
        suggestion_id INTEGER,
        market TEXT NOT NULL,
        side TEXT NOT NULL,
        qty REAL NOT NULL,
        price REAL NOT NULL,
        fee REAL NOT NULL DEFAULT 0,
        source TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """,
]

BOT_STATE_MIGRATION = """
CREATE TABLE IF NOT EXISTS bot_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    enabled INTEGER NOT NULL DEFAULT 1,
    current_state TEXT NOT NULL DEFAULT 'idle',
    last_poll_at TEXT,
    last_run_at TEXT,
    updated_at TEXT NOT NULL
);
INSERT OR IGNORE INTO bot_state (id, enabled, current_state, updated_at)
VALUES (1, 1, 'idle', datetime('now'));
"""


def run_migrations(conn: sqlite3.Connection) -> None:
    conn.executescript(MIGRATIONS[0])
    row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
    current = row[0] if row else 0
    if current == 0:
        for sql in MIGRATIONS[1:]:
            conn.executescript(sql)
        conn.executescript(BOT_STATE_MIGRATION)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    elif current == 1 and SCHEMA_VERSION >= 2:
        conn.executescript(BOT_STATE_MIGRATION)
        conn.execute("UPDATE schema_version SET version = ?", (SCHEMA_VERSION,))
    elif current < SCHEMA_VERSION:
        raise RuntimeError(f"Unsupported schema version {current}; expected {SCHEMA_VERSION}")
    conn.commit()
