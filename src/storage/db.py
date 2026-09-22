"""Database connection and helpers."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from src.storage.migrations import run_migrations
from src.storage.models import CryptoAnalysisResult, NewArticle

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "data" / "advisor.db"


def get_db_path() -> Path:
    override = os.environ.get("ADVISOR_DB_PATH")
    if override:
        return Path(override)
    return DEFAULT_DB_PATH


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | None = None) -> Path:
    conn = get_connection(path)
    try:
        run_migrations(conn)
    finally:
        conn.close()
    return path or get_db_path()


@contextmanager
def db_session(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    conn = get_connection(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log_activity(
    conn: sqlite3.Connection,
    message: str,
    *,
    level: str = "info",
    event_type: str = "system",
    metadata: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO activity_log (timestamp, level, event_type, message, metadata_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (utc_now_iso(), level, event_type, message, json.dumps(metadata) if metadata else None),
    )


def article_exists(conn: sqlite3.Connection, url: str, content_hash: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM articles WHERE url = ? OR content_hash = ? LIMIT 1",
        (url, content_hash),
    ).fetchone()
    return row is not None


def insert_article(conn: sqlite3.Connection, article: NewArticle) -> int | None:
    if article_exists(conn, article.url, article.content_hash):
        return None
    cur = conn.execute(
        """
        INSERT INTO articles (url, title, summary, source, published_at, content_hash, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            article.url,
            article.title,
            article.summary,
            article.source,
            article.published_at.isoformat() if article.published_at else None,
            article.content_hash,
            utc_now_iso(),
        ),
    )
    return int(cur.lastrowid)


def count_unanalyzed_articles(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS n FROM articles a
        LEFT JOIN analyses an ON an.article_id = a.id
        WHERE an.id IS NULL
        """
    ).fetchone()
    return int(row["n"]) if row else 0


def fetch_unanalyzed_articles(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT a.* FROM articles a
        LEFT JOIN analyses an ON an.article_id = a.id
        WHERE an.id IS NULL
        ORDER BY a.fetched_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def insert_analysis(
    conn: sqlite3.Connection,
    article_id: int,
    model: str,
    raw_response: str,
    parsed: CryptoAnalysisResult,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO analyses (article_id, model, raw_response, parsed_json, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (article_id, model, raw_response, parsed.model_dump_json(), utc_now_iso()),
    )
    return int(cur.lastrowid)


def insert_suggestion(
    conn: sqlite3.Connection,
    analysis_id: int,
    market: str,
    action: str,
    confidence: float,
    rationale: str,
    event_type: str,
    visible: bool,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO suggestions
        (analysis_id, market, action, confidence, rationale, event_type, visible, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            analysis_id,
            market,
            action,
            confidence,
            rationale,
            event_type,
            1 if visible else 0,
            utc_now_iso(),
        ),
    )
    return int(cur.lastrowid)


def seed_trader_config(
    conn: sqlite3.Connection,
    allocation_eur: float,
    reserve_eur: float,
    isolation_mode: str,
) -> None:
    conn.execute(
        """
        INSERT INTO trader_config (id, allocation_eur, reserve_eur, isolation_mode, attribution_start, subaccount_id)
        VALUES (1, ?, ?, ?, NULL, NULL)
        ON CONFLICT(id) DO UPDATE SET
            allocation_eur = excluded.allocation_eur,
            reserve_eur = excluded.reserve_eur,
            isolation_mode = excluded.isolation_mode
        """,
        (allocation_eur, reserve_eur, isolation_mode),
    )


def list_cached_markets(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT market FROM bitvavo_markets_cache WHERE status = 'trading' ORDER BY market"
    ).fetchall()
    return [r["market"] for r in rows]
