from __future__ import annotations

import argparse
import json

from analysis.ai_allocator import suggest_allocation
from data.multi_market import get_multiple_market_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="複数銘柄を分析し、研究用の仮想ポートフォリオ配分案を作成します。"
    )
    parser.add_argument("tickers", nargs="+", help="ティッカー。例: 7203.T 6758.T 8306.T")
    parser.add_argument("--period", default="6mo", help="株価取得期間。例: 3mo, 6mo, 1y")
    parser.add_argument("--news-count", type=int, default=5, help="銘柄ごとのニュース件数")
    parser.add_argument("--cash", type=float, default=10.0, help="現金比率(%)")
    parser.add_argument("--max-weight", type=float, default=40.0, help="1銘柄の最大比率(%)")
    args = parser.parse_args()

    data = get_multiple_market_data(args.tickers, period=args.period, news_count=args.news_count)
    valid = [item for item in data if "error" not in item]
    if not valid:
        raise ValueError("有効な銘柄データがありません")

    allocation = suggest_allocation(
        valid,
        cash_weight_percent=args.cash,
        max_single_weight_percent=args.max_weight,
    )

    print("===== 自動仮想ポートフォリオ配分案 =====")
    for item in allocation["portfolio"]:
        print(f"{item['ticker']}: {item['weight_percent']:.2f}% | {item['reason']}")
    print(f"現金: {allocation['cash_percent']:.2f}%")
    print(f"合計: {allocation['total_percent']:.2f}%")
    print(f"\n概要: {allocation['summary']}")
    print("主なリスク:")
    for risk in allocation["key_risks"]:
        print(f"- {risk}")

    print("\n===== JSON =====")
    print(json.dumps(allocation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
