"""Ollama HTTP client for headline analysis."""

from __future__ import annotations

import httpx

from src.analyze.parser import parse_analysis_response
from src.analyze.prompts_crypto import SYSTEM_PROMPT, build_analysis_prompt
from src.config_loader import OllamaConfig
from src.storage.models import CryptoAnalysisResult


class OllamaClient:
    def __init__(self, config: OllamaConfig) -> None:
        self.config = config

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.config.base_url.rstrip('/')}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def analyze(
        self,
        headline_id: str,
        title: str,
        summary: str,
        source: str,
        watchlist_markets: list[str],
    ) -> tuple[CryptoAnalysisResult | None, str, str]:
        prompt = build_analysis_prompt(headline_id, title, summary, source, watchlist_markets)
        raw, model_used = self._generate(prompt, self.config.model)
        parsed = parse_analysis_response(raw, headline_id)
        if parsed is None and self.config.fallback_model:
            raw, model_used = self._generate(prompt, self.config.fallback_model)
            parsed = parse_analysis_response(raw, headline_id)
        return parsed, raw, model_used

    def _generate(self, prompt: str, model: str) -> tuple[str, str]:
        url = f"{self.config.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
            "stream": False,
            "format": "json",
            "options": {"temperature": self.config.temperature},
        }
        with httpx.Client(timeout=float(self.config.timeout_seconds)) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("response", ""), model


def analyze_headline(
    client: OllamaClient,
    headline_id: str,
    title: str,
    summary: str,
    source: str,
    watchlist_markets: list[str],
) -> tuple[CryptoAnalysisResult | None, str, str]:
    return client.analyze(headline_id, title, summary, source, watchlist_markets)
