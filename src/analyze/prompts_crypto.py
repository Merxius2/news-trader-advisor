"""Crypto-specific Ollama prompts (Bitvavo fork)."""

from __future__ import annotations

SYSTEM_PROMPT = """You are a crypto market analyst for a local trading advisor on Bitvavo (EUR spot pairs only).
Analyze news headlines and output STRICT JSON only — no markdown, no prose outside JSON.

Rules:
- Reason about spot markets on Bitvavo (EUR pairs), not perpetuals unless the article mentions them.
- Map assets only to the provided watchlist markets.
- Weigh volatility, EU/NL regulation, liquidity, and source quality (confirmed vs rumor).
- Never invent prices, wallet addresses, or on-chain stats not in the article.
- confidence is 0.0–1.0. Use no_action when unclear.
- Include plain-language rationale and concrete risk_factors.
"""


def build_analysis_prompt(
    headline_id: str,
    title: str,
    summary: str,
    source: str,
    watchlist_markets: list[str],
) -> str:
    markets_csv = ", ".join(watchlist_markets) or "none"
    return f"""Analyze this crypto headline for a Bitvavo spot advisor.

headline_id: {headline_id}
source: {source}
title: {title}
summary: {summary}

Watchlist markets (only suggest these): {markets_csv}

Return JSON matching this schema:
{{
  "headline_id": "{headline_id}",
  "base_assets": ["BTC"],
  "markets": ["BTC-EUR"],
  "event_type": "etf_flow|regulation|listing|protocol_upgrade|macro|adoption|exchange|stablecoin|whale_move|legal|hack|other",
  "sentiment": "bullish|bearish|neutral|mixed",
  "time_horizon": "minutes|hours|days|weeks",
  "suggested_action": "would_buy|would_sell|would_reduce|would_hold|no_action",
  "confidence": 0.0,
  "source_quality": "confirmed|reported|opinion|rumor",
  "rationale": "...",
  "risk_factors": ["..."],
  "would_do": {{
    "market": "BTC-EUR",
    "side": "buy|sell",
    "notional_hint": "small|medium|large",
    "entry_logic": "...",
    "exit_logic": "..."
  }},
  "disclaimer": "Advisory only — not executed — not financial advice"
}}
"""
