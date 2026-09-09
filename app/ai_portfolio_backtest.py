from __future__ import annotations

from typing import Any

from analysis.ai_allocator import suggest_allocation
from portfolio_backtest import download_prices, portfolio_backtest


def run_ai_allocation_historical_check(
    market_data: list[dict[str, Any]],
    period: str = "10y",
    cash_weight_percent: float = 10.0,
    max_single_weight_percent: float = 40.0,
    rebalance: str = "monthly",
    transaction_cost_bps: float = 10.0,
) -> dict[str, Any]:
    """Create an AI allocation from current candidate data and test that exact mix on past prices.

    This is a historical sensitivity check, not a point-in-time out-of-sample test, because
    today's AI allocation can use information that was not available during the historical period.
    """
    candidates = {
        str(item.get("ticker", "")).strip().upper()
        for item in market_data
        if "error" not in item and item.get("ticker")
    }
    if len(candidates) < 2:
        raise ValueError("AI配分を作るには、有効な候補銘柄が2つ以上必要です")

    allocation = suggest_allocation(
        market_data,
        cash_weight_percent=cash_weight_percent,
        max_single_weight_percent=max_single_weight_percent,
    )
    portfolio = allocation.get("portfolio") or []
    unknown = [
        str(item.get("ticker", "")).strip().upper()
        for item in portfolio
        if str(item.get("ticker", "")).strip().upper() not in candidates
    ]
    if unknown:
        raise ValueError(
            "AIが入力候補にない銘柄を返しました: " + ", ".join(unknown)
        )

    weights = {
        str(item["ticker"]).strip().upper(): float(item["weight_percent"])
        for item in portfolio
        if float(item.get("weight_percent", 0)) > 0
    }
    if len(weights) < 2:
        raise ValueError("AIが2銘柄以上の配分を作れませんでした")

    prices = download_prices(list(weights), period=period)
    missing = [ticker for ticker in weights if ticker not in prices.columns]
    if missing:
        raise ValueError("過去価格を取得できない銘柄があります: " + ", ".join(missing))

    test = portfolio_backtest(
        prices,
        weights,
        rebalance=rebalance,
        transaction_cost_bps=transaction_cost_bps,
        cash_weight_percent=float(allocation.get("cash_percent", cash_weight_percent)),
    )

    return {
        "allocation": allocation,
        "backtest": test,
        "candidate_tickers": sorted(candidates),
        "test_type": "current_ai_allocation_historical_sensitivity",
        "test_warning": (
            "現在のAI配分を過去価格に当てはめた検証です。過去時点で同じAI判断ができたことを示す" 
            "厳密なアウトオブサンプル・バックテストではありません。"
        ),
    }
