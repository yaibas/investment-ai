from __future__ import annotations

import argparse
from typing import Any

import pandas as pd

from backtest import download_history, sma_crossover_backtest
from risk_metrics import calculate_risk_metrics


def walk_forward_backtest(
    history: pd.DataFrame,
    settings: list[tuple[int, int]],
    train_days: int = 504,
    test_days: int = 126,
    transaction_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    """Optimize on past data, then test the selected strategy on the next unseen window."""
    if train_days < 60:
        raise ValueError("train_days は60以上にしてください")
    if test_days < 20:
        raise ValueError("test_days は20以上にしてください")
    if not settings:
        raise ValueError("戦略設定が空です")

    clean = history.dropna(subset=["Close"]).copy()
    periods: list[dict[str, Any]] = []
    oos_returns: list[pd.Series] = []

    start = 0
    while start + train_days + test_days <= len(clean):
        train = clean.iloc[start : start + train_days]
        test = clean.iloc[start + train_days : start + train_days + test_days]
        train_results = []

        for fast, slow in settings:
            try:
                result = sma_crossover_backtest(
                    train,
                    fast_window=fast,
                    slow_window=slow,
                    transaction_cost_bps=transaction_cost_bps,
                    slippage_bps=slippage_bps,
                )
                train_results.append((result["annualized_return_percent"], fast, slow, result))
            except ValueError:
                continue

        if not train_results:
            start += test_days
            continue

        _, fast, slow, train_result = max(train_results, key=lambda row: row[0])
        test_result = sma_crossover_backtest(
            test,
            fast_window=fast,
            slow_window=slow,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
        )

        periods.append(
            {
                "train_start": train.index[0].strftime("%Y-%m-%d"),
                "train_end": train.index[-1].strftime("%Y-%m-%d"),
                "test_start": test.index[0].strftime("%Y-%m-%d"),
                "test_end": test.index[-1].strftime("%Y-%m-%d"),
                "fast": fast,
                "slow": slow,
                "train_annualized_return_percent": train_result["annualized_return_percent"],
                "test_return_percent": test_result["total_return_percent"],
                "test_buy_hold_return_percent": test_result["benchmark_buy_hold_return_percent"],
                "test_max_drawdown_percent": test_result["max_drawdown_percent"],
            }
        )

        combined_window = clean.iloc[start : start + train_days + test_days]
        daily = combined_window["Close"].pct_change().fillna(0)
        fast_sma = combined_window["Close"].rolling(fast).mean()
        slow_sma = combined_window["Close"].rolling(slow).mean()
        position = (fast_sma > slow_sma).astype(float).shift(1).fillna(0)
        friction = (transaction_cost_bps + slippage_bps) / 10000
        turnover = position.diff().abs().fillna(position.abs())
        strategy_daily = daily * position - turnover * friction
        oos_returns.append(strategy_daily.loc[test.index])

        start += test_days

    if not periods:
        raise ValueError("十分な履歴がありません。期間を長くするか train/test を小さくしてください")

    combined = pd.concat(oos_returns).sort_index()
    equity = (1.0 + combined).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1.0
    days = max((equity.index[-1] - equity.index[0]).days, 1)
    annualized = equity.iloc[-1] ** (365 / days) - 1
    benchmark_daily = clean["Close"].pct_change().fillna(0).loc[combined.index]
    buy_hold = (1 + benchmark_daily).prod() - 1
    risk = calculate_risk_metrics(combined)

    return {
        "periods": periods,
        "out_of_sample_return_percent": round((equity.iloc[-1] - 1) * 100, 2),
        "out_of_sample_annualized_return_percent": round(annualized * 100, 2),
        "out_of_sample_max_drawdown_percent": round(drawdown.min() * 100, 2),
        "out_of_sample_annualized_volatility_percent": risk["annualized_volatility_percent"],
        "out_of_sample_sharpe_ratio": risk["sharpe_ratio"],
        "out_of_sample_sortino_ratio": risk["sortino_ratio"],
        "out_of_sample_buy_hold_return_percent": round(buy_hold * 100, 2),
        "period_count": len(periods),
    }


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


def main() -> None:
    parser = argparse.ArgumentParser(description="過去で戦略を選び、次の未使用期間で検証します")
    parser.add_argument("ticker")
    parser.add_argument("--period", default="10y")
    parser.add_argument("--train-days", type=int, default=504, help="戦略を選ぶ過去期間の日数")
    parser.add_argument("--test-days", type=int, default=126, help="選んだ戦略を試す未来期間の日数")
    parser.add_argument("--strategy", action="append", dest="strategies")
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    args = parser.parse_args()

    settings = [
        parse_strategy(value)
        for value in (args.strategies or ["10:30", "20:50", "50:200"])
    ]
    history = download_history(args.ticker, args.period)
    result = walk_forward_backtest(
        history,
        settings,
        train_days=args.train_days,
        test_days=args.test_days,
        transaction_cost_bps=args.cost_bps,
        slippage_bps=args.slippage_bps,
    )

    print("===== ウォークフォワード検証 =====")
    print(f"期間数: {result['period_count']}")
    print(f"未来期間の累積リターン: {result['out_of_sample_return_percent']:.2f}%")
    print(f"未来期間の年率リターン: {result['out_of_sample_annualized_return_percent']:.2f}%")
    print(f"未来期間の最大下落: {result['out_of_sample_max_drawdown_percent']:.2f}%")
    print(f"値動きの大きさ: {result['out_of_sample_annualized_volatility_percent']:.2f}%")
    print(f"シャープレシオ: {result['out_of_sample_sharpe_ratio']}")
    print(f"ソルティノレシオ: {result['out_of_sample_sortino_ratio']}")
    print(f"同期間の買って持つだけ: {result['out_of_sample_buy_hold_return_percent']:.2f}%")
    print("\n期間ごとの選択")
    for period in result["periods"]:
        print(
            f"{period['test_start']}〜{period['test_end']}: "
            f"SMA {period['fast']}/{period['slow']} → "
            f"{period['test_return_percent']:.2f}%"
        )


if __name__ == "__main__":
    main()
