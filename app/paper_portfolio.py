from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yfinance as yf


@dataclass
class Position:
    ticker: str
    shares: float
    avg_price: float


@dataclass
class PaperPortfolio:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    transactions: list[dict[str, Any]] = field(default_factory=list)

    def buy(self, ticker: str, shares: float, price: float) -> None:
        ticker = ticker.strip().upper()
        if shares <= 0 or price <= 0:
            raise ValueError("shares と price は0より大きくしてください")
        cost = shares * price
        if cost > self.cash:
            raise ValueError(f"現金が不足しています: 必要額={cost:.2f}, 現金={self.cash:.2f}")

        position = self.positions.get(ticker)
        if position is None:
            self.positions[ticker] = Position(ticker, shares, price)
        else:
            total_cost = position.shares * position.avg_price + cost
            total_shares = position.shares + shares
            position.shares = total_shares
            position.avg_price = total_cost / total_shares

        self.cash -= cost
        self.transactions.append(
            {
                "date": date.today().isoformat(),
                "side": "BUY",
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "value": cost,
            }
        )

    def sell(self, ticker: str, shares: float, price: float) -> None:
        ticker = ticker.strip().upper()
        if shares <= 0 or price <= 0:
            raise ValueError("shares と price は0より大きくしてください")
        position = self.positions.get(ticker)
        if position is None or shares > position.shares:
            raise ValueError(f"保有数量が不足しています: {ticker}")

        proceeds = shares * price
        position.shares -= shares
        self.cash += proceeds
        if position.shares == 0:
            del self.positions[ticker]

        self.transactions.append(
            {
                "date": date.today().isoformat(),
                "side": "SELL",
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "value": proceeds,
            }
        )

    def valuation(self, prices: dict[str, float]) -> dict[str, Any]:
        holdings = []
        total_positions = 0.0
        for ticker, position in sorted(self.positions.items()):
            price = prices.get(ticker)
            if price is None:
                continue
            value = position.shares * price
            unrealized = (price - position.avg_price) * position.shares
            total_positions += value
            holdings.append(
                {
                    "ticker": ticker,
                    "shares": round(position.shares, 6),
                    "avg_price": round(position.avg_price, 4),
                    "price": round(price, 4),
                    "market_value": round(value, 2),
                    "unrealized_pnl": round(unrealized, 2),
                }
            )

        total_value = self.cash + total_positions
        return {
            "cash": round(self.cash, 2),
            "positions_value": round(total_positions, 2),
            "total_value": round(total_value, 2),
            "holdings": holdings,
            "transactions": self.transactions,
        }


def fetch_latest_prices(tickers: list[str]) -> dict[str, float]:
    prices: dict[str, float] = {}
    for ticker in tickers:
        normalized = ticker.strip().upper()
        history = yf.Ticker(normalized).history(period="5d", interval="1d", auto_adjust=False)
        if history.empty:
            raise ValueError(f"価格を取得できませんでした: {normalized}")
        prices[normalized] = float(history["Close"].dropna().iloc[-1])
    return prices


def save_portfolio(portfolio: PaperPortfolio, path: str) -> None:
    payload = {
        "cash": portfolio.cash,
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


def load_portfolio(path: str) -> PaperPortfolio:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    positions = {
        ticker: Position(
            ticker=item["ticker"],
            shares=float(item["shares"]),
            avg_price=float(item["avg_price"]),
        )
        for ticker, item in payload.get("positions", {}).items()
    }
    return PaperPortfolio(
        cash=float(payload["cash"]),
        positions=positions,
        transactions=payload.get("transactions", []),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="仮想ポートフォリオを管理します（実注文なし）")
    parser.add_argument("--file", default="paper_portfolio.json", help="ポートフォリオ保存先")
    parser.add_argument("--cash", type=float, default=1_000_000, help="新規作成時の初期現金")
    parser.add_argument("--buy", nargs=3, metavar=("TICKER", "SHARES", "PRICE"), help="仮想買い注文")
    parser.add_argument("--sell", nargs=3, metavar=("TICKER", "SHARES", "PRICE"), help="仮想売り注文")
    parser.add_argument("--quote", nargs="+", metavar="TICKER", help="現在価格を取得して評価")
    args = parser.parse_args()

    path = Path(args.file)
    portfolio = load_portfolio(str(path)) if path.exists() else PaperPortfolio(cash=args.cash)

    if args.buy:
        ticker, shares, price = args.buy
        portfolio.buy(ticker, float(shares), float(price))
        save_portfolio(portfolio, str(path))

    if args.sell:
        ticker, shares, price = args.sell
        portfolio.sell(ticker, float(shares), float(price))
        save_portfolio(portfolio, str(path))

    tickers = args.quote or list(portfolio.positions)
    prices = fetch_latest_prices(tickers) if tickers else {}
    result = portfolio.valuation(prices)

    print("===== 仮想ポートフォリオ =====")
    print(f"総評価額: {result['total_value']:.2f}")
    print(f"現金: {result['cash']:.2f}")
    print(f"保有評価額: {result['positions_value']:.2f}")
    for holding in result["holdings"]:
        print(
            f"{holding['ticker']}: {holding['shares']}株 | "
            f"評価額 {holding['market_value']:.2f} | "
            f"含み損益 {holding['unrealized_pnl']:.2f}"
        )
    print(f"取引回数: {len(result['transactions'])}")


if __name__ == "__main__":
    main()
