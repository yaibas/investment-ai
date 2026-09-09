from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def compare_stocks(market_data: list[dict[str, Any]]) -> str:
    """Compare multiple market-data records with an LLM."""
    valid_data = [item for item in market_data if "error" not in item]
    if not valid_data:
        raise ValueError("比較できる市場データがありません")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY が設定されていません")

    client = OpenAI(api_key=api_key)

    compact = [
        {
            "ticker": item["ticker"],
            "date": item["date"],
            "price": item["price"],
            "change_percent": item["change_percent"],
            "volume": item["volume"],
            "open": item["open"],
            "high": item["high"],
            "low": item["low"],
        }
        for item in valid_data
    ]

    prompt = f"""
あなたは投資分析アシスタントです。

以下の複数銘柄の市場データを比較してください。

{json.dumps(compact, ensure_ascii=False, indent=2)}

次の形式で回答してください。

総合ランキング:
1. ティッカー - 注目度（高/中/低）
   理由:
   リスク:
2. ...

最も注目する銘柄:
理由:

注意:
- 数値データから考えられる材料を説明してください。
- 将来の利益を保証しないでください。
- 買い/売りを断定せず、「注目候補」として説明してください。
"""

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6"),
        input=prompt,
    )
    return response.output_text
