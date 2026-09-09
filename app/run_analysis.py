from __future__ import annotations

import argparse

from analysis.compare_analyzer import compare_stocks
from data.multi_market import get_multiple_market_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="複数銘柄の市場・テクニカル・企業情報・ニュースを取得してAI比較分析します。"
    )
    parser.add_argument(
        "tickers",
        nargs="+",
        help="分析するティッカー。例: 7203.T 6758.T 8306.T",
    )
    parser.add_argument(
        "--period",
        default="6mo",
        help="株価の取得期間。例: 1mo, 3mo, 6mo, 1y",
    )
    parser.add_argument(
        "--news-count",
        type=int,
        default=5,
        help="銘柄ごとに取得するニュース件数",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    market_data = get_multiple_market_data(
        args.tickers,
        period=args.period,
        news_count=args.news_count,
    )

    print("===== 市場データ・テクニカル・企業情報・ニュース =====")
    for item in market_data:
        ticker = item.get("ticker", "UNKNOWN")
        if "error" in item:
            print(f"{ticker}: ERROR - {item['error']}")
            continue

        technical = item.get("technical", {})
        fundamentals = item.get("fundamentals", {})
        news = item.get("news", [])

        print(
            f"\n{ticker} | {item['date']} | "
            f"価格: {item['price']} | 前日比: {item['change_percent']}% | "
            f"出来高: {item['volume']}"
        )
        print(
            f"  SMA20: {technical.get('sma_20')} | "
            f"SMA50: {technical.get('sma_50')} | "
            f"RSI14: {technical.get('rsi_14')} | "
            f"MACD: {technical.get('macd')}"
        )
        print(
            f"  PER: {fundamentals.get('trailing_pe')} | "
            f"PBR: {fundamentals.get('price_to_book')} | "
            f"営業利益率: {fundamentals.get('operating_margin_percent')}% | "
            f"純利益率: {fundamentals.get('net_margin_percent')}%"
        )
        print("  最近のニュース:")
        if isinstance(news, list) and news:
            for article in news:
                if "error" in article:
                    print(f"    ERROR - {article['error']}")
                    continue
                print(f"    - {article.get('title')} ({article.get('publisher')})")
        else:
            print("    ニュースなし")

    valid_data = [item for item in market_data if "error" not in item]
    if not valid_data:
        print("\n比較できる銘柄がありません。")
        return

    print("\n===== AI比較分析 =====")
    print(compare_stocks(valid_data))


if __name__ == "__main__":
    main()
