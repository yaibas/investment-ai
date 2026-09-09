from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_history(path: str) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("履歴ファイルの形式が不正です")
    return payload


def export_csv(history: list[dict[str, Any]], path: str) -> None:
    with Path(path).open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["date", "total_value", "cash", "positions_value"],
        )
        writer.writeheader()
        for item in history:
            writer.writerow({key: item.get(key) for key in writer.fieldnames})


def chart(history: list[dict[str, Any]], output: str) -> None:
    import matplotlib.pyplot as plt

    dates = [item["date"] for item in history]
    values = [float(item["total_value"]) for item in history]
    if not values:
        raise ValueError("グラフ化できる履歴がありません")

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(dates, values, marker="o", linewidth=1.5)
    axis.set_title("Paper Portfolio Value")
    axis.set_xlabel("Date")
    axis.set_ylabel("Portfolio Value")
    axis.grid(True, alpha=0.25)
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description="仮想ポートフォリオの履歴をCSV・グラフに出力します")
    parser.add_argument("--history-file", default="portfolio_history.json")
    parser.add_argument("--csv", default="portfolio_history.csv")
    parser.add_argument("--chart", default="portfolio_history.png")
    args = parser.parse_args()

    history = load_history(args.history_file)
    export_csv(history, args.csv)
    chart(history, args.chart)
    print(f"CSV: {args.csv}")
    print(f"グラフ: {args.chart}")
    print(f"記録数: {len(history)}")


if __name__ == "__main__":
    main()
