"""Optional CryptoCompare news API."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from src.config_loader import CryptoCompareSource, get_cryptocompare_api_key
from src.ingest.deduper import content_hash, normalize_url
from src.storage.models import NewArticle

API_URL = "https://min-api.cryptocompare.com/data/v2/news/"


class CryptoCompareFetcher:
    def __init__(self, config: CryptoCompareSource, api_key: str | None) -> None:
        self.config = config
        self.api_key = api_key

    def fetch_all(self) -> list[NewArticle]:
        if not self.config.enabled or not self.api_key:
            return []
        articles: list[NewArticle] = []
        for category in self.config.categories:
            articles.extend(self._fetch_category(category))
        return articles

    def _fetch_category(self, category: str) -> list[NewArticle]:
        params = {"categories": category, "lang": "EN"}
        headers = {"authorization": f"Apikey {self.api_key}"}
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(API_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        out: list[NewArticle] = []
        for item in data.get("Data", []):
            url = normalize_url(item.get("url", ""))
            title = (item.get("title") or "").strip()
            if not url or not title:
                continue
            published = datetime.fromtimestamp(item.get("published_on", 0), tz=timezone.utc)
            source = item.get("source_info", {}).get("name") or "CryptoCompare"
            pub_iso = published.isoformat()
            out.append(
                NewArticle(
                    url=url,
                    title=title,
                    summary=(item.get("body") or "")[:4000],
                    source=source,
                    published_at=published,
                    content_hash=content_hash(title, pub_iso, source),
                )
            )
        return out


def fetch_cryptocompare_news(config: CryptoCompareSource) -> list[NewArticle]:
    return CryptoCompareFetcher(config, get_cryptocompare_api_key()).fetch_all()
