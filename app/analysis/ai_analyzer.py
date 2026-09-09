import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY が設定されていません")

client = OpenAI(api_key=api_key)


def analyze_stock(stock_data: dict) -> str:
    """Market data を AI に渡して、投資候補を分析する。"""
    prompt = f"""
あなたは投資分析アシスタントです。

以下の市場データを分析してください。

銘柄名: {stock_data["name"]}
ティッカー: {stock_data["ticker"]}
現在価格: {stock_data["price"]}
1日の変化率: {stock_data["change_percent"]}%
出来高: {stock_data["volume"]}

以下の形式で回答してください。

判定: 買い候補 / 売り候補 / 様子見
理由:
リスク:
注目ポイント:

投資判断を断定せず、与えられたデータから考えられる材料を説明してください。
"""

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6"),
        input=prompt,
    )

    return response.output_text
