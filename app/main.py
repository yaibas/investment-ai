from analysis.ai_analyzer import analyze_stock
from data.market_data import get_market_data


def main() -> None:
    # 日本株の例: トヨタ自動車
    ticker = "7203.T"

    stock = get_market_data(ticker, period="1mo")

    result = analyze_stock(stock)

    print("===== AI投資分析 =====")
    print(f"銘柄: {stock['ticker']}")
    print(f"データ日付: {stock['date']}")
    print(f"現在価格: {stock['price']}")
    print(f"前日比: {stock['change_percent']}%")
    print(f"出来高: {stock['volume']}")
    print()
    print(result)


if __name__ == "__main__":
    main()
