"""Load YAML config and environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


@dataclass
class ScheduleConfig:
    hourly_digest_minute: int = 0
    news_poll_interval_minutes: int = 3
    daily_summary_hour: int = 18


@dataclass
class OllamaConfig:
    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:7b"
    fallback_model: str = "martain7r/finance-llama-8b:q4_k_m"
    temperature: float = 0.2
    timeout_seconds: int = 120
    prompts_module: str = "crypto"


@dataclass
class SuggestionsConfig:
    min_confidence_for_digest: float = 0.5
    min_confidence_for_highlight: float = 0.75
    max_articles_per_run: int = 30
    backlog_skip_ingest_threshold: int = 10
    backlog_max_articles_per_run: int = 5
    rumor_confidence_cap: float = 0.5


@dataclass
class BitvavoConfig:
    rest_url: str = "https://api.bitvavo.com/v2"
    ws_url: str = "wss://ws.bitvavo.com/v2/"
    readonly: bool = True
    sync_interval_seconds: int = 45
    quote_currency: str = "EUR"


@dataclass
class TraderConfig:
    allocation_eur: float = 500.0
    reserve_eur: float = 50.0
    isolation: str = "tagged_orders"
    client_order_id_prefix: str = "advisor"
    subaccount_id: str | None = None
    attribution_start: str | None = None


@dataclass
class DatabaseConfig:
    path: str = "data/advisor.db"


@dataclass
class Settings:
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    suggestions: SuggestionsConfig = field(default_factory=SuggestionsConfig)
    bitvavo: BitvavoConfig = field(default_factory=BitvavoConfig)
    trader: TraderConfig = field(default_factory=TraderConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)


@dataclass
class WatchlistMarket:
    market: str
    base: str
    notes: str = ""


@dataclass
class WatchlistConfig:
    markets: list[WatchlistMarket] = field(default_factory=list)

    @property
    def market_symbols(self) -> list[str]:
        return [m.market for m in self.markets]

    @property
    def base_assets(self) -> list[str]:
        return [m.base for m in self.markets]


@dataclass
class RssSource:
    name: str
    url: str


@dataclass
class CryptoCompareSource:
    enabled: bool = False
    categories: list[str] = field(default_factory=list)


@dataclass
class SourcesConfig:
    rss: list[RssSource] = field(default_factory=list)
    cryptocompare: CryptoCompareSource = field(default_factory=CryptoCompareSource)


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load_settings(path: Path | None = None) -> Settings:
    load_dotenv(ROOT / ".env")
    data = _read_yaml(path or CONFIG_DIR / "settings.yaml")
    return Settings(
        schedule=ScheduleConfig(**data.get("schedule", {})),
        ollama=OllamaConfig(**data.get("ollama", {})),
        suggestions=SuggestionsConfig(**data.get("suggestions", {})),
        bitvavo=BitvavoConfig(**data.get("bitvavo", {})),
        trader=TraderConfig(**data.get("trader", {})),
        database=DatabaseConfig(**data.get("database", {})),
    )


def load_watchlist(path: Path | None = None) -> WatchlistConfig:
    data = _read_yaml(path or CONFIG_DIR / "watchlist.yaml")
    markets = [WatchlistMarket(**m) for m in data.get("markets", [])]
    return WatchlistConfig(markets=markets)


def load_sources(path: Path | None = None) -> SourcesConfig:
    data = _read_yaml(path or CONFIG_DIR / "sources.yaml")
    rss = [RssSource(**r) for r in data.get("rss", [])]
    cc = data.get("cryptocompare", {}) or {}
    return SourcesConfig(
        rss=rss,
        cryptocompare=CryptoCompareSource(
            enabled=bool(cc.get("enabled", False)),
            categories=list(cc.get("categories", [])),
        ),
    )


def get_cryptocompare_api_key() -> str | None:
    load_dotenv(ROOT / ".env")
    return os.environ.get("CRYPTOCOMPARE_API_KEY") or None
