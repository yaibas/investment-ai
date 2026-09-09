from analysis.ai_analyzer import analyze_stock


def main() -> None:
    # Test data for the first version.
    stock = {
        "name": "Example Company",
        "ticker": "EXAMPLE",
        "price": 1500,
        "change_percent": 2.4,
        "volume": 1_200_000,
    }

    result = analyze_stock(stock)

    print("===== AI投資分析 =====")
    print(result)


if __name__ == "__main__":
    main()
