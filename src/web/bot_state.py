"""Bot daemon state persisted in SQLite."""

from __future__ import annotations

import sqlite3
from typing import Literal

BotState = Literal["idle", "news", "analysis", "trading", "stopped"]

_STATE_LABELS = {
    "idle": ("Idle", "Waiting for next news poll"),
    "news": ("Reading news", "Polling RSS and CryptoCompare feeds"),
    "analysis": ("Analyzing", "Running Ollama on new headlines"),
    "trading": ("Trading", "Order execution (Phase 6)"),
    "stopped": ("Stopped", "Bot paused — scheduler will not run cycles"),
}


def ensure_bot_state(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO bot_state (id, enabled, current_state, updated_at)
        VALUES (1, 1, 'idle', datetime('now'))
        """
    )


def get_bot_row(conn: sqlite3.Connection) -> sqlite3.Row:
    ensure_bot_state(conn)
    row = conn.execute("SELECT * FROM bot_state WHERE id = 1").fetchone()
    assert row is not None
    return row


def is_bot_enabled(conn: sqlite3.Connection) -> bool:
    return bool(get_bot_row(conn)["enabled"])


def set_bot_enabled(conn: sqlite3.Connection, enabled: bool) -> None:
    ensure_bot_state(conn)
    state: BotState = "idle" if enabled else "stopped"
    conn.execute(
        """
        UPDATE bot_state
        SET enabled = ?, current_state = ?, updated_at = datetime('now')
        WHERE id = 1
        """,
        (1 if enabled else 0, state),
    )


def set_bot_state(conn: sqlite3.Connection, state: BotState) -> None:
    ensure_bot_state(conn)
    conn.execute(
        """
        UPDATE bot_state SET current_state = ?, updated_at = datetime('now') WHERE id = 1
        """,
        (state,),
    )


def mark_poll_started(conn: sqlite3.Connection) -> None:
    ensure_bot_state(conn)
    conn.execute(
        """
        UPDATE bot_state
        SET last_poll_at = datetime('now'), updated_at = datetime('now')
        WHERE id = 1
        """
    )


def mark_run_finished(conn: sqlite3.Connection) -> None:
    ensure_bot_state(conn)
    conn.execute(
        """
        UPDATE bot_state
        SET last_run_at = datetime('now'), current_state = 'idle', updated_at = datetime('now')
        WHERE id = 1
        """
    )


def bot_status_dict(conn: sqlite3.Connection) -> dict:
    row = get_bot_row(conn)
    state = row["current_state"]
    title, detail = _STATE_LABELS.get(state, (state, ""))
    if state == "stopped" or not row["enabled"]:
        title, detail = _STATE_LABELS["stopped"]
    return {
        "enabled": bool(row["enabled"]),
        "state": state,
        "title": title,
        "detail": detail,
        "last_poll_at": row["last_poll_at"],
        "last_run_at": row["last_run_at"],
    }
