from __future__ import annotations

from typing import Any

import yfinance as yf


def _latest_value(statement: Any, row_name: str) -> float | None:
    """Return the latest non-null numeric value for a financial-statement row."""
    if statement is None or row_name not in statement.index:
        return None

    row = statement.loc[row_name]
    for raw in row.tolist():
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value == value:  # NaN check without importing math.
            return value
    return None


def get_fundamental_data(ticker: str) -> dict[str, Any]:
    """Fetch a compact set of recent fundamental data from Yahoo Finance."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker が空です")

    yf_ticker = yf.Ticker(ticker)
    income_stmt = yf_ticker.get_income_stmt(freq="yearly")
    info = yf_ticker.get_info()

    revenue = _latest_value(income_stmt, "TotalRevenue")
    net_income = _latest_value(income_stmt, "NetIncome")
    operating_income = _latest_value(income_stmt, "OperatingIncome")

    net_margin = None
    if revenue and net_income is not None:
        net_margin = net_income / revenue * 100

    operating_margin = None
    if revenue and operating_income is not None:
        operating_margin = operating_income / revenue * 100

    def safe_float(value: Any) -> float | None:
        try:
            numeric = float(value)
            return numeric if numeric == numeric else None
        except (TypeError, ValueError):
            return None

    return {
        "ticker": ticker,
        "company_name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": safe_float(info.get("marketCap")),
        "trailing_pe": safe_float(info.get("trailingPE")),
        "forward_pe": safe_float(info.get("forwardPE")),
        "price_to_book": safe_float(info.get("priceToBook")),
        "dividend_yield_percent": (
            safe_float(info.get("dividendYield")) * 100
            if safe_float(info.get("dividendYield")) is not None
            else None
        ),
        "revenue": revenue,
        "operating_income": operating_income,
        "net_income": net_income,
        "operating_margin_percent": (
            round(operating_margin, 4) if operating_margin is not None else None
        ),
        "net_margin_percent": round(net_margin, 4) if net_margin is not None else None,
    }
