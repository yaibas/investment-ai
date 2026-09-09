from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _build_records(market_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for item in market_data:
        if "error" in item:
            continue
        fundamentals = item.get("fundamentals") or {}
        technical = item.get("technical") or {}
        records.append(
            {
                "ticker": item.get("ticker"),
                "price": item.get("price"),
                "change_percent": item.get("change_percent"),
                "technical": technical,
                "fundamentals": {
                    "company_name": fundamentals.get("company_name"),
                    "sector": fundamentals.get("sector"),
                    "market_cap": fundamentals.get("market_cap"),
                    "trailing_pe": fundamentals.get("trailing_pe"),
                    "forward_pe": fundamentals.get("forward_pe"),
                    "price_to_book": fundamentals.get("price_to_book"),
                    "operating_margin_percent": fundamentals.get("operating_margin_percent"),
                    "net_margin_percent": fundamentals.get("net_margin_percent"),
                },
                "news": (item.get("news") or [])[:5],
            }
        )
    return records


def suggest_allocation(
    market_data: list[dict[str, Any]],
    cash_weight_percent: float = 10.0,
    max_single_weight_percent: float = 40.0,
) -> dict[str, Any]:
    """Ask an LLM for an analysis-based paper-portfolio allocation suggestion."""
    if not market_data:
        raise ValueError("分析対象データがありません")
    if not 0 <= cash_weight_percent <= 100:
        raise ValueError("cash_weight_percent は0〜100で指定してください")
    if not 1 <= max_single_weight_percent <= 100:
        raise ValueError("max_single_weight_percent は1〜100で指定してください")

    records = _build_records(market_data)
    if not records:
        raise ValueError("有効な銘柄データがありません")

    target_total = 100.0 - cash_weight_percent
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    client = OpenAI()

    prompt = f"""
あなたは投資分析支援AIです。以下の銘柄データだけを使って、仮想ポートフォリオの配分案を作成してください。

重要:
- これは過去・現在データに基づく研究用の仮想配分であり、利益を保証しない。
- 実際の売買注文は行わない。
- 最終的な配分は100%。現金は{cash_weight_percent:.1f}%固定、残り{target_total:.1f}%を銘柄へ配分する。
- 1銘柄の配分上限は{max_single_weight_percent:.1f}%。
- データが不足する銘柄には無理に高い比率を付けない。
- PER/PBR、利益率、テクニカル、ニュース、集中リスクを総合評価する。
- 未来の株価や収益を断定しない。

次のJSONだけを返してください。Markdownや説明文は不要です。
{{
  "portfolio": [
    {{"ticker": "7203.T", "weight_percent": 30.0, "reason": "..."}}
  ],
  "cash_percent": {cash_weight_percent:.1f},
  "summary": "全体の考え方",
  "key_risks": ["...", "..."]
}}

銘柄データ:
{json.dumps(records, ensure_ascii=False)}
"""

    response = client.responses.create(model=model, input=prompt)
    text = response.output_text.strip()
    result = json.loads(text)

    portfolio = result.get("portfolio") or []
    normalized = []
    for item in portfolio:
        ticker = str(item.get("ticker", "")).strip().upper()
        try:
            weight = float(item.get("weight_percent", 0))
        except (TypeError, ValueError):
            continue
        weight = max(0.0, min(weight, max_single_weight_percent))
        if ticker and weight > 0:
            normalized.append(
                {
                    "ticker": ticker,
                    "weight_percent": round(weight, 2),
                    "reason": str(item.get("reason", "")),
                }
            )

    total = sum(item["weight_percent"] for item in normalized)
    tolerance = 0.05
    if abs(total - target_total) > tolerance:
        raise ValueError(
            f"AI配分の合計が不正です: 銘柄={total:.2f}%, 目標={target_total:.2f}%"
        )

    cash = float(result.get("cash_percent", cash_weight_percent))
    if abs(cash - cash_weight_percent) > tolerance:
        raise ValueError("AIが指定した現金比率が設定値と一致しません")

    return {
        "portfolio": normalized,
        "cash_percent": round(cash_weight_percent, 2),
        "total_percent": round(total + cash_weight_percent, 2),
        "summary": str(result.get("summary", "")),
        "key_risks": result.get("key_risks") or [],
    }
