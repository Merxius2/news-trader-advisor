"""Post-LLM rules for crypto suggestions."""

from __future__ import annotations

from dataclasses import dataclass

from src.config_loader import SuggestionsConfig, WatchlistConfig
from src.storage.models import CryptoAnalysisResult


@dataclass
class RuleOutcome:
    result: CryptoAnalysisResult
    visible: bool
    notes: list[str]


class RulesEngine:
    def __init__(
        self,
        watchlist: WatchlistConfig,
        settings: SuggestionsConfig,
        listed_markets: list[str],
    ) -> None:
        self.watchlist = watchlist
        self.settings = settings
        self.listed_markets = set(listed_markets)

    def apply(self, analysis: CryptoAnalysisResult) -> RuleOutcome:
        notes: list[str] = []
        data = analysis.model_copy(deep=True)
        visible = True

        allowed = set(self.watchlist.market_symbols) & self.listed_markets
        data.markets = [m for m in data.markets if m in allowed]
        if not data.markets and data.suggested_action != "no_action":
            data.suggested_action = "no_action"
            notes.append("No watchlist/listed markets matched")

        if data.source_quality == "rumor":
            if data.confidence > self.settings.rumor_confidence_cap:
                data.confidence = self.settings.rumor_confidence_cap
                notes.append("Rumor cap applied")

        if data.confidence < self.settings.min_confidence_for_digest:
            visible = False
            notes.append("Below digest confidence threshold")

        if data.suggested_action == "no_action":
            visible = False
            notes.append("no_action hidden from highlights")

        return RuleOutcome(result=data, visible=visible, notes=notes)

    def detect_conflicts(self, recent: list[tuple[str, str]]) -> list[str]:
        """Return markets with conflicting actions within the recent window."""
        by_market: dict[str, set[str]] = {}
        for market, action in recent:
            by_market.setdefault(market, set()).add(action)
        return [m for m, actions in by_market.items() if len(actions) > 1]
