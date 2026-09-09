from __future__ import annotations

from typing import Any


WEIGHTS = {
    "technical": 0.30,
    "fundamental": 0.30,
    "news": 0.15,
    "momentum": 0.25,
}

LABELS = {
    "technical": "チャートの状態",
    "fundamental": "会社の数字",
    "news": "最近の材料",
    "momentum": "直近の値動き",
}


def build_decision_framework(score: dict[str, Any]) -> dict[str, Any]:
    """Explain how the beginner score contributes to the overall result."""
    components = score.get("components") or {}
    normalized = {
        "technical": float(components.get("テクニカル", 0)),
        "fundamental": float(components.get("会社の数字", 0)),
        "news": float(components.get("最近の材料", 0)),
        "momentum": float(components.get("直近の値動き", 0)),
    }
    contributions = {
        key: round(normalized[key] * weight, 1)
        for key, weight in WEIGHTS.items()
    }
    return {
        "weights": WEIGHTS.copy(),
        "labels": LABELS.copy(),
        "scores": normalized,
        "contributions": contributions,
        "total": round(sum(contributions.values()), 1),
        "note": "各点数に重みを掛けて合計しています。説明用のルールであり、将来の株価を予測するものではありません。",
    }
