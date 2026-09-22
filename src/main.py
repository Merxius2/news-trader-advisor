"""CLI entry point — Phase 0+1."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.bitvavo.markets_cache import refresh_markets_cache
from src.config_loader import load_settings
from src.pipeline import IngestPipeline
from src.scheduler import SchedulerService
from src.storage.db import db_session, init_db, log_activity, seed_trader_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("advisor")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="advisor",
        description="Crypto News Advisor — Bitvavo fork (Phase 0+1)",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init-db", help="Initialize SQLite schema and trader config")
    sub.add_parser("cache-markets", help="Refresh Bitvavo /markets cache (public API)")
    sub.add_parser("run-once", help="Run one ingest + analysis cycle and write hourly report")
    sub.add_parser("run-daemon", help="Run hourly digest scheduler (blocks)")
    return parser


def cmd_init_db() -> int:
    settings = load_settings()
    db_path = init_db(Path(settings.database.path))
    with db_session(db_path) as conn:
        seed_trader_config(
            conn,
            settings.trader.allocation_eur,
            settings.trader.reserve_eur,
            settings.trader.isolation,
        )
        log_activity(conn, "Database initialized", event_type="system")
    logger.info("Database ready at %s", db_path)
    return 0


def cmd_cache_markets() -> int:
    settings = load_settings()
    db_path = init_db(Path(settings.database.path))
    with db_session(db_path) as conn:
        count = refresh_markets_cache(conn, settings.bitvavo)
        log_activity(conn, f"Cached {count} Bitvavo markets", event_type="sync")
    logger.info("Cached %d markets", count)
    return 0


def cmd_run_once() -> int:
    settings = load_settings()
    db_path = init_db(Path(settings.database.path))
    with db_session(db_path) as conn:
        pipeline = IngestPipeline(conn, settings)
        result = pipeline.run_full_cycle()
        logger.info(
            "Cycle complete — fetched=%d stored=%d analyzed=%d suggestions=%d",
            result.fetched,
            result.stored,
            result.analyzed,
            result.suggestions,
        )
    return 0


def cmd_run_daemon() -> int:
    from src.web.jobs import run_news_cycle

    settings = load_settings()
    init_db(Path(settings.database.path))

    def poll_job() -> None:
        run_news_cycle(settings, write_report=False)

    def hourly_job() -> None:
        run_news_cycle(settings, write_report=True)

    service = SchedulerService(settings, hourly_job)
    service.add_news_poll_job(poll_job)
    service.start()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "init-db": cmd_init_db,
        "cache-markets": cmd_cache_markets,
        "run-once": cmd_run_once,
        "run-daemon": cmd_run_daemon,
    }
    return commands[args.command]()


if __name__ == "__main__":
    sys.exit(main())
