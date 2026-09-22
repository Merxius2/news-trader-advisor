"""Crypto RSS ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from src.config_loader import RssSource
from src.ingest.deduper import content_hash, normalize_url
from src.storage.models import NewArticle


def _parse_published(entry: feedparser.FeedParserDict) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if getattr(entry, "updated_parsed", None):
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    if entry.get("published"):
        try:
            return parsedate_to_datetime(entry["published"]).astimezone(timezone.utc)
        except (TypeError, ValueError):
            return None
    return None


def parse_rss_entry(entry: feedparser.FeedParserDict, source_name: str) -> NewArticle | None:
    link = entry.get("link") or entry.get("id")
    title = (entry.get("title") or "").strip()
    if not link or not title:
        return None
    url = normalize_url(link)
    summary = (entry.get("summary") or entry.get("description") or "").strip()
    published = _parse_published(entry)
    pub_iso = published.isoformat() if published else None
    return NewArticle(
        url=url,
        title=title,
        summary=summary[:4000],
        source=source_name,
        published_at=published,
        content_hash=content_hash(title, pub_iso, source_name),
    )


class RssFetcher:
    def __init__(self, sources: list[RssSource]) -> None:
        self.sources = sources

    def fetch_all(self) -> list[NewArticle]:
        articles: list[NewArticle] = []
        for source in self.sources:
            articles.extend(self.fetch_source(source))
        return articles

    def fetch_source(self, source: RssSource) -> list[NewArticle]:
        parsed = feedparser.parse(source.url)
        out: list[NewArticle] = []
        for entry in parsed.entries:
            article = parse_rss_entry(entry, source.name)
            if article:
                out.append(article)
        return out


def fetch_rss_feeds(sources: list[RssSource]) -> list[NewArticle]:
    return RssFetcher(sources).fetch_all()
