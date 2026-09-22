"""Pydantic schemas and row dataclasses for storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

EventType = Literal["trade", "news", "analysis", "sync", "system", "idle"]
LogLevel = Literal["info", "warn", "error"]
SuggestedAction = Literal[
    "would_buy", "would_sell", "would_reduce", "would_hold", "no_action"
]
Sentiment = Literal["bullish", "bearish", "neutral", "mixed"]
TimeHorizon = Literal["minutes", "hours", "days", "weeks"]
SourceQuality = Literal["confirmed", "reported", "opinion", "rumor"]
CryptoEventType = Literal[
    "hack",
    "regulation",
    "etf_flow",
    "listing",
    "protocol_upgrade",
    "macro",
    "adoption",
    "exchange",
    "stablecoin",
    "whale_move",
    "legal",
    "other",
]


class WouldDo(BaseModel):
    market: str
    side: Literal["buy", "sell"]
    notional_hint: Literal["small", "medium", "large"]
    entry_logic: str
    exit_logic: str


class CryptoAnalysisResult(BaseModel):
    headline_id: str
    base_assets: list[str] = Field(default_factory=list)
    markets: list[str] = Field(default_factory=list)
    event_type: CryptoEventType
    sentiment: Sentiment
    time_horizon: TimeHorizon
    suggested_action: SuggestedAction
    confidence: float = Field(ge=0.0, le=1.0)
    source_quality: SourceQuality
    rationale: str
    risk_factors: list[str] = Field(default_factory=list)
    would_do: Optional[WouldDo] = None
    disclaimer: str = "Advisory only — not executed — not financial advice"

    @field_validator("confidence")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        return round(v, 4)


@dataclass
class ArticleRow:
    id: Optional[int]
    url: str
    title: str
    summary: str
    source: str
    published_at: Optional[datetime]
    content_hash: str
    fetched_at: datetime


@dataclass
class NewArticle:
    url: str
    title: str
    summary: str
    source: str
    published_at: Optional[datetime]
    content_hash: str
