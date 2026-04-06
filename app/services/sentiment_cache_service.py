from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlmodel import Session, select
from app.models.news_cache import NewsCache
from intelligence.news_service import get_news_for_symbol
from intelligence.sentiment_service import get_sentiment

logger = logging.getLogger(__name__)

class SentimentCacheService:
    def __init__(self, db: Session):
        self.db = db

    def get_cached_sentiment(self, symbol: str) -> Optional[dict]:
        """Retrieve valid sentiment from cache."""
        now = datetime.now(timezone.utc)
        statement = select(NewsCache).where(
            NewsCache.symbol == symbol,
            NewsCache.cache_expires_at > now
        )
        result = self.db.exec(statement).first()
        if result:
            return {
                'overall_sentiment': result.overall_sentiment,
                'overall_score': result.overall_score,
                'trading_bias': result.trading_bias,
                'bias_strength': result.bias_strength,
                'positive_count': result.positive_count,
                'negative_count': result.negative_count,
                'neutral_count': result.neutral_count,
                'news_count': result.news_count
            }
        return None

    def update_cache(self, symbol: str) -> Optional[dict]:
        """Run sentiment analysis and update cache (1 hour expiry)."""
        try:
            news_items = get_news_for_symbol(symbol, limit=10)
            raw = get_sentiment(symbol, news_items)
            if not raw:
                return None

            # Delete old entries
            old_entries = self.db.exec(select(NewsCache).where(NewsCache.symbol == symbol)).all()
            for old in old_entries:
                self.db.delete(old)

            new_cache = NewsCache(
                symbol=symbol,
                overall_sentiment=raw.get('overall_sentiment', 'neutral'),
                overall_score=raw.get('overall_score', 0.0),
                trading_bias=raw.get('trading_bias', 'NEUTRAL'),
                bias_strength=raw.get('bias_strength', 'none'),
                positive_count=raw.get('positive_count', 0),
                negative_count=raw.get('negative_count', 0),
                neutral_count=raw.get('neutral_count', 0),
                news_count=raw.get('news_count', len(news_items)),
                cache_expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            self.db.add(new_cache)
            self.db.commit()
            return self.get_cached_sentiment(symbol)
        except Exception as e:
            logger.error(f'Failed to update sentiment cache for {symbol}: {e}')
            return None
