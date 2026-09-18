from __future__ import annotations

from datetime import datetime, timedelta

import feedparser


FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
]


def fetch_news(symbol: str, limit: int = 12) -> list[dict]:
    items: list[dict] = []
    cutoff = datetime.utcnow() - timedelta(hours=48)
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = getattr(entry, "title", "")
                link = getattr(entry, "link", "")
                ts = getattr(entry, "published", "")
                items.append({
                    "title": title,
                    "link": link,
                    "ts": ts,
                    "source": url,
                    "symbol": symbol,
                })
        except Exception:
            continue
    return items[:limit]
