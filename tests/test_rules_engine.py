import unittest

from src.config_loader import SuggestionsConfig, WatchlistConfig, WatchlistMarket
from src.storage.models import CryptoAnalysisResult, WouldDo
from src.suggest.rules_engine import RulesEngine


def _analysis(**kwargs) -> CryptoAnalysisResult:
    base = dict(
        headline_id="1",
        base_assets=["BTC"],
        markets=["BTC-EUR"],
        event_type="etf_flow",
        sentiment="bullish",
        time_horizon="days",
        suggested_action="would_buy",
        confidence=0.8,
        source_quality="confirmed",
        rationale="Test",
        risk_factors=[],
        would_do=WouldDo(
            market="BTC-EUR",
            side="buy",
            notional_hint="small",
            entry_logic="x",
            exit_logic="y",
        ),
    )
    base.update(kwargs)
    return CryptoAnalysisResult(**base)


class RulesEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        wl = WatchlistConfig(
            markets=[WatchlistMarket(market="BTC-EUR", base="BTC")]
        )
        self.engine = RulesEngine(wl, SuggestionsConfig(), ["BTC-EUR"])

    def test_low_confidence_hidden(self) -> None:
        outcome = self.engine.apply(_analysis(confidence=0.4))
        self.assertFalse(outcome.visible)

    def test_rumor_cap(self) -> None:
        outcome = self.engine.apply(
            _analysis(source_quality="rumor", confidence=0.9)
        )
        self.assertLessEqual(outcome.result.confidence, 0.5)


if __name__ == "__main__":
    unittest.main()
