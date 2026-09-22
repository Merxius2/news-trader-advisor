"""Markdown report output."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"


class MarkdownReporter:
    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or REPORTS_DIR

    def write_hourly(self, conn: sqlite3.Connection, run_started: datetime | None = None) -> Path:
        return write_hourly_report(conn, self.reports_dir, run_started)


def write_hourly_report(
    conn: sqlite3.Connection,
    reports_dir: Path | None = None,
    run_started: datetime | None = None,
) -> Path:
    out_dir = reports_dir or REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    now = run_started or datetime.now(timezone.utc)
    filename = now.strftime("%Y-%m-%d_%H.md")
    path = out_dir / filename

    suggestions = conn.execute(
        """
        SELECT s.*, a.title, a.source
        FROM suggestions s
        JOIN analyses an ON an.id = s.analysis_id
        JOIN articles a ON a.id = an.article_id
        WHERE s.created_at >= datetime('now', '-1 hour')
        ORDER BY s.confidence DESC
        """
    ).fetchall()

    lines = [
        f"# Hourly digest — {now.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Suggestions this hour: **{len(suggestions)}**",
        "",
    ]
    for row in suggestions:
        vis = "visible" if row["visible"] else "log-only"
        lines.extend(
            [
                f"## {row['title'][:120]}",
                f"- Source: {row['source']}",
                f"- Market: `{row['market']}` · Action: **{row['action']}** · Confidence: {row['confidence']:.2f}",
                f"- Event: {row['event_type']} · Status: {vis}",
                "",
                row["rationale"],
                "",
            ]
        )
    if not suggestions:
        lines.append("_No new suggestions in the last hour._")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
