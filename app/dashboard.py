from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from analysis.compare_analyzer import compare_stocks
from backtest import download_history, sma_crossover_backtest
from data.multi_market import get_multiple_market_data
from walk_forward import parse_strategy, walk_forward_backtest


st.set_page_config(page_title="Investment AI", page_icon="📈", layout="wide")

st.title("📈 Investment AI")
st.caption("市場データを集め、AIで比較し、過去データで検証する初心者向けツール")

with st.sidebar:
    st.header("設定")
    ticker_text = st.text_input("銘柄コード", "7203.T, 6758.T, 8306.T")
    period = st.selectbox("株価を調べる期間", ["3mo", "6mo", "1y", "2y", "5y", "10y"], index=1)
    strategies_text = st.text_input("検証する方法", "10:30, 20:50, 50:200")
    cash_note = st.info("ここでは実際のお金を動かしません。分析・検証・仮想運用用です。")

tickers = [item.strip().upper() for item in ticker_text.split(",") if item.strip()]
try:
    strategies = [parse_strategy(item.strip()) for item in strategies_text.split(",") if item.strip()]
except ValueError as exc:
    st.error(str(exc))
    strategies = []

analysis_tab, test_tab, terms_tab = st.tabs(["🔎 AI分析", "🧪 過去でテスト", "📚 用語"],)

with analysis_tab:
    st.subheader("銘柄を比べる")
    st.write("入力した銘柄について、価格・会社情報・最近のニュースなどをまとめ、AIが比較します。")
    if st.button("分析を開始", type="primary") and tickers:
        try:
            with st.spinner("市場データを取得しています…"):
                data = get_multiple_market_data(tickers, period=period, news_count=5)
            valid = [item for item in data if "error" not in item]
            errors = [item for item in data if "error" in item]
            if errors:
                for item in errors:
                    st.warning(f"{item['ticker']}: {item['error']}")
            if valid:
                table_rows = []
                for item in valid:
                    fundamentals = item.get("fundamentals", {})
                    technical = item.get("technical", {})
                    table_rows.append(
                        {
                            "銘柄": item["ticker"],
                            "価格": item["price"],
                            "前日比(%)": item["change_percent"],
                            "PER": fundamentals.get("trailing_pe"),
                            "PBR": fundamentals.get("price_to_book"),
                            "RSI": technical.get("rsi_14"),
                        }
                    )
                st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
                st.subheader("AIの比較")
                with st.spinner("AIが比較しています…"):
                    st.write(compare_stocks(valid))
        except Exception as exc:
            st.error(f"エラー: {exc}")
    else:
        st.info("まず銘柄コードを確認して「分析を開始」を押してください。")

with test_tab:
    st.subheader("過去の株価で試す")
    st.write("ここでは『この方法を昔から使っていたらどうなった？』を計算します。未来の利益を保証するものではありません。")
    selected_ticker = tickers[0] if tickers else "7203.T"
    col1, col2 = st.columns(2)
    with col1:
        train_years = st.number_input("過去を見て方法を選ぶ期間（年）", min_value=1, max_value=5, value=2, step=1)
    with col2:
        test_months = st.number_input("その後をテストする期間（月）", min_value=1, max_value=12, value=6, step=1)

    if st.button("過去テストを開始") and strategies:
        try:
            with st.spinner("過去の株価を計算しています…"):
                history = download_history(selected_ticker, period="10y")
                wf = walk_forward_backtest(
                    history,
                    strategies,
                    train_days=int(train_years * 252),
                    test_days=int(test_months * 21),
                )
            c1, c2, c3 = st.columns(3)
            c1.metric("未知の期間での累積成績", f"{wf['out_of_sample_return_percent']:.2f}%")
            c2.metric("年率換算", f"{wf['out_of_sample_annualized_return_percent']:.2f}%")
            c3.metric("最大の下落", f"{wf['out_of_sample_max_drawdown_percent']:.2f}%")
            st.caption(f"同じテスト期間で『買ってそのまま持つ』場合: {wf['out_of_sample_buy_hold_return_percent']:.2f}%")
            st.dataframe(pd.DataFrame(wf["periods"]), use_container_width=True)
        except Exception as exc:
            st.error(f"エラー: {exc}")

with terms_tab:
    st.subheader("難しい言葉をかんたんに")
    terms = [
        ("バックテスト", "過去の株価を使って、投資方法を試すこと。"),
        ("SMA", "一定期間の株価の平均。10:30なら10日平均と30日平均を比べる。"),
        ("最大下落", "資産がピークからどれくらい大きく減ったか。大きいほど値下がりがきつかった。"),
        ("AI分析", "価格だけでなく、会社情報やニュースなども材料にして比較すること。"),
        ("ウォークフォワード検証", "過去だけで方法を選び、その後の『まだ見ていない期間』で試すこと。過去に合わせすぎていないかを見るために使う。"),
        ("スリッページ", "注文した価格と、実際に成立すると仮定した価格のズレ。テストでは少し不利な条件として入れる。"),
    ]
    for name, explanation in terms:
        with st.expander(name):
            st.write(explanation)
