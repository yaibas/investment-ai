from __future__ import annotations

from typing import Any

import pandas as pd


def add_technical_indicators(history: pd.DataFrame) -> pd.DataFrame:
    """Add common trend, momentum, and volatility indicators."""
    df = history.copy()
    close = df["Close"]

    df["SMA_20"] = close.rolling(20).mean()
    df["SMA_50"] = close.rolling(50).mean()
    df["EMA_20"] = close.ewm(span=20, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    df["RSI_14"] = 100 - (100 / (1 + rs))

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_12 - ema_26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    df["daily_return"] = close.pct_change()
    df["volatility_20d"] = df["daily_return"].rolling(20).std() * (252**0.5) * 100

    return df


def summarize_technical_indicators(history: pd.DataFrame) -> dict[str, Any]:
    """Return the latest technical indicator values in JSON-friendly form."""
    df = add_technical_indicators(history)
    latest = df.iloc[-1]

    def value(name: str) -> float | None:
        raw = latest.get(name)
        if pd.isna(raw):
            return None
        return round(float(raw), 4)

    return {
        "sma_20": value("SMA_20"),
        "sma_50": value("SMA_50"),
        "ema_20": value("EMA_20"),
        "rsi_14": value("RSI_14"),
        "macd": value("MACD"),
        "macd_signal": value("MACD_signal"),
        "annualized_volatility_20d_percent": value("volatility_20d"),
    }
