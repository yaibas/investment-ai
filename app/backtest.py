from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import yfinance as yf


def download_history(ticker: str, period: str = "5y"):
    history = yf.Ticker(ticker.strip().upper()).history(
        period=period,
        interval="1d",
        auto_adjust=False,
    )
    if history.empty:
        raise ValueError(f"履歴データを取得できませんでした: {ticker}")
    return history.dropna(subset=["Close"])


def sma_crossover_backtest(
    history,
    fast_window: int = 20,
    slow_window: int = 50,
) -> dict[str, Any]:
    """Long-only SMA crossover backtest.

    Position is 1 when SMA(fast) > SMA(slow), otherwise 0.
    Signals are shifted by one day to avoid look-ahead bias.
    No transaction costs or taxes are modeled yet.
    """
    close = history["Close"].astype(float)
    frame = history.copy()
    frame["sma_fast"] = close.rolling(fast_window).mean()
    frame["sma_slow"] = close.rolling(slow_window).mean()
    frame["position"] = (frame["sma_fast"] > frame["sma_slow"]).astype(int)

    daily_return = close.pct_change().fillna(0.0)
    strategy_return = daily_return * frame["position"].shift(1).fillna(0)
    equity = (1 + strategy_return).cumprod()
    benchmark = (1 + daily_return).cumprod()

    running_max = equity.cummax()
    drawdown = equity / running_max - 1

    total_return = float(equity.iloc[-1] - 1)
    benchmark_return = float(benchmark.iloc[-1] - 1)
    max_drawdown = float(drawdown.min())

    active = strategy_return[strategy_return != 0]
    win_rate = float((active > 0).mean()) if len(active) else 0.0

    years = (equity.index[-1] - equity.index[0]).days / 365.25
    annualized_return = (
        float(equity.iloc[-1] ** (1 / years) - 1) if years > 0 else 0.0
    )

    return {
        "start": equity.index[0].strftime("%Y-%m-%d"),
        "end": equity.index[-1].strftime("%Y-%m-%d"),
        "total_return_percent": round(total_return * 100, 2),
        "benchmark_buy_hold_return_percent": round(benchmark_return * 100, 2),
        "annualized_return_percent": round(annualized_return * 100, 2),
        "max_drawdown_percent": round(max_drawdown * 100, 2),
        "win_rate_percent": round(win_rate * 100, 2),
        "final_equity": round(float(equity.iloc[-1]), 4),
        "fast_window": fast_window,
        "slow_window": slow_window,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="SMAクロス戦略のバックテスト")
    parser.add_argument("ticker", help="ティッカー。例: 7203.T")
    parser.add_argument("--period", default="5y", help="期間。例: 2y, 5y, 10y")
    parser.add_argument("--fast", type=int, default=20)
    parser.add_argument("--slow", type=int, default=50)
    args = parser.parse_args()

    if args.fast >= args.slow:
        raise ValueError("fast は slow より小さくしてください")

    history = download_history(args.ticker, args.period)
    result = sma_crossover_backtest(history, args.fast, args.slow)

    print("===== バックテスト =====")
    print(f"銘柄: {args.ticker.strip().upper()}")
    print(f"期間: {result['start']} ～ {result['end']}")
    print(f"SMA: {result['fast_window']} / {result['slow_window']}")
    print(f"戦略リターン: {result['total_return_percent']}%")
    print(f"買い持ち: {result['benchmark_buy_hold_return_percent']}%")
    print(f"年率リターン: {result['annualized_return_percent']}%")
    print(f"最大ドローダウン: {result['max_drawdown_percent']}%")
    print(f"勝率: {result['win_rate_percent']}%")


if __name__ == "__main__":
    main()
