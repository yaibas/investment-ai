from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf


INTERVALS: dict[str, str] = {
    "1分足": "1m",
    "2分足": "2m",
    "5分足": "5m",
    "15分足": "15m",
    "30分足": "30m",
    "1時間足": "60m",
}


def fetch_intraday_history(ticker: str, interval: str = "1m", period: str = "1d") -> pd.DataFrame:
    """Fetch recent intraday OHLCV data from Yahoo Finance via yfinance."""
    if interval not in INTERVALS.values():
        raise ValueError("対応していない時間足です")
    if period not in {"1d", "5d", "7d", "30d", "60d"}:
        raise ValueError("対応していない期間です")

    history = yf.Ticker(ticker).history(
        period=period,
        interval=interval,
        prepost=False,
        auto_adjust=False,
        repair=True,
    )
    if history.empty:
        raise ValueError("場中データを取得できませんでした")

    columns = ["Open", "High", "Low", "Close", "Volume"]
    available = [column for column in columns if column in history.columns]
    if "Close" not in available:
        raise ValueError("終値データが取得できませんでした")

    result = history[available].dropna(subset=["Close"]).copy()
    if result.empty:
        raise ValueError("有効な価格データがありません")
    return result


def add_intraday_indicators(history: pd.DataFrame) -> pd.DataFrame:
    """Add lightweight day-trading indicators to intraday price data."""
    data = history.copy()
    data["EMA9"] = data["Close"].ewm(span=9, adjust=False).mean()
    data["EMA20"] = data["Close"].ewm(span=20, adjust=False).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    data["RSI14"] = 100 - (100 / (1 + rs))

    if "Volume" in data:
        data["VolumeMA20"] = data["Volume"].rolling(20).mean()
    return data


def intraday_summary(data: pd.DataFrame) -> dict[str, Any]:
    """Summarize the most recent intraday data."""
    close = float(data["Close"].iloc[-1])
    previous = float(data["Close"].iloc[-2]) if len(data) >= 2 else close
    change_percent = ((close / previous) - 1) * 100 if previous else 0.0

    return {
        "latest_price": close,
        "change_percent": change_percent,
        "timestamp": data.index[-1].isoformat(),
        "high": float(data["High"].max()) if "High" in data else close,
        "low": float(data["Low"].min()) if "Low" in data else close,
        "volume": int(data["Volume"].sum()) if "Volume" in data else 0,
    }
