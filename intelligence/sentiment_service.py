"""
FinBERT sentiment wrapper.

Delegates to intelligence.vendors.sentiment_analyzer — a self-contained copy
with no dependency on the FX project directory.

FinBERT models lazy-load on first call (~30s), then are cached in the singleton.
Subsequent calls are fast.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_sentiment(symbol: str, news_items: list[dict]) -> Optional[dict]:
    """
    Run FinBERT sentiment analysis on the provided news items for a symbol.

    Returns dict with:
      overall_sentiment: bullish | bearish | neutral
      overall_score:     -1.0 to +1.0
      trading_bias:      BUY | SELL | NEUTRAL
      bias_strength:     strong | moderate | weak | none
      positive_count, negative_count, neutral_count, news_count
      analyzed_items:    per-headline breakdown
    """
    if not news_items:
        return None
    try:
        from intelligence.vendors.sentiment_analyzer import get_sentiment_analyzer
        analyzer = get_sentiment_analyzer()
        return analyzer.get_sentiment_for_symbol(symbol, news_items)
    except Exception as e:
        logger.warning("Sentiment analysis failed for %s: %s", symbol, e)
        return None
