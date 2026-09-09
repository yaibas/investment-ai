from __future__ import annotations

from typing import Any

import yfinance as yf


def get_news(ticker: str, count: int = 5) -> list[dict[str, Any]]:
    """Fetch recent news items for a ticker via yfinance."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker が空です")
    if count < 1:
        return []

    raw_items = yf.Ticker(ticker).get_news(count=count, tab="news")
    results: list[dict[str, Any]] = []

    for item in raw_items[:count]:
        content = item.get("content", item)
        title = content.get("title")
        publisher = content.get("provider", {}).get("displayName")
        canonical = content.get("canonicalUrl", {}).get("url")
        pub_date = content.get("pubDate")

        if not title:
            continue

        results.append(
            {
                "title": title,
                "publisher": publisher,
                "published_at": pub_date,
                "url": canonical,
            }
        )

    return results
