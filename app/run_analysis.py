from __future__ import annotations

import argparse

from analysis.compare_analyzer import compare_stocks
from data.multi_market import get_multiple_market_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="複数銘柄の市場データとテクニカル指標を取得してAI比較分析します。"
    )
    parser.add_argument(
        "tickers",
        nargs="+",
        help="分析するティッカー。例: 7203.T 6758.T 8306.T",
    )
    parser.add_argument(
        "--period",
        default="6mo",
        help="取得期間。例: 1mo, 3mo, 6mo, 1y",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    market_data = get_multiple_market_data(args.tickers, period=args.period)

    print("===== 市場データ・テクニカル指標 =====")
    for item in market_data:
        ticker = item.get("ticker", "UNKNOWN")
        if "error" in item:
            print(f"{ticker}: ERROR - {item['error']}")
            continue

        technical = item.get("technical", {})
        print(
            f"{ticker} | {item['date']} | "
            f"価格: {item['price']} | 前日比: {item['change_percent']}% | "
            f"出来高: {item['volume']}"
        )
        print(
            f"  SMA20: {technical.get('sma_20')} | "
            f"SMA50: {technical.get('sma_50')} | "
            f"EMA20: {technical.get('ema_20')} | "
            f"RSI14: {technical.get('rsi_14')}"
        )
        print(
            f"  MACD: {technical.get('macd')} | "
            f"Signal: {technical.get('macd_signal')} | "
            f"年率換算ボラティリティ(20日): "
            f"{technical.get('annualized_volatility_20d_percent')}%"
        )

    valid_data = [item for item in market_data if "error" not in item]
    if not valid_data:
        print("\n比較できる銘柄がありません。")
        return

    print("\n===== AI比較分析 =====")
    print(compare_stocks(valid_data))


if __name__ == "__main__":
    main()
