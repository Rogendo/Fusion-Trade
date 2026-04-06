"""
News Service for Forex Market

Fetches real-time forex news from multiple RSS feeds and news APIs.
Filters news by currency pair relevance.
"""

import feedparser
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
from dataclasses import dataclass

import logging
logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """Represents a single news article"""
    title: str
    summary: str
    source: str
    published: str
    link: str
    currencies: List[str]  # Related currency codes


class NewsService:
    """Service for fetching forex-related news"""

    # Forex news RSS feeds
    FOREX_FEEDS = {
        "ForexLive": "https://www.forexlive.com/feed/news",
        "FXStreet": "https://www.fxstreet.com/rss/news",
        "DailyFX": "https://www.dailyfx.com/feeds/market-news",
        "Investing": "https://www.investing.com/rss/news_301.rss",
    }

    # Currency mapping for filtering
    CURRENCY_KEYWORDS = {
        'EUR': ['euro', 'eur', 'ecb', 'european', 'eurozone', 'lagarde'],
        'USD': ['dollar', 'usd', 'fed', 'federal reserve', 'powell', 'fomc', 'us economy'],
        'GBP': ['pound', 'gbp', 'sterling', 'boe', 'bank of england', 'uk economy', 'brexit'],
        'JPY': ['yen', 'jpy', 'boj', 'bank of japan', 'kuroda', 'ueda', 'japan'],
        'AUD': ['aussie', 'aud', 'rba', 'australia', 'australian'],
        'NZD': ['kiwi', 'nzd', 'rbnz', 'new zealand'],
        'CAD': ['loonie', 'cad', 'boc', 'bank of canada', 'canadian'],
        'CHF': ['franc', 'chf', 'snb', 'swiss', 'switzerland'],
        'XAU': ['gold', 'xau', 'precious metal', 'bullion'],
        'XAG': ['silver', 'xag'],
    }

    def __init__(self):
        self._cache: Dict[str, List[NewsItem]] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=15)

    def _extract_currencies(self, text: str) -> List[str]:
        """Extract currency codes mentioned in text"""
        text_lower = text.lower()
        found_currencies = []

        for currency, keywords in self.CURRENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_currencies.append(currency)
                    break

        return list(set(found_currencies))

    def _parse_feed(self, feed_name: str, feed_url: str) -> List[NewsItem]:
        """Parse a single RSS feed"""
        news_items = []

        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:20]:  # Limit per feed
                title = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))

                # Clean HTML from summary
                summary = re.sub(r'<[^>]+>', '', summary)[:500]

                # Extract currencies mentioned
                currencies = self._extract_currencies(f"{title} {summary}")

                news_items.append(NewsItem(
                    title=title,
                    summary=summary,
                    source=feed_name,
                    published=entry.get('published', ''),
                    link=entry.get('link', ''),
                    currencies=currencies
                ))

        except Exception as e:
            logger.warning(f"Failed to parse feed {feed_name}: {e}")

        return news_items

    def fetch_all_news(self, force_refresh: bool = False) -> List[NewsItem]:
        """Fetch news from all configured feeds"""

        # Check cache
        if not force_refresh and self._cache_time:
            if datetime.now() - self._cache_time < self._cache_ttl:
                logger.info("Returning cached news")
                return self._cache.get('all', [])

        logger.info("Fetching fresh news from all feeds...")
        all_news = []

        for feed_name, feed_url in self.FOREX_FEEDS.items():
            news = self._parse_feed(feed_name, feed_url)
            all_news.extend(news)
            logger.info(f"Fetched {len(news)} articles from {feed_name}")

        # Sort by recency (most recent first)
        # Note: This is a simple sort; proper datetime parsing would be better
        all_news.sort(key=lambda x: x.published, reverse=True)

        # Update cache
        self._cache['all'] = all_news
        self._cache_time = datetime.now()

        logger.info(f"Total news articles fetched: {len(all_news)}")
        return all_news

    def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Get news relevant to a specific trading symbol"""

        # Extract base and quote currencies from symbol
        # e.g., "EURUSD=X" -> ["EUR", "USD"]
        clean_symbol = symbol.replace('=X', '').replace('=F', '')

        currencies = []
        if len(clean_symbol) >= 6:
            currencies = [clean_symbol[:3], clean_symbol[3:6]]
        elif clean_symbol == 'GC':
            currencies = ['XAU', 'USD']
        elif clean_symbol == 'SI':
            currencies = ['XAG', 'USD']

        # Fetch all news
        all_news = self.fetch_all_news()

        # Filter for relevant currencies
        relevant_news = []
        for news in all_news:
            if any(curr in news.currencies for curr in currencies):
                relevant_news.append(news)

        logger.info(f"Found {len(relevant_news)} news items for {symbol}")
        return relevant_news[:limit]

    def get_market_sentiment_summary(self) -> Dict:
        """Get a summary of market sentiment from news"""
        all_news = self.fetch_all_news()

        currency_mentions = {}
        for news in all_news:
            for curr in news.currencies:
                currency_mentions[curr] = currency_mentions.get(curr, 0) + 1

        return {
            'total_articles': len(all_news),
            'currency_mentions': currency_mentions,
            'top_currencies': sorted(currency_mentions.items(), key=lambda x: x[1], reverse=True)[:5],
            'sources': list(self.FOREX_FEEDS.keys()),
            'cache_age_seconds': (datetime.now() - self._cache_time).seconds if self._cache_time else None
        }

    def to_dict_list(self, news_items: List[NewsItem]) -> List[Dict]:
        """Convert NewsItem list to dict list for JSON serialization"""
        return [
            {
                'title': item.title,
                'summary': item.summary,
                'source': item.source,
                'published': item.published,
                'link': item.link,
                'currencies': item.currencies
            }
            for item in news_items
        ]


# Singleton instance
_news_service_instance: Optional[NewsService] = None

def get_news_service() -> NewsService:
    """Get or create NewsService singleton"""
    global _news_service_instance
    if _news_service_instance is None:
        _news_service_instance = NewsService()
    return _news_service_instance
