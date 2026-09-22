"""Background news/analysis cycles for dashboard + scheduler."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from src.config_loader import Settings, load_settings
from src.pipeline import CycleResult, IngestPipeline
from src.storage.db import count_unanalyzed_articles, db_session, init_db, log_activity
from src.web.bot_state import is_bot_enabled, mark_poll_started, mark_run_finished, set_bot_state

logger = logging.getLogger(__name__)

_run_lock = threading.Lock()


@dataclass
class CyclePlan:
    unanalyzed: int
    skip_ingest: bool
    analysis_limit: int

    @property
    def backlog_mode(self) -> bool:
        return self.skip_ingest


def plan_cycle(settings: Settings, unanalyzed: int) -> CyclePlan:
    """Skip RSS ingest when the analysis queue is backed up."""
    threshold = settings.suggestions.backlog_skip_ingest_threshold
    skip_ingest = unanalyzed >= threshold
    analysis_limit = (
        settings.suggestions.backlog_max_articles_per_run
        if skip_ingest
        else settings.suggestions.max_articles_per_run
    )
    return CyclePlan(
        unanalyzed=unanalyzed,
        skip_ingest=skip_ingest,
        analysis_limit=analysis_limit,
    )


def run_news_cycle(settings: Settings | None = None, *, write_report: bool = False) -> bool:
    """Run ingest + analysis if bot enabled. Returns False if skipped or already running."""
    settings = settings or load_settings()
    if not _run_lock.acquire(blocking=False):
        logger.info("News cycle already running — skip")
        return False

    ingest = CycleResult(fetched=0, stored=0, analyzed=0, suggestions=0)
    analysis = CycleResult(fetched=0, stored=0, analyzed=0, suggestions=0)

    try:
        db_path = init_db(Path(settings.database.path))
        with db_session(db_path) as conn:
            if not is_bot_enabled(conn):
                log_activity(conn, "Bot paused — cycle skipped", event_type="idle")
                return False

            mark_poll_started(conn)
            plan = plan_cycle(settings, count_unanalyzed_articles(conn))

            if plan.backlog_mode:
                set_bot_state(conn, "analysis")
                log_activity(
                    conn,
                    f"Backlog mode — {plan.unanalyzed} queued, skipping RSS ingest",
                    event_type="system",
                    metadata={
                        "unanalyzed": plan.unanalyzed,
                        "analysis_limit": plan.analysis_limit,
                    },
                )
            else:
                set_bot_state(conn, "news")
                log_activity(conn, "Reading news feeds", event_type="news")

        if not plan.backlog_mode:
            with db_session(db_path) as conn:
                pipeline = IngestPipeline(conn, settings)
                ingest = pipeline.run_ingest_cycle()

        with db_session(db_path) as conn:
            set_bot_state(conn, "analysis")
            if ingest.stored:
                log_activity(
                    conn,
                    f"Ingested {ingest.stored} new headline(s)",
                    event_type="news",
                    metadata={"stored": ingest.stored, "fetched": ingest.fetched},
                )
            pipeline = IngestPipeline(conn, settings)
            analysis = pipeline.run_analysis_cycle(limit=plan.analysis_limit)

        if write_report:
            with db_session(db_path) as conn:
                pipeline = IngestPipeline(conn, settings)
                report_path = pipeline.reporter.write_hourly(conn)
                log_activity(
                    conn,
                    f"Hourly report written: {report_path.name}",
                    event_type="system",
                )

        with db_session(db_path) as conn:
            mark_run_finished(conn)
            remaining = count_unanalyzed_articles(conn)
            log_activity(
                conn,
                f"Cycle complete — stored={ingest.stored} analyzed={analysis.analyzed} "
                f"({remaining} still queued)",
                event_type="system",
                metadata={
                    "stored": ingest.stored,
                    "analyzed": analysis.analyzed,
                    "suggestions": analysis.suggestions,
                    "unanalyzed_remaining": remaining,
                    "backlog_mode": plan.backlog_mode,
                },
            )
        logger.info(
            "Cycle complete stored=%d analyzed=%d backlog=%s",
            ingest.stored,
            analysis.analyzed,
            plan.backlog_mode,
        )
        return True
    finally:
        _run_lock.release()


def trigger_news_cycle_async(settings: Settings | None = None) -> bool:
    settings = settings or load_settings()

    def _worker() -> None:
        try:
            run_news_cycle(settings, write_report=False)
        except Exception:
            logger.exception("Background news cycle failed")
            db_path = init_db(Path(settings.database.path))
            with db_session(db_path) as conn:
                mark_run_finished(conn)
                log_activity(conn, "News cycle failed — see logs", level="error", event_type="system")

    if not _run_lock.acquire(blocking=False):
        return False
    _run_lock.release()

    thread = threading.Thread(target=_worker, daemon=True, name="news-cycle")
    thread.start()
    return True
