from __future__ import annotations

import argparse
from typing import Any

from backtest import download_history, sma_crossover_backtest


def compare_strategies(
    history,
    settings: list[tuple[int, int]],
    transaction_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> list[dict[str, Any]]:
    results = []
    for fast, slow in settings:
        result = sma_crossover_backtest(
            history,
            fast_window=fast,
            slow_window=slow,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
        )
        results.append(result)
    return sorted(results, key=lambda item: item["annualized_return_percent"], reverse=True)


def parse_strategy(value: str) -> tuple[int, int]:
    parts = value.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"戦略は fast:slow 形式で指定してください: {value}")
    try:
        fast, slow = (int(part) for part in parts)
    except ValueError as exc:
        raise ValueError(f"戦略は整数の fast:slow 形式で指定してください: {value}") from exc
    if fast < 2 or fast >= slow:
        raise ValueError(f"不正なSMA設定です: {value}")
    return fast, slow


def main() -> None:
    parser = argparse.ArgumentParser(description="複数SMA戦略を同じ履歴で比較します")
    parser.add_argument("ticker", help="ティッカー。例: 7203.T")
    parser.add_argument("--period", default="5y")
    parser.add_argument(
        "--strategy",
        action="append",
        dest="strategies",
        help="比較するSMA。例: --strategy 10:30 --strategy 20:50",
    )
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    args = parser.parse_args()

    settings = [
        parse_strategy(value)
        for value in (args.strategies or ["10:30", "20:50", "50:200"])
    ]
    history = download_history(args.ticker, args.period)
    results = compare_strategies(
        history,
        settings,
        transaction_cost_bps=args.cost_bps,
        slippage_bps=args.slippage_bps,
    )

    print("===== SMA戦略比較 =====")
    print(f"銘柄: {args.ticker.strip().upper()}")
    print(f"期間: {results[0]['start']} ～ {results[0]['end']}")
    print("順位 | SMA | 年率リターン | 累積リターン | 最大DD | 売買回数")
    for rank, result in enumerate(results, start=1):
        print(
            f"{rank:>2} | {result['fast_window']:>3}/{result['slow_window']:<3} | "
            f"{result['annualized_return_percent']:>8.2f}% | "
            f"{result['total_return_percent']:>8.2f}% | "
            f"{result['max_drawdown_percent']:>7.2f}% | "
            f"{result['trade_events']:>5}"
        )


if __name__ == "__main__":
    main()
