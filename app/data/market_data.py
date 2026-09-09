from __future__ import annotations

from typing import Any

import yfinance as yf

from analysis.technical import summarize_technical_indicators


def get_market_data(ticker: str, period: str = "6mo") -> dict[str, Any]:
    """Fetch recent market data and technical indicators via yfinance."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker が空です")

    history = yf.Ticker(ticker).history(
        period=period,
        interval="1d",
        auto_adjust=False,
    )

    if history.empty:
        raise ValueError(f"市場データを取得できませんでした: {ticker}")

    history = history.dropna(subset=["Close", "Volume"])
    if history.empty:
        raise ValueError(f"有効な市場データがありません: {ticker}")

    latest = history.iloc[-1]
    previous = history.iloc[-2] if len(history) >= 2 else None

    close = float(latest["Close"])
    previous_close = float(previous["Close"]) if previous is not None else close
    change_percent = ((close - previous_close) / previous_close * 100) if previous_close else 0.0

    return {
        "ticker": ticker,
        "date": history.index[-1].strftime("%Y-%m-%d"),
        "price": round(close, 2),
        "change_percent": round(change_percent, 2),
        "volume": int(latest["Volume"]),
        "open": round(float(latest["Open"]), 2),
        "high": round(float(latest["High"]), 2),
        "low": round(float(latest["Low"]), 2),
        "technical": summarize_technical_indicators(history),
    }
