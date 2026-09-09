from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yfinance as yf

from data.ticker_master import display_name, resolve_ticker

DEFAULT_DIAMONDS = 100_000.0


@dataclass
class DiamondPosition:
    ticker: str
    shares: float = 0.0
    avg_price: float = 0.0


@dataclass
class DiamondPortfolio:
    diamonds: float = DEFAULT_DIAMONDS
    positions: dict[str, DiamondPosition] = field(default_factory=dict)
    transactions: list[dict[str, Any]] = field(default_factory=list)

    def buy_with_diamonds(self, name_or_ticker: str, diamonds: float, price: float) -> None:
        ticker = resolve_ticker(name_or_ticker)
        diamonds = float(diamonds)
        if diamonds <= 0 or price <= 0:
            raise ValueError("ダイヤと価格は0より大きくしてください")
        if diamonds > self.diamonds:
            raise ValueError(f"ダイヤが不足しています: 必要 {diamonds:.0f} / 保有 {self.diamonds:.0f}")

        shares = diamonds / price
        position = self.positions.get(ticker)
        if position is None:
            self.positions[ticker] = DiamondPosition(ticker, shares, price)
        else:
            total_cost = position.shares * position.avg_price + diamonds
            total_shares = position.shares + shares
            position.shares = total_shares
            position.avg_price = total_cost / total_shares

        self.diamonds -= diamonds
        self.transactions.append(
            {
                "date": date.today().isoformat(),
                "side": "BUY",
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "diamonds": diamonds,
            }
        )

    def sell_shares(self, name_or_ticker: str, shares: float, price: float) -> None:
        ticker = resolve_ticker(name_or_ticker)
        shares = float(shares)
        if shares <= 0 or price <= 0:
            raise ValueError("株数と価格は0より大きくしてください")
        position = self.positions.get(ticker)
        if position is None or shares > position.shares + 1e-12:
            raise ValueError("保有株数が不足しています")

        proceeds = shares * price
        position.shares -= shares
        self.diamonds += proceeds
        self.transactions.append(
            {
                "date": date.today().isoformat(),
                "side": "SELL",
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "diamonds": proceeds,
            }
        )
        if position.shares <= 1e-10:
            del self.positions[ticker]

    def valuation(self, prices: dict[str, float]) -> dict[str, Any]:
        holdings = []
        invested = 0.0
        unrealized = 0.0
        for ticker, position in sorted(self.positions.items()):
            price = prices.get(ticker)
            if price is None:
                continue
            value = position.shares * price
            pnl = (price - position.avg_price) * position.shares
            invested += value
            unrealized += pnl
            holdings.append(
                {
                    "ticker": ticker,
                    "name": display_name(ticker),
                    "shares": round(position.shares, 6),
                    "avg_price": round(position.avg_price, 2),
                    "price": round(price, 2),
                    "market_value": round(value, 2),
                    "unrealized_pnl": round(pnl, 2),
                }
            )
        total = self.diamonds + invested
        return {
            "diamonds": round(self.diamonds, 2),
            "positions_value": round(invested, 2),
            "total_value": round(total, 2),
            "unrealized_pnl": round(unrealized, 2),
            "holdings": holdings,
            "transactions": self.transactions,
        }


def fetch_latest_prices(tickers: list[str]) -> dict[str, float]:
    prices: dict[str, float] = {}
    for ticker in tickers:
        normalized = resolve_ticker(ticker)
        history = yf.Ticker(normalized).history(period="5d", interval="1d", auto_adjust=False)
        if history.empty or history["Close"].dropna().empty:
            raise ValueError(f"価格を取得できませんでした: {normalized}")
        prices[normalized] = float(history["Close"].dropna().iloc[-1])
    return prices


def save_diamond_portfolio(portfolio: DiamondPortfolio, path: str) -> None:
    payload = {
        "diamonds": portfolio.diamonds,
        "positions": {
            ticker: {
                "ticker": position.ticker,
                "shares": position.shares,
                "avg_price": position.avg_price,
            }
            for ticker, position in portfolio.positions.items()
        },
        "transactions": portfolio.transactions,
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_diamond_portfolio(path: str) -> DiamondPortfolio:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    positions = {
        ticker: DiamondPosition(
            ticker=item["ticker"],
            shares=float(item["shares"]),
            avg_price=float(item["avg_price"]),
        )
        for ticker, item in payload.get("positions", {}).items()
    }
    return DiamondPortfolio(
        diamonds=float(payload.get("diamonds", DEFAULT_DIAMONDS)),
        positions=positions,
        transactions=payload.get("transactions", []),
    )
