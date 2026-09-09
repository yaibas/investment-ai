from __future__ import annotations

import argparse
from typing import Any

import pandas as pd
import yfinance as yf

TRADING_DAYS = 252


def download_prices(tickers: list[str], period: str = "10y") -> pd.DataFrame:
    cleaned = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    if len(cleaned) < 2:
        raise ValueError("2銘柄以上を指定してください")
    data = yf.download(cleaned, period=period, interval="1d", auto_adjust=False, progress=False, group_by="column")
    if data.empty:
        raise ValueError("価格データを取得できませんでした")
    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"].copy()
    else:
        close = data[["Close"]].copy()
        close.columns = cleaned[: len(close.columns)]
    missing = [ticker for ticker in cleaned if ticker not in close.columns]
    if missing:
        raise ValueError(f"取得できない銘柄があります: {', '.join(missing)}")
    return close[cleaned].ffill().dropna()


def portfolio_backtest(
    prices: pd.DataFrame,
    weights: dict[str, float],
    rebalance: str = "monthly",
    transaction_cost_bps: float = 10.0,
    cash_weight_percent: float = 0.0,
) -> dict[str, Any]:
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps は0以上にしてください")
    if not 0 <= cash_weight_percent < 100:
        raise ValueError("cash_weight_percent は0〜100未満で指定してください")
    if not weights or any(float(v) < 0 for v in weights.values()):
        raise ValueError("ウェイトは0以上で指定してください")
    available = [ticker for ticker in weights if ticker in prices.columns]
    if len(available) < 2:
        raise ValueError("価格データが揃っている銘柄が2つ以上必要です")
    raw = {ticker: float(weights[ticker]) for ticker in available}
    total = sum(raw.values())
    if total <= 0:
        raise ValueError("ウェイトの合計は0より大きくしてください")

    investable_fraction = 1.0 - cash_weight_percent / 100.0
    normalized = {ticker: value / total for ticker, value in raw.items()}
    target_weights = {ticker: value * investable_fraction for ticker, value in normalized.items()}

    returns = prices[list(target_weights)].pct_change().fillna(0.0)
    if rebalance == "daily":
        flags = pd.Series(True, index=returns.index)
    elif rebalance == "monthly":
        periods = returns.index.to_period("M")
        flags = pd.Series(periods != periods.shift(1), index=returns.index)
    else:
        raise ValueError("rebalance は daily または monthly にしてください")

    holdings = pd.Series(0.0, index=target_weights)
    strategy_returns: list[float] = []
    turnovers: list[float] = []
    for date in returns.index:
        if flags.loc[date] or holdings.sum() == 0:
            target = pd.Series(target_weights)
            turnover = float((target - holdings).abs().sum())
            holdings = target
        else:
            turnover = 0.0
        gross = float((returns.loc[date] * holdings).sum())
        cost = turnover * transaction_cost_bps / 10_000
        strategy_returns.append(gross - cost)
        turnovers.append(turnover)

    daily = pd.Series(strategy_returns, index=returns.index)
    equity = (1 + daily).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1
    annualized_return = equity.iloc[-1] ** (TRADING_DAYS / max(len(equity), 1)) - 1
    volatility = daily.std(ddof=1) * (TRADING_DAYS ** 0.5) if len(daily) > 1 else 0.0
    downside_values = daily[daily < 0]
    downside = downside_values.std(ddof=1) * (TRADING_DAYS ** 0.5) if len(downside_values) > 1 else 0.0
    return {
        "start": equity.index[0].strftime("%Y-%m-%d"),
        "end": equity.index[-1].strftime("%Y-%m-%d"),
        "weights": target_weights,
        "cash_weight_percent": round(cash_weight_percent, 2),
        "rebalance": rebalance,
        "total_return_percent": round(float(equity.iloc[-1] - 1) * 100, 2),
        "annualized_return_percent": round(float(annualized_return) * 100, 2),
        "annualized_volatility_percent": round(float(volatility) * 100, 2),
        "sharpe_ratio": round(float(annualized_return / volatility), 3) if volatility > 0 else 0.0,
        "sortino_ratio": round(float(annualized_return / downside), 3) if downside > 0 else 0.0,
        "max_drawdown_percent": round(float(drawdown.min()) * 100, 2),
        "average_turnover_percent": round(float(sum(turnovers) / len(turnovers)) * 100, 2),
    }


def parse_weights(values: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for value in values:
        ticker, separator, weight = value.partition("=")
        if not separator:
            raise ValueError("ウェイトは TICKER=割合 の形式で指定してください")
        result[ticker.strip().upper()] = float(weight)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="複数銘柄を組み合わせたポートフォリオを過去データで検証します")
    parser.add_argument("tickers", nargs="+", help="例: 7203.T 6758.T 8306.T")
    parser.add_argument("--period", default="10y")
    parser.add_argument("--weight", action="append", help="例: --weight 7203.T=40 --weight 6758.T=30")
    parser.add_argument("--cash", type=float, default=0.0, help="現金比率（%）")
    parser.add_argument("--rebalance", choices=["daily", "monthly"], default="monthly")
    parser.add_argument("--cost-bps", type=float, default=10.0)
    args = parser.parse_args()
    prices = download_prices(args.tickers, args.period)
    weights = parse_weights(args.weight) if args.weight else {ticker: 1.0 for ticker in args.tickers}
    result = portfolio_backtest(prices, weights, args.rebalance, args.cost_bps, args.cash)
    print("===== ポートフォリオ・バックテスト =====")
    print(f"期間: {result['start']} ～ {result['end']}")
    print(f"配分: {result['weights']}")
    print(f"現金: {result['cash_weight_percent']}%")
    print(f"累積リターン: {result['total_return_percent']}%")
    print(f"年率リターン: {result['annualized_return_percent']}%")
    print(f"値動きの大きさ: {result['annualized_volatility_percent']}%")
    print(f"シャープレシオ: {result['sharpe_ratio']}")
    print(f"ソルティノレシオ: {result['sortino_ratio']}")
    print(f"最大下落: {result['max_drawdown_percent']}%")
    print(f"平均売買比率: {result['average_turnover_percent']}%")


if __name__ == "__main__":
    main()
