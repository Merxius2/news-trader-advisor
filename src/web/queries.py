"""Read-only dashboard queries."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.analyze.ollama_client import OllamaClient
from src.config_loader import Settings, WatchlistConfig, load_settings, load_watchlist
from src.web.bot_state import bot_status_dict


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_time_short(value: Optional[str]) -> str:
    dt = _parse_ts(value)
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone()
    return local.strftime("%H:%M")


def format_relative(value: Optional[str]) -> str:
    dt = _parse_ts(value)
    if not dt:
        return "never"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


def action_tag_class(action: str) -> str:
    if action in ("would_buy",):
        return "tag-buy"
    if action in ("would_sell", "would_reduce"):
        return "tag-sell"
    return "tag-hold"


def fetch_activity_log(
    conn: sqlite3.Connection,
    *,
    event_type: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if event_type and event_type != "all":
        rows = conn.execute(
            """
            SELECT id, timestamp, level, event_type, message, metadata_json
            FROM activity_log
            WHERE event_type = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (event_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, timestamp, level, event_type, message, metadata_json
            FROM activity_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    items = []
    for row in rows:
        meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        items.append(
            {
                "id": row["id"],
                "time": format_time_short(row["timestamp"]),
                "event_type": row["event_type"],
                "level": row["level"],
                "message": row["message"],
                "metadata": meta,
            }
        )
    return items


def fetch_suggestions(conn: sqlite3.Connection, *, limit: int = 10) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT s.id, s.market, s.action, s.confidence, s.rationale, s.event_type,
               s.visible, s.created_at,
               art.title, art.source, art.published_at, art.url,
               an.parsed_json, an.model
        FROM suggestions s
        JOIN analyses an ON an.id = s.analysis_id
        JOIN articles art ON art.id = an.article_id
        ORDER BY s.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    out: list[dict[str, Any]] = []
    for row in rows:
        parsed = json.loads(row["parsed_json"])
        would_do = parsed.get("would_do")
        would_do_text = None
        if would_do:
            would_do_text = (
                f"{would_do.get('side', '').title()} {would_do.get('market', row['market'])} "
                f"({would_do.get('notional_hint', 'small')}) — {would_do.get('entry_logic', '')}"
            )
        risks = parsed.get("risk_factors") or []
        out.append(
            {
                "id": row["id"],
                "title": row["title"],
                "source": row["source"],
                "market": row["market"],
                "action": row["action"],
                "action_class": action_tag_class(row["action"]),
                "confidence": row["confidence"],
                "rationale": row["rationale"],
                "event_type": row["event_type"],
                "source_quality": parsed.get("source_quality", "reported"),
                "visible": bool(row["visible"]),
                "time": format_time_short(row["created_at"]),
                "would_do_text": would_do_text,
                "risks": risks,
                "model": row["model"],
            }
        )
    return out


def fetch_watchlist_signals(
    conn: sqlite3.Connection,
    watchlist: WatchlistConfig,
) -> list[dict[str, Any]]:
    items = []
    for market in watchlist.markets:
        row = conn.execute(
            """
            SELECT s.action, s.confidence, s.created_at
            FROM suggestions s
            WHERE s.market = ?
            ORDER BY s.created_at DESC
            LIMIT 1
            """,
            (market.market,),
        ).fetchone()
        if row:
            items.append(
                {
                    "market": market.market,
                    "base": market.base,
                    "notes": market.notes,
                    "action": row["action"],
                    "action_class": action_tag_class(row["action"]),
                    "confidence": row["confidence"],
                    "has_signal": True,
                }
            )
        else:
            items.append(
                {
                    "market": market.market,
                    "base": market.base,
                    "notes": market.notes,
                    "action": "no_action",
                    "action_class": "tag-hold",
                    "confidence": None,
                    "has_signal": False,
                }
            )
    return items


def fetch_trader_config(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM trader_config WHERE id = 1").fetchone()


def system_status(conn: sqlite3.Connection, settings: Settings) -> dict[str, Any]:
    bot = bot_status_dict(conn)
    ollama_ok = OllamaClient(settings.ollama).health_check()
    last_poll = bot.get("last_poll_at") or bot.get("last_run_at")
    article_count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    suggestion_count = conn.execute("SELECT COUNT(*) FROM suggestions").fetchone()[0]
    trader = fetch_trader_config(conn)
    allocation = trader["allocation_eur"] if trader else settings.trader.allocation_eur
    return {
        "ollama_ok": ollama_ok,
        "ollama_model": settings.ollama.model,
        "news_poll_ago": format_relative(last_poll),
        "bitvavo_status": "Phase 3",
        "allocation_eur": allocation,
        "article_count": article_count,
        "suggestion_count": suggestion_count,
        "bot": bot,
    }


def list_digest_files(reports_dir: Path) -> list[dict[str, str]]:
    if not reports_dir.is_dir():
        return []
    files = sorted(reports_dir.glob("*.md"), reverse=True)
    return [{"name": f.name, "path": str(f)} for f in files[:50]]
