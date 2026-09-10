from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

KUN_API_BASE = os.getenv("KUN_DATA_API_BASE", "https://kun.pro/api").rstrip("/")
KUN_DATA_TOKEN = os.getenv("KUN_DATA_TOKEN", "").strip()


def realtime_enabled() -> bool:
    return bool(KUN_DATA_TOKEN)


def _headers() -> dict[str, str]:
    if not KUN_DATA_TOKEN:
        raise RuntimeError("KUN_DATA_TOKEN が設定されていません")
    return {"Authorization": f"Bearer {KUN_DATA_TOKEN}", "Accept": "application/json"}


def _request(path: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        f"{KUN_API_BASE}/{path.lstrip('/')}",
        params=params,
        headers=_headers(),
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") not in (None, 200):
        raise RuntimeError(payload.get("msg") or "市場データAPIからエラーが返されました")
    return payload


def _symbol(ticker: str) -> str:
    code = ticker.split(".", 1)[0]
    return f"TSE:{code}"


def fetch_realtime_snapshot(ticker: str) -> dict[str, Any]:
    payload = _request(
        "exchange",
        {"market": "JP", "venue": "TSE", "symbol": _symbol(ticker)},
    )
    items = payload.get("list") or []
    if not items:
        raise ValueError(f"リアルタイム価格を取得できませんでした: {ticker}")
    item = items[0]
    ts = item.get("timestamp") or item.get("time")
    return {
        "ticker": ticker,
        "price": float(item["price"]),
        "change": float(item.get("ch", 0.0)),
        "change_percent": float(item.get("chp", 0.0)),
        "high": float(item.get("high", item["price"])),
        "low": float(item.get("low", item["price"])),
        "open": float(item.get("open", item["price"])),
        "prev_close": float(item.get("prev_close", 0.0)),
        "volume": int(float(item.get("volume", 0))),
        "timestamp": _timestamp_text(ts),
        "source": "KUN realtime market data",
    }


def fetch_realtime_history(ticker: str, interval: str = "1", count: int = 200) -> pd.DataFrame:
    payload = _request(
        "history",
        {"market": "JP", "symbol": _symbol(ticker), "interval": interval, "count": count},
    )
    rows = payload.get("list") or []
    if not rows:
        raise ValueError(f"ローソク足データを取得できませんでした: {ticker}")

    frame = pd.DataFrame(rows).rename(
        columns={
            "timestamp": "Timestamp",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    required = ["Open", "High", "Low", "Close", "Volume", "Timestamp"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"リアルタイム履歴に必要な列がありません: {missing}")

    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], unit="s", utc=True)
    frame = frame.set_index("Timestamp").sort_index()
    frame.index = frame.index.tz_convert("Asia/Tokyo")
    return frame[["Open", "High", "Low", "Close", "Volume"]].astype(float)


def _timestamp_text(value: Any) -> str:
    if value is None:
        return "不明"
    try:
        dt = datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except (TypeError, ValueError, OSError):
        return str(value)
