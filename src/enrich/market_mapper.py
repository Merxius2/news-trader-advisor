"""Map headline text to Bitvavo watchlist markets."""

from __future__ import annotations

import re

from src.config_loader import WatchlistConfig

_ASSET_PATTERNS: dict[str, re.Pattern[str]] = {
    "BTC": re.compile(r"\b(bitcoin|btc)\b", re.I),
    "ETH": re.compile(r"\b(ethereum|eth|ether)\b", re.I),
    "SOL": re.compile(r"\b(solana|sol)\b", re.I),
    "XRP": re.compile(r"\b(xrp|ripple)\b", re.I),
    "ADA": re.compile(r"\b(cardano|ada)\b", re.I),
}


class MarketMapper:
    def __init__(self, watchlist: WatchlistConfig, listed_markets: list[str] | None = None) -> None:
        self.watchlist = watchlist
        self.listed_markets = set(listed_markets or watchlist.market_symbols)

    def extract_base_assets(self, text: str) -> list[str]:
        found: list[str] = []
        for base in self.watchlist.base_assets:
            pattern = _ASSET_PATTERNS.get(base)
            if pattern and pattern.search(text):
                found.append(base)
        return found

    def map_markets(self, text: str, llm_markets: list[str] | None = None) -> list[str]:
        markets: list[str] = []
        if llm_markets:
            for m in llm_markets:
                if m in self.listed_markets and m in self.watchlist.market_symbols:
                    markets.append(m)
        for base in self.extract_base_assets(text):
            market = f"{base}-EUR"
            if market in self.listed_markets and market not in markets:
                markets.append(market)
        return markets
