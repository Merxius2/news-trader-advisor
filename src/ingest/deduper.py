"""Article deduplication."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from src.storage.models import NewArticle

_STRIP_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid"}


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k not in _STRIP_PARAMS]
    clean = parsed._replace(query=urlencode(query), fragment="")
    return urlunparse(clean)


def content_hash(title: str, published_at: str | None, source: str) -> str:
    raw = f"{title.strip().lower()}|{published_at or ''}|{source.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def is_duplicate(existing_urls: set[str], existing_hashes: set[str], article: NewArticle) -> bool:
    return article.url in existing_urls or article.content_hash in existing_hashes


def filter_new(articles: list[NewArticle], existing_urls: set[str], existing_hashes: set[str]) -> list[NewArticle]:
    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    out: list[NewArticle] = []
    for article in articles:
        if is_duplicate(existing_urls, existing_hashes, article):
            continue
        if article.url in seen_urls or article.content_hash in seen_hashes:
            continue
        seen_urls.add(article.url)
        seen_hashes.add(article.content_hash)
        out.append(article)
    return out


def cluster_near_duplicates(articles: list[NewArticle], window_minutes: int = 45) -> list[NewArticle]:
    """Keep first article per normalized title within clustering window (simplified Phase 1)."""
    if not articles:
        return []
    grouped: dict[str, NewArticle] = {}
    for article in sorted(articles, key=lambda a: a.published_at or a.content_hash):
        key = re.sub(r"\s+", " ", article.title.strip().lower())[:120]
        if key not in grouped:
            grouped[key] = article
    return list(grouped.values())
