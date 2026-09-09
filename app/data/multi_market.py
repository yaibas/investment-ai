from __future__ import annotations

from typing import Any

from data.fundamental_data import get_fundamental_data
from data.market_data import get_market_data
from data.news_data import get_news


def get_multiple_market_data(
    tickers: list[str],
    period: str = "6mo",
    news_count: int = 5,
) -> list[dict[str, Any]]:
    """Fetch market, technical, fundamental, and recent-news data for multiple tickers."""
    results: list[dict[str, Any]] = []

    for ticker in tickers:
        normalized = ticker.strip().upper()
        try:
            market = get_market_data(normalized, period=period)

            try:
                fundamentals = get_fundamental_data(normalized)
            except Exception as exc:
                fundamentals = {"error": str(exc)}

            try:
                news = get_news(normalized, count=news_count)
            except Exception as exc:
                news = [{"error": str(exc)}]

            market["fundamentals"] = fundamentals
            market["news"] = news
            results.append(market)
        except Exception as exc:
            results.append(
                {
                    "ticker": normalized,
                    "error": str(exc),
                }
            )

    return results
