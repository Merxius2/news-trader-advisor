"""Ingest and analysis pipeline."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from src.analyze.ollama_client import OllamaClient
from src.config_loader import (
    Settings,
    SourcesConfig,
    WatchlistConfig,
    get_cryptocompare_api_key,
    load_settings,
    load_sources,
    load_watchlist,
)
from src.enrich.market_mapper import MarketMapper
from src.ingest.cryptocompare_fetcher import CryptoCompareFetcher
from src.ingest.deduper import cluster_near_duplicates, filter_new
from src.ingest.rss_fetcher import RssFetcher
from src.output.reporter import MarkdownReporter
from src.storage.db import (
    fetch_unanalyzed_articles,
    insert_analysis,
    insert_article,
    insert_suggestion,
    list_cached_markets,
    log_activity,
    utc_now_iso,
)
from src.suggest.rules_engine import RulesEngine


@dataclass
class CycleResult:
    fetched: int
    stored: int
    analyzed: int
    suggestions: int


class IngestPipeline:
    def __init__(
        self,
        conn: sqlite3.Connection,
        settings: Settings | None = None,
        watchlist: WatchlistConfig | None = None,
        sources: SourcesConfig | None = None,
    ) -> None:
        self.conn = conn
        self.settings = settings or load_settings()
        self.watchlist = watchlist or load_watchlist()
        self.sources = sources or load_sources()
        self.listed_markets = list_cached_markets(conn) or self.watchlist.market_symbols
        self.mapper = MarketMapper(self.watchlist, self.listed_markets)
        self.rules = RulesEngine(self.watchlist, self.settings.suggestions, self.listed_markets)
        self.ollama = OllamaClient(self.settings.ollama)
        self.reporter = MarkdownReporter()

    def run_ingest_cycle(self) -> CycleResult:
        rss = RssFetcher(self.sources.rss).fetch_all()
        cc = CryptoCompareFetcher(self.sources.cryptocompare, get_cryptocompare_api_key()).fetch_all()
        combined = cluster_near_duplicates(rss + cc)

        existing_urls = {
            r["url"] for r in self.conn.execute("SELECT url FROM articles").fetchall()
        }
        existing_hashes = {
            r["content_hash"] for r in self.conn.execute("SELECT content_hash FROM articles").fetchall()
        }
        new_articles = filter_new(combined, existing_urls, existing_hashes)

        stored = 0
        for article in new_articles[: self.settings.suggestions.max_articles_per_run]:
            article_id = insert_article(self.conn, article)
            if article_id:
                stored += 1
                log_activity(
                    self.conn,
                    f"New headline: {article.title[:120]}",
                    event_type="news",
                    metadata={"source": article.source, "url": article.url},
                )

        self.conn.commit()
        return CycleResult(fetched=len(combined), stored=stored, analyzed=0, suggestions=0)

    def run_analysis_cycle(self, limit: int | None = None) -> CycleResult:
        if not self.ollama.health_check():
            log_activity(
                self.conn,
                "Ollama unavailable — skipping analysis cycle",
                level="warn",
                event_type="system",
            )
            self.conn.commit()
            return CycleResult(fetched=0, stored=0, analyzed=0, suggestions=0)

        batch_limit = limit if limit is not None else self.settings.suggestions.max_articles_per_run
        pending = fetch_unanalyzed_articles(self.conn, batch_limit)
        analyzed = 0
        suggestions_count = 0

        for row in pending:
            headline_id = str(row["id"])
            # Release DB lock while Ollama runs (can take minutes per headline).
            self.conn.commit()
            parsed, raw, model = self.ollama.analyze(
                headline_id,
                row["title"],
                row["summary"],
                row["source"],
                self.watchlist.market_symbols,
            )
            if parsed is None:
                log_activity(
                    self.conn,
                    f"Analysis parse failed: {row['title'][:80]}",
                    level="warn",
                    event_type="analysis",
                )
                self.conn.commit()
                continue

            parsed.markets = self.mapper.map_markets(
                f"{row['title']} {row['summary']}", parsed.markets
            )
            outcome = self.rules.apply(parsed)
            analysis_id = insert_analysis(
                self.conn, row["id"], model, raw, outcome.result
            )
            analyzed += 1

            primary_market = outcome.result.markets[0] if outcome.result.markets else "—"
            suggestion_id = insert_suggestion(
                self.conn,
                analysis_id,
                primary_market,
                outcome.result.suggested_action,
                outcome.result.confidence,
                outcome.result.rationale,
                outcome.result.event_type,
                outcome.visible,
            )
            suggestions_count += 1
            log_activity(
                self.conn,
                f"Analyzed → {outcome.result.suggested_action} {primary_market} ({outcome.result.confidence:.2f})",
                event_type="analysis",
                metadata={"suggestion_id": suggestion_id, "visible": outcome.visible},
            )

        self.conn.commit()
        return CycleResult(
            fetched=0, stored=0, analyzed=analyzed, suggestions=suggestions_count
        )

    def run_full_cycle(self) -> CycleResult:
        ingest = self.run_ingest_cycle()
        analysis = self.run_analysis_cycle()
        report_path = self.reporter.write_hourly(self.conn)
        log_activity(
            self.conn,
            f"Hourly report written: {report_path.name}",
            event_type="system",
            metadata={"path": str(report_path)},
        )
        self.conn.execute(
            """
            INSERT INTO runs (type, started_at, finished_at, articles_processed)
            VALUES ('hourly', ?, ?, ?)
            """,
            (utc_now_iso(), utc_now_iso(), ingest.stored),
        )
        self.conn.commit()
        return CycleResult(
            fetched=ingest.fetched,
            stored=ingest.stored,
            analyzed=analysis.analyzed,
            suggestions=analysis.suggestions,
        )
