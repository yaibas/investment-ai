from __future__ import annotations

import argparse
from typing import Any

import yfinance as yf

from risk_metrics import calculate_risk_metrics


def download_history(ticker: str, period: str = "5y"):
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker が空です")

    history = yf.Ticker(ticker).history(
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
    transaction_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    """Long-only SMA crossover backtest with trading friction.

    Position is 1 when SMA(fast) > SMA(slow), otherwise 0.
    Signals are shifted by one day to avoid look-ahead bias.
    Trading friction is charged whenever the position changes.
    """
    if fast_window < 2:
        raise ValueError("fast_window は2以上にしてください")
    if fast_window >= slow_window:
        raise ValueError("fast_window は slow_window より小さくしてください")
    if transaction_cost_bps < 0 or slippage_bps < 0:
        raise ValueError("transaction_cost_bps と slippage_bps は0以上にしてください")

    close = history["Close"].astype(float)
    frame = history.copy()
    frame["sma_fast"] = close.rolling(fast_window).mean()
    frame["sma_slow"] = close.rolling(slow_window).mean()
    frame["target_position"] = (frame["sma_fast"] > frame["sma_slow"]).astype(float)

    position = frame["target_position"].shift(1).fillna(0.0)
    turnover = position.diff().abs().fillna(position.abs())
    friction_rate = (transaction_cost_bps + slippage_bps) / 10_000

    daily_return = close.pct_change().fillna(0.0)
    gross_strategy_return = daily_return * position
    trading_cost = turnover * friction_rate
    net_strategy_return = gross_strategy_return - trading_cost

    equity = (1 + net_strategy_return).cumprod()
    benchmark = (1 + daily_return).cumprod()

    running_max = equity.cummax()
    drawdown = equity / running_max - 1

    total_return = float(equity.iloc[-1] - 1)
    benchmark_return = float(benchmark.iloc[-1] - 1)
    max_drawdown = float(drawdown.min())

    active = net_strategy_return[position > 0]
    win_rate = float((active > 0).mean()) if len(active) else 0.0
    trade_events = int((turnover > 0).sum())

    years = (equity.index[-1] - equity.index[0]).days / 365.25
    annualized_return = (
        float(equity.iloc[-1] ** (1 / years) - 1) if years > 0 else 0.0
    )
    risk = calculate_risk_metrics(net_strategy_return)

    return {
        "start": equity.index[0].strftime("%Y-%m-%d"),
        "end": equity.index[-1].strftime("%Y-%m-%d"),
        "total_return_percent": round(total_return * 100, 2),
        "benchmark_buy_hold_return_percent": round(benchmark_return * 100, 2),
        "annualized_return_percent": round(annualized_return * 100, 2),
        "max_drawdown_percent": round(max_drawdown * 100, 2),
        "annualized_volatility_percent": risk["annualized_volatility_percent"],
        "sharpe_ratio": risk["sharpe_ratio"],
        "sortino_ratio": risk["sortino_ratio"],
        "positive_day_rate_percent": risk["positive_day_rate_percent"],
        "win_rate_percent": round(win_rate * 100, 2),
        "trade_events": trade_events,
        "transaction_cost_bps": transaction_cost_bps,
        "slippage_bps": slippage_bps,
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
    parser.add_argument(
        "--cost-bps",
        type=float,
        default=10.0,
        help="売買コスト。1bps=0.01%%。デフォルト10bps",
    )
    parser.add_argument(
        "--slippage-bps",
        type=float,
        default=5.0,
        help="想定スリッページ。1bps=0.01%%。デフォルト5bps",
    )
    args = parser.parse_args()

    history = download_history(args.ticker, args.period)
    result = sma_crossover_backtest(
        history,
        args.fast,
        args.slow,
        transaction_cost_bps=args.cost_bps,
        slippage_bps=args.slippage_bps,
    )

    print("===== バックテスト =====")
    print(f"銘柄: {args.ticker.strip().upper()}")
    print(f"期間: {result['start']} ～ {result['end']}")
    print(f"SMA: {result['fast_window']} / {result['slow_window']}")
    print(f"戦略リターン: {result['total_return_percent']}%")
    print(f"買い持ち: {result['benchmark_buy_hold_return_percent']}%")
    print(f"年率リターン: {result['annualized_return_percent']}%")
    print(f"最大ドローダウン: {result['max_drawdown_percent']}%")
    print(f"年率ボラティリティ: {result['annualized_volatility_percent']}%")
    print(f"シャープレシオ: {result['sharpe_ratio']}")
    print(f"ソルティノレシオ: {result['sortino_ratio']}")
    print(f"勝率: {result['win_rate_percent']}%")
    print(f"売買イベント数: {result['trade_events']}")
    print(
        f"売買コスト: {result['transaction_cost_bps']}bps / "
        f"スリッページ: {result['slippage_bps']}bps"
    )


if __name__ == "__main__":
    main()
