from __future__ import annotations

from typing import Any

from data.market_data import get_market_data


def get_multiple_market_data(
    tickers: list[str], period: str = "1mo"
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for ticker in tickers:
        try:
            results.append(get_market_data(ticker, period=period))
        except Exception as exc:
            results.append({"ticker": ticker.strip().upper(), "error": str(exc)})
    return results
