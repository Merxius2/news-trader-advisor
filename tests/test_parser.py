import unittest

from src.analyze.parser import parse_analysis_response


SAMPLE = """
{
  "headline_id": "42",
  "base_assets": ["BTC"],
  "markets": ["BTC-EUR"],
  "event_type": "etf_flow",
  "sentiment": "bullish",
  "time_horizon": "days",
  "suggested_action": "would_buy",
  "confidence": 0.72,
  "source_quality": "confirmed",
  "rationale": "ETF inflows support spot demand.",
  "risk_factors": ["Already up today"],
  "would_do": {
    "market": "BTC-EUR",
    "side": "buy",
    "notional_hint": "small",
    "entry_logic": "Scale in",
    "exit_logic": "Take profit +5%"
  },
  "disclaimer": "Advisory only"
}
"""


class ParserTests(unittest.TestCase):
    def test_parse_valid_json(self) -> None:
        result = parse_analysis_response(SAMPLE, "42")
        assert result is not None
        self.assertEqual(result.markets, ["BTC-EUR"])
        self.assertEqual(result.confidence, 0.72)


if __name__ == "__main__":
    unittest.main()
