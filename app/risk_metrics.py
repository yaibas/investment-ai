from __future__ import annotations

from typing import Any

import pandas as pd


def calculate_risk_metrics(daily_returns: pd.Series) -> dict[str, Any]:
    """Calculate simple annualized return/risk metrics from daily returns."""
    returns = pd.Series(daily_returns, dtype="float64").dropna()
    if returns.empty:
        return {
            "annualized_return_percent": 0.0,
            "annualized_volatility_percent": 0.0,
            "sharpe_ratio": None,
            "sortino_ratio": None,
            "max_drawdown_percent": 0.0,
            "positive_day_rate_percent": 0.0,
        }

    equity = (1.0 + returns).cumprod()
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0

    annualized_return = equity.iloc[-1] ** (252 / len(returns)) - 1.0
    volatility = returns.std(ddof=1) * (252**0.5) if len(returns) > 1 else 0.0
    daily_mean = returns.mean()
    daily_std = returns.std(ddof=1)
    downside = returns[returns < 0]
    downside_std = downside.std(ddof=1) if len(downside) > 1 else 0.0

    sharpe = daily_mean / daily_std * (252**0.5) if daily_std > 0 else None
    sortino = daily_mean / downside_std * (252**0.5) if downside_std > 0 else None

    return {
        "annualized_return_percent": round(float(annualized_return * 100), 2),
        "annualized_volatility_percent": round(float(volatility * 100), 2),
        "sharpe_ratio": round(float(sharpe), 2) if sharpe is not None else None,
        "sortino_ratio": round(float(sortino), 2) if sortino is not None else None,
        "max_drawdown_percent": round(float(drawdown.min() * 100), 2),
        "positive_day_rate_percent": round(float((returns > 0).mean() * 100), 2),
    }
