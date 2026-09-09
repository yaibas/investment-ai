from analysis.compare_analyzer import compare_stocks
from data.multi_market import get_multiple_market_data

TICKERS = ["7203.T", "6758.T", "9984.T", "8306.T"]


def main() -> None:
    data = get_multiple_market_data(TICKERS, period="1mo")
    print("===== 市場データ =====")
    for item in data:
        if "error" in item:
            print(f"{item['ticker']}: ERROR - {item['error']}")
        else:
            print(
                f"{item['ticker']} | {item['date']} | "
                f"価格: {item['price']} | 前日比: {item['change_percent']}% | "
                f"出来高: {item['volume']}"
            )
    print("\n===== AI比較分析 =====")
    print(compare_stocks(data))


if __name__ == "__main__":
    main()
