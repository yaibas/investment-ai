from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from backtest import download_history, sma_crossover_backtest


def parse_strategy(value: str) -> tuple[int, int]:
    parts = value.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"戦略は fast:slow 形式で指定してください: {value}")
    try:
        fast, slow = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError(f"戦略は整数の fast:slow 形式で指定してください: {value}") from exc
    if fast < 2 or fast >= slow:
        raise ValueError(f"不正なSMA設定です: {value}")
    return fast, slow


def batch_backtest(
    tickers: list[str],
    settings: list[tuple[int, int]],
    period: str = "5y",
    transaction_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        history = download_history(ticker, period)
        for fast, slow in settings:
            result = sma_crossover_backtest(
                history,
                fast_window=fast,
                slow_window=slow,
                transaction_cost_bps=transaction_cost_bps,
                slippage_bps=slippage_bps,
            )
            results.append({"ticker": ticker, "fast": fast, "slow": slow, **result})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="複数銘柄×複数SMA戦略を一括バックテストします")
    parser.add_argument("tickers", nargs="+", help="ティッカー。例: 7203.T 6758.T 8306.T")
    parser.add_argument("--period", default="5y")
    parser.add_argument(
        "--strategy",
        action="append",
        dest="strategies",
        help="比較するSMA。例: --strategy 10:30 --strategy 20:50",
    )
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--csv", help="結果CSVの保存先")
    args = parser.parse_args()

    settings = [
        parse_strategy(value)
        for value in (args.strategies or ["10:30", "20:50", "50:200"])
    ]
    results = batch_backtest(
        args.tickers,
        settings,
        period=args.period,
        transaction_cost_bps=args.cost_bps,
        slippage_bps=args.slippage_bps,
    )
    results.sort(key=lambda item: item["annualized_return_percent"], reverse=True)

    print("===== 複数銘柄×戦略 一括バックテスト =====")
    print("順位 | 銘柄 | SMA | 年率リターン | 累積リターン | 最大DD | 売買回数")
    for rank, result in enumerate(results, start=1):
        print(
            f"{rank:>2} | {result['ticker']:<8} | "
            f"{result['fast']:>3}/{result['slow']:<3} | "
            f"{result['annualized_return_percent']:>8.2f}% | "
            f"{result['total_return_percent']:>8.2f}% | "
            f"{result['max_drawdown_percent']:>7.2f}% | "
            f"{result['trade_events']:>5}"
        )

    if args.csv:
        path = Path(args.csv)
        fieldnames = [
            "ticker", "fast", "slow", "start", "end",
            "total_return_percent", "benchmark_buy_hold_return_percent",
            "annualized_return_percent", "max_drawdown_percent",
            "win_rate_percent", "trade_events", "transaction_cost_bps",
            "slippage_bps", "final_equity",
        ]
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows({key: row.get(key) for key in fieldnames} for row in results)
        print(f"\nCSV保存: {path}")


if __name__ == "__main__":
    main()
