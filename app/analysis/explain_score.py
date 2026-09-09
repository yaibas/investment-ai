from __future__ import annotations

from typing import Any


def _bounded_score(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _optional_float(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def explain_score(item: dict[str, Any]) -> dict[str, Any]:
    """Create a transparent educational score from available market information.

    This is not a prediction model and is intentionally simple so a beginner can
    see which inputs affected the score.
    """
    technical = item.get("technical", {})
    fundamentals = item.get("fundamentals", {})
    news = item.get("news", [])

    price = _optional_float(item, "price")
    change = _optional_float(item, "change_percent")
    sma20 = _optional_float(technical, "sma_20")
    sma50 = _optional_float(technical, "sma_50")
    rsi = _optional_float(technical, "rsi_14")
    macd = _optional_float(technical, "macd")
    macd_signal = _optional_float(technical, "macd_signal")
    pe = _optional_float(fundamentals, "trailing_pe")
    operating_margin = _optional_float(fundamentals, "operating_margin_percent")
    net_margin = _optional_float(fundamentals, "net_margin_percent")

    technical_score = 50.0
    technical_reasons: list[str] = []
    if price is not None and sma20 is not None:
        if price > sma20:
            technical_score += 15
            technical_reasons.append("現在価格が20日平均より上")
        else:
            technical_score -= 15
            technical_reasons.append("現在価格が20日平均より下")
    if sma20 is not None and sma50 is not None:
        if sma20 > sma50:
            technical_score += 15
            technical_reasons.append("20日平均が50日平均より上")
        else:
            technical_score -= 15
            technical_reasons.append("20日平均が50日平均より下")
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            technical_score += 10
            technical_reasons.append("MACDがシグナルより上")
        else:
            technical_score -= 10
            technical_reasons.append("MACDがシグナルより下")
    if rsi is not None:
        if 45 <= rsi <= 65:
            technical_score += 10
            technical_reasons.append("RSIが極端ではない")
        elif rsi > 70:
            technical_score -= 10
            technical_reasons.append("RSIが高く、過熱の可能性")
        elif rsi < 30:
            technical_score -= 5
            technical_reasons.append("RSIが低く、弱い動きの可能性")

    fundamental_score = 50.0
    fundamental_reasons: list[str] = []
    if pe is not None:
        if 0 < pe <= 20:
            fundamental_score += 15
            fundamental_reasons.append("PERが比較的低い")
        elif pe > 40:
            fundamental_score -= 15
            fundamental_reasons.append("PERが高め")
        else:
            fundamental_score += 5
            fundamental_reasons.append("PERは中間的な水準")
    if operating_margin is not None:
        fundamental_score += 10 if operating_margin >= 10 else -5
        fundamental_reasons.append(
            "営業利益率が10%以上" if operating_margin >= 10 else "営業利益率が10%未満"
        )
    if net_margin is not None:
        fundamental_score += 10 if net_margin >= 5 else -5
        fundamental_reasons.append(
            "純利益率が5%以上" if net_margin >= 5 else "純利益率が5%未満"
        )

    news_score = 50.0
    news_reasons: list[str] = []
    news_count = len(news) if isinstance(news, list) else 0
    if news_count >= 3:
        news_score += 10
        news_reasons.append("最近のニュース材料が複数ある")
    elif news_count == 0:
        news_score -= 5
        news_reasons.append("取得できたニュースが少ない")
    else:
        news_reasons.append("最近のニュース材料を確認")

    momentum_score = 50.0 + (change or 0.0) * 3.0
    momentum_score = _bounded_score(momentum_score)
    if change is not None:
        momentum_reasons = [f"前日比 {change:.2f}%"]
    else:
        momentum_reasons = ["前日比データなし"]

    components = {
        "テクニカル": round(_bounded_score(technical_score), 1),
        "会社の数字": round(_bounded_score(fundamental_score), 1),
        "最近の材料": round(_bounded_score(news_score), 1),
        "直近の値動き": round(momentum_score, 1),
    }
    overall = round(sum(components.values()) / len(components), 1)

    if overall >= 70:
        label = "比較的強い材料"
    elif overall >= 55:
        label = "やや良い材料"
    elif overall >= 45:
        label = "中立"
    else:
        label = "注意材料が多い"

    return {
        "overall_score": overall,
        "label": label,
        "components": components,
        "reasons": {
            "テクニカル": technical_reasons or ["利用できるデータが少ない"],
            "会社の数字": fundamental_reasons or ["利用できる企業データが少ない"],
            "最近の材料": news_reasons,
            "直近の値動き": momentum_reasons,
        },
        "note": "この点数は説明用の単純なルールで計算しており、将来の株価を予測するものではありません。",
    }
