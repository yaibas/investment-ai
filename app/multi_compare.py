"""Multi-ticker market-data and AI comparison entry point."""

from analysis.compare_analyzer import compare_stocks
from data.multi_market import get_multiple_market_data

TICKERS = ["7203.T", "6758.T", "9984.T", "8306.T"]


def main() -> None:
    data = get_multiple_market_data(TICKERS, period="1mo")
    for item in data:
        if "error" in item:
            print(f"{item['ticker']}: ERROR - {item['error']}")
        else:
            print(
                f"{item['ticker']} | {item['date']} | "
                f"price={item['price']} | change={item['change_percent']}% | "
                f"volume={item['volume']}"
            )
    print("\n===== AI comparison =====")
    print(compare_stocks(data))


if __name__ == "__main__":
    main()
