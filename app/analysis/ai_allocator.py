from __future__ import annotations

from typing import Any

from analysis.explain_score import explain_score
from data.ticker_master import display_name


def suggest_allocation(
    market_data: list[dict[str, Any]],
    cash_weight_percent: float = 10.0,
    max_single_weight_percent: float = 40.0,
) -> dict[str, Any]:
    """Create a deterministic, explainable paper allocation without an API key.

    The allocation is based on the existing educational score. It is not a predictive model.
    """
    if not market_data:
        raise ValueError("分析対象データがありません")
    if not 0 <= cash_weight_percent <= 100:
        raise ValueError("cash_weight_percent は0〜100で指定してください")
    if not 1 <= max_single_weight_percent <= 100:
        raise ValueError("max_single_weight_percent は1〜100で指定してください")

    valid = [item for item in market_data if "error" not in item and item.get("ticker")]
    if len(valid) < 2:
        raise ValueError("有効な銘柄データが2つ以上必要です")

    target_total = 100.0 - cash_weight_percent
    ranked: list[dict[str, Any]] = []
    for item in valid:
        score = explain_score(item)
        ranked.append(
            {
                "ticker": str(item["ticker"]).strip().upper(),
                "score": float(score["overall_score"]),
                "label": score["label"],
            }
        )
    ranked.sort(key=lambda x: (-x["score"], x["ticker"]))

    # Shift scores to positive weights so a below-average score still receives some weight,
    # then cap and redistribute until the requested invested total is satisfied.
    floor = 5.0
    raw = {item["ticker"]: max(item["score"] - 35.0, floor) for item in ranked}
    active = set(raw)
    weights = {ticker: 0.0 for ticker in raw}

    remaining = target_total
    while active and remaining > 1e-9:
        subtotal = sum(raw[ticker] for ticker in active)
        if subtotal <= 0:
            break
        capped_any = False
        for ticker in list(active):
            proposed = remaining * raw[ticker] / subtotal
            if proposed >= max_single_weight_percent:
                weights[ticker] = max_single_weight_percent
                remaining -= max_single_weight_percent
                active.remove(ticker)
                capped_any = True
        if not capped_any:
            for ticker in active:
                weights[ticker] = remaining * raw[ticker] / subtotal
            remaining = 0.0

    # Round while preserving the requested total as closely as possible.
    rounded = {ticker: round(value, 2) for ticker, value in weights.items() if value > 0.005}
    rounding_gap = round(target_total - sum(rounded.values()), 2)
    if rounding_gap and rounded:
        top_ticker = max(rounded, key=rounded.get)
        rounded[top_ticker] = round(rounded[top_ticker] + rounding_gap, 2)

    portfolio = []
    for item in ranked:
        ticker = item["ticker"]
        weight = rounded.get(ticker, 0.0)
        if weight <= 0:
            continue
        portfolio.append(
            {
                "ticker": ticker,
                "weight_percent": weight,
                "reason": f"{display_name(ticker)}の説明用スコアが{item['score']:.1f}点で、候補内の相対的な評価が高い順に配分。",
            }
        )

    total = round(sum(item["weight_percent"] for item in portfolio) + cash_weight_percent, 2)
    key_risks = [
        "これは価格・企業データなどを単純なルールで点数化した研究用の配分です。",
        "同じ業種や値動きの似た銘柄に集中すると、同時に下落する可能性があります。",
    ]
    return {
        "portfolio": portfolio,
        "cash_percent": round(cash_weight_percent, 2),
        "total_percent": total,
        "summary": "候補銘柄の説明用スコアを相対比較し、上限を守りながら高い銘柄にやや厚く配分したローカル自動配分です。",
        "key_risks": key_risks,
    }
