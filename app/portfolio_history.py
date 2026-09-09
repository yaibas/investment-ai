from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from paper_portfolio import fetch_latest_prices, load_portfolio


def load_history(path: str) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("履歴ファイルの形式が不正です")
    return payload


def save_history(history: list[dict[str, Any]], path: str) -> None:
    Path(path).write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def record_snapshot(portfolio_file: str, history_file: str) -> dict[str, Any]:
    portfolio = load_portfolio(portfolio_file)
    tickers = list(portfolio.positions)
    prices = fetch_latest_prices(tickers) if tickers else {}
    valuation = portfolio.valuation(prices)
    snapshot = {
        "date": date.today().isoformat(),
        "total_value": float(valuation["total_value"]),
        "cash": float(valuation["cash"]),
        "positions_value": float(valuation["positions_value"]),
    }

    history = load_history(history_file)
    existing = next(
        (item for item in history if item.get("date") == snapshot["date"]), None
    )
    if existing is None:
        history.append(snapshot)
    else:
        existing.update(snapshot)
    history.sort(key=lambda item: item["date"])
    save_history(history, history_file)
    return snapshot


def performance(history: list[dict[str, Any]]) -> dict[str, float | None]:
    values = [
        float(item["total_value"])
        for item in history
        if item.get("total_value") is not None
    ]
    if not values:
        return {"total_return_percent": None, "max_drawdown_percent": None}

    initial = values[0]
    total_return = (values[-1] / initial - 1) * 100 if initial else 0.0

    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = (value / peak - 1) * 100 if peak else 0.0
        max_drawdown = min(max_drawdown, drawdown)

    return {
        "total_return_percent": round(total_return, 2),
        "max_drawdown_percent": round(max_drawdown, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="仮想ポートフォリオの運用履歴を記録・表示します"
    )
    parser.add_argument("--portfolio-file", default="paper_portfolio.json")
    parser.add_argument("--history-file", default="portfolio_history.json")
    parser.add_argument("--record", action="store_true", help="今日の評価額を記録")
    args = parser.parse_args()

    history = load_history(args.history_file)
    if args.record:
        snapshot = record_snapshot(args.portfolio_file, args.history_file)
        history = load_history(args.history_file)
        print(f"記録日: {snapshot['date']}")
        print(f"総評価額: {snapshot['total_value']:.2f}")

    stats = performance(history)
    print("===== 運用履歴 =====")
    print(f"記録日数: {len(history)}")
    if stats["total_return_percent"] is None:
        print("リターン: データ不足")
        print("最大ドローダウン: データ不足")
    else:
        print(f"累積リターン: {stats['total_return_percent']:.2f}%")
        print(f"最大ドローダウン: {stats['max_drawdown_percent']:.2f}%")

    for item in history[-10:]:
        print(f"{item['date']}: {float(item['total_value']):.2f}")


if __name__ == "__main__":
    main()
