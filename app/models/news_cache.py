from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

class NewsCache(SQLModel, table=True):
    __tablename__ = 'news_cache'

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    overall_sentiment: str
    overall_score: float
    trading_bias: str
    bias_strength: str
    positive_count: int
    negative_count: int
    neutral_count: int
    news_count: int
    cache_expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
