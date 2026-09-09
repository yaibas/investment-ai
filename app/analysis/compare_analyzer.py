from __future__ import annotations

from typing import Any

from analysis.explain_score import explain_score
from data.ticker_master import display_name


def compare_stocks(market_data: list[dict[str, Any]]) -> str:
    """Compare stocks locally without an external LLM or API key."""
    valid_data = [item for item in market_data if "error" not in item]
    if not valid_data:
        raise ValueError("比較できる市場データがありません")

    ranked = sorted(valid_data, key=lambda item: explain_score(item)["overall_score"], reverse=True)
    lines = ["ローカル自動比較（APIキー不要）", ""]
    lines.append("総合ランキング:")
    for index, item in enumerate(ranked, 1):
        score = explain_score(item)
        name = display_name(item["ticker"])
        reasons = []
        for category_reasons in score["reasons"].values():
            if category_reasons:
                reasons.append(category_reasons[0])
        lines.append(f"{index}. {name}（{item['ticker']}） - {score['label']} / {score['overall_score']:.1f}点")
        lines.append(f"   主な材料: {'、'.join(reasons[:3])}")

    top = ranked[0]
    top_score = explain_score(top)
    lines.extend(
        [
            "",
            f"最も点数が高い銘柄: {display_name(top['ticker'])}（{top['ticker']}）",
            f"理由: {top_score['label']} / 総合スコア {top_score['overall_score']:.1f}点。",
            "",
            "注意:",
            "- この比較は取得できた価格・企業データなどを単純なルールで整理したものです。",
            "- AIや外部APIを使わないため、文章の柔軟さより再現性と低コストを優先しています。",
            "- 将来の利益や株価を保証するものではありません。",
        ]
    )
    return "\n".join(lines)
