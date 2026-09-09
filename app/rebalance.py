from __future__ import annotations

import argparse
from pathlib import Path

from analysis.ai_allocator import suggest_allocation
from data.multi_market import get_multiple_market_data
from paper_portfolio import PaperPortfolio, fetch_latest_prices, load_portfolio, save_portfolio


def rebalance_portfolio(
    portfolio: PaperPortfolio,
    target_weights: dict[str, float],
    prices: dict[str, float],
    cash_target_percent: float,
    min_trade_shares: float = 0.000001,
) -> list[dict[str, float | str]]:
    """Rebalance a virtual portfolio toward target weights using latest prices."""
    if not 0 <= cash_target_percent <= 100:
        raise ValueError("cash_target_percent は0〜100で指定してください")

    current = portfolio.valuation(prices)
    total_value = float(current["total_value"])
    target_cash = total_value * cash_target_percent / 100.0
    trades: list[dict[str, float | str]] = []

    all_tickers = sorted(set(portfolio.positions) | set(target_weights))
    missing_prices = [ticker for ticker in all_tickers if ticker not in prices]
    if missing_prices:
        raise ValueError(f"価格が取得できない銘柄があります: {', '.join(missing_prices)}")

    # First sell positions that are above target. This creates cash for purchases.
    for ticker in all_tickers:
        position = portfolio.positions.get(ticker)
        price = prices[ticker]
        target_value = total_value * target_weights.get(ticker, 0.0) / 100.0
        current_value = position.shares * price if position else 0.0
        excess_value = current_value - target_value
        if excess_value <= 0:
            continue
        shares = min(position.shares, excess_value / price)
        if shares < min_trade_shares:
            continue
        portfolio.sell(ticker, shares, price)
        trades.append({"side": "SELL", "ticker": ticker, "shares": shares, "price": price})

    # Then buy underweight positions, while preserving the target cash reserve.
    refreshed = portfolio.valuation(prices)
    available_cash = float(refreshed["cash"]) - target_cash
    if available_cash > 0:
        for ticker in all_tickers:
            price = prices[ticker]
            target_value = total_value * target_weights.get(ticker, 0.0) / 100.0
            position = portfolio.positions.get(ticker)
            current_value = position.shares * price if position else 0.0
            needed_value = target_value - current_value
            if needed_value <= 0 or available_cash <= 0:
                continue
            spend = min(needed_value, available_cash)
            shares = spend / price
            if shares < min_trade_shares:
                continue
            portfolio.buy(ticker, shares, price)
            available_cash -= spend
            trades.append({"side": "BUY", "ticker": ticker, "shares": shares, "price": price})

    return trades


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI配分案を仮想ポートフォリオへ反映します（実注文なし）"
    )
    parser.add_argument("tickers", nargs="+", help="分析するティッカー")
    parser.add_argument("--file", default="paper_portfolio.json", help="ポートフォリオ保存先")
    parser.add_argument("--cash", type=float, default=10.0, help="AI配分で保持する現金比率(%)")
    parser.add_argument("--max-weight", type=float, default=40.0, help="1銘柄の最大比率(%)")
    parser.add_argument("--period", default="6mo", help="AI分析用の株価取得期間")
    parser.add_argument("--news-count", type=int, default=5, help="銘柄ごとのニュース件数")
    args = parser.parse_args()

    if not 0 <= args.cash <= 100:
        raise ValueError("--cash は0〜100で指定してください")

    path = Path(args.file)
    portfolio = load_portfolio(str(path)) if path.exists() else PaperPortfolio(cash=1_000_000)

    data = get_multiple_market_data(
        args.tickers,
        period=args.period,
        news_count=args.news_count,
    )
    valid = [item for item in data if "error" not in item]
    if not valid:
        raise ValueError("有効な銘柄データがありません")

    allocation = suggest_allocation(
        valid,
        cash_weight_percent=args.cash,
        max_single_weight_percent=args.max_weight,
    )
    target_weights = {
        item["ticker"]: float(item["weight_percent"])
        for item in allocation["portfolio"]
    }
    prices = fetch_latest_prices(sorted(set(target_weights) | set(portfolio.positions)))
    trades = rebalance_portfolio(
        portfolio,
        target_weights=target_weights,
        prices=prices,
        cash_target_percent=args.cash,
    )
    save_portfolio(portfolio, str(path))

    result = portfolio.valuation(prices)
    print("===== AI仮想リバランス =====")
    for item in allocation["portfolio"]:
        print(f"目標 {item['ticker']}: {item['weight_percent']:.2f}% | {item['reason']}")
    print(f"現金目標: {allocation['cash_percent']:.2f}%")
    print(f"AI概要: {allocation['summary']}")
    print("\n===== 仮想取引 =====")
    if trades:
        for trade in trades:
            print(
                f"{trade['side']} {trade['ticker']} "
                f"{float(trade['shares']):.6f}株 @ {float(trade['price']):.4f}"
            )
    else:
        print("変更なし")

    print("\n===== 現在の評価 =====")
    print(f"総評価額: {result['total_value']:.2f}")
    print(f"現金: {result['cash']:.2f}")
    print(f"保有評価額: {result['positions_value']:.2f}")
    for holding in result["holdings"]:
        weight = holding["market_value"] / result["total_value"] * 100 if result["total_value"] else 0.0
        print(
            f"{holding['ticker']}: {holding['shares']:.6f}株 | "
            f"評価額 {holding['market_value']:.2f} | "
            f"比率 {weight:.2f}% | "
            f"含み損益 {holding['unrealized_pnl']:.2f}"
        )


if __name__ == "__main__":
    main()
