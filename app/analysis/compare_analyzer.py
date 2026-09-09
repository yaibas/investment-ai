from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def compare_stocks(market_data: list[dict[str, Any]]) -> str:
    """Compare market, technical, fundamental, and recent-news context."""
    valid_data = [item for item in market_data if "error" not in item]
    if not valid_data:
        raise ValueError("比較できる市場データがありません")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY が設定されていません")

    client = OpenAI(api_key=api_key)

    compact = []
    for item in valid_data:
        compact.append(
            {
                "ticker": item["ticker"],
                "date": item["date"],
                "price": item["price"],
                "change_percent": item["change_percent"],
                "volume": item["volume"],
                "open": item["open"],
                "high": item["high"],
                "low": item["low"],
                "technical": item.get("technical", {}),
                "fundamentals": item.get("fundamentals", {}),
                "news": item.get("news", []),
            }
        )

    prompt = f"""
あなたは投資分析アシスタントです。

以下の複数銘柄について、市場データ、テクニカル指標、企業ファンダメンタルズ、
最近のニュースを比較してください。

{json.dumps(compact, ensure_ascii=False, indent=2, default=str)}

次の形式で回答してください。

総合ランキング:
1. ティッカー - 注目度（高/中/低）
   主な材料:
   ポジティブ要因:
   ネガティブ要因:
   リスク:
2. ...

最も注目する銘柄:
理由:

ニュースの扱い:
- ニュースの見出しだけで将来を断定しないでください。
- ニュースは「材料の有無」を確認するために使い、事実と推測を分けてください。

ファンダメンタルズでは、PER、PBR、時価総額、売上高、営業利益、純利益、
営業利益率、純利益率など、利用できる項目を考慮してください。
テクニカルではSMA20/SMA50、EMA20、RSI14、MACD、20日ベースの年率換算ボラティリティを考慮してください。

注意:
- 提供されたデータから考えられる材料を説明してください。
- 将来の利益を保証しないでください。
- 買い/売りを断定せず、「注目候補」として説明してください。
"""

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6"),
        input=prompt,
    )
    return response.output_text
