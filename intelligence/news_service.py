"""
News service wrapper.

Delegates to intelligence.vendors.news_service — a self-contained copy
with no dependency on the FX project directory.

Aggregates ForexLive, FXStreet, DailyFX, and Investing.com feeds with a
15-min cache. Returns list of {title, summary, source, published, link, currencies}.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_news_for_symbol(symbol: str, limit: int = 10) -> list[dict]:
    """
    Fetch recent news headlines for a symbol.
    Returns list of {title, summary, source, published, link, currencies}.
    Results are cached for 15 minutes by the underlying service.
    """
    try:
        from intelligence.vendors.news_service import get_news_service
        svc    = get_news_service()
        items  = svc.get_news_for_symbol(symbol, limit=limit)
        return svc.to_dict_list(items)
    except Exception as e:
        logger.warning("News fetch failed for %s: %s", symbol, e)
        return []
