from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from ai_portfolio_backtest import run_ai_allocation_historical_check
from analysis.compare_analyzer import compare_stocks
from analysis.explain_score import explain_score
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
    st.info("ここでは実際のお金を動かしません。分析・検証・仮想運用用です。")

tickers = [item.strip().upper() for item in ticker_text.split(",") if item.strip()]
try:
    strategies = [parse_strategy(item.strip()) for item in strategies_text.split(",") if item.strip()]
except ValueError as exc:
    st.error(str(exc))
    strategies = []

analysis_tab, ai_portfolio_tab, test_tab, terms_tab = st.tabs(
    ["🔎 AI分析", "🧠 AIポートフォリオ", "🧪 過去でテスト", "📚 用語"]
)

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
                    score = explain_score(item)
                    table_rows.append(
                        {
                            "銘柄": item["ticker"],
                            "価格": item["price"],
                            "前日比(%)": item["change_percent"],
                            "総合スコア": score["overall_score"],
                            "評価": score["label"],
                            "PER": fundamentals.get("trailing_pe"),
                            "PBR": fundamentals.get("price_to_book"),
                            "RSI": technical.get("rsi_14"),
                        }
                    )
                scores_df = pd.DataFrame(table_rows).sort_values("総合スコア", ascending=False)
                st.dataframe(scores_df, use_container_width=True, hide_index=True)

                st.subheader("なぜこの点数？")
                st.caption("点数はAIの予言ではなく、取得できたデータを初心者向けに整理するための説明用スコアです。")
                for item in valid:
                    score = explain_score(item)
                    with st.expander(f"{item['ticker']}：{score['overall_score']:.1f}点 — {score['label']}"):
                        cols = st.columns(4)
                        for column, (name, value) in zip(cols, score["components"].items()):
                            column.metric(name, f"{value:.1f}")
                        st.write("主な理由")
                        for category, reasons in score["reasons"].items():
                            st.markdown(f"**{category}**")
                            for reason in reasons:
                                st.write(f"- {reason}")
                        st.caption(score["note"])

                st.subheader("AIの比較")
                with st.spinner("AIが比較しています…"):
                    st.write(compare_stocks(valid))
        except Exception as exc:
            st.error(f"エラー: {exc}")
    else:
        st.info("まず銘柄コードを確認して「分析を開始」を押してください。")

with ai_portfolio_tab:
    st.subheader("AIにポートフォリオを作ってもらう")
    st.write("入力した候補銘柄をAIが比較し、『どれを何％持つか』を決め、その配分を過去の価格データで確認します。")
    st.warning(
        "これは現在のAI配分を過去価格に当てはめる『歴史的感度チェック』です。 "
        "過去時点の情報だけでAIが判断した厳密なアウトオブサンプル検証ではありません。"
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        cash_weight = st.slider("現金比率（%）", 0, 50, 10, 5)
    with col2:
        max_weight = st.slider("1銘柄の上限（%）", 10, 100, 40, 5)
    with col3:
        rebalance = st.selectbox("再配分の頻度", ["monthly", "daily"], format_func=lambda x: "毎月" if x == "monthly" else "毎日")

    if st.button("AI配分を作って過去検証", type="primary"):
        if len(tickers) < 2:
            st.error("2銘柄以上を入力してください。")
        else:
            try:
                with st.spinner("現在のデータを集めてAIが配分を考えています…"):
                    current_data = get_multiple_market_data(tickers, period=period, news_count=5)
                    result = run_ai_allocation_historical_check(
                        current_data,
                        period="10y",
                        cash_weight_percent=float(cash_weight),
                        max_single_weight_percent=float(max_weight),
                        rebalance=rebalance,
                    )

                allocation = result["allocation"]
                backtest = result["backtest"]

                st.subheader("AIが考えた配分")
                allocation_rows = [
                    {
                        "銘柄": item["ticker"],
                        "比率(%)": item["weight_percent"],
                        "理由": item["reason"],
                    }
                    for item in allocation["portfolio"]
                ]
                allocation_rows.append({"銘柄": "現金", "比率(%)": allocation["cash_percent"], "理由": "価格変動に備えるための待機資金"})
                st.dataframe(pd.DataFrame(allocation_rows), use_container_width=True, hide_index=True)
                st.write(f"**AIの方針:** {allocation['summary']}")
                if allocation["key_risks"]:
                    st.write("**主なリスク**")
                    for risk in allocation["key_risks"]:
                        st.write(f"- {risk}")

                st.subheader("過去10年の価格で確認")
                c1, c2, c3 = st.columns(3)
                c1.metric("累積リターン", f"{backtest['total_return_percent']:.2f}%")
                c2.metric("年率リターン", f"{backtest['annualized_return_percent']:.2f}%")
                c3.metric("最大下落", f"{backtest['max_drawdown_percent']:.2f}%")
                c4, c5, c6 = st.columns(3)
                c4.metric("値動きの大きさ", f"{backtest['annualized_volatility_percent']:.2f}%")
                c5.metric("シャープレシオ", f"{backtest['sharpe_ratio']}")
                c6.metric("ソルティノレシオ", f"{backtest['sortino_ratio']}")
                st.caption(f"検証期間: {backtest['start']} ～ {backtest['end']} / 再配分: {'毎月' if rebalance == 'monthly' else '毎日'} / 現金: {backtest['cash_weight_percent']:.1f}%")
                st.info(result["test_warning"])
            except Exception as exc:
                st.error(f"エラー: {exc}")
    else:
        st.info("候補銘柄を2つ以上入力して、AI配分の検証を開始してください。")

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
            c4, c5, c6 = st.columns(3)
            c4.metric("値動きの大きさ", f"{wf['out_of_sample_annualized_volatility_percent']:.2f}%")
            c5.metric("効率スコア", f"{wf['out_of_sample_sharpe_ratio'] if wf['out_of_sample_sharpe_ratio'] is not None else '—'}")
            c6.metric("下落だけで見た効率", f"{wf['out_of_sample_sortino_ratio'] if wf['out_of_sample_sortino_ratio'] is not None else '—'}")
            st.caption(f"同じテスト期間で『買ってそのまま持つ』場合: {wf['out_of_sample_buy_hold_return_percent']:.2f}%")
            st.dataframe(pd.DataFrame(wf["periods"]), use_container_width=True, hide_index=True)
            st.info("見方: 年率リターンは年間ペースの成績、値動きの大きさは成績のブレ、最大の下落はピークからの最大下落です。効率スコア（シャープ）は『リスクに対してどれくらい成績が出たか』、下落だけで見た効率（ソルティノ）は『下落リスクを重く見た効率』の目安です。数字が高いほど一概に優秀とは限りません。")
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
        ("ボラティリティ", "値動きの大きさ。大きいほど、成績がブレやすいと考える。"),
        ("シャープレシオ", "リスクに対してどれくらいリターンが出たかを見る目安。高いほど効率が良い傾向。"),
        ("ソルティノレシオ", "特に下落方向のブレを重く見て、成績の効率を確認する目安。"),
        ("AIポートフォリオ検証", "AIが現在の候補銘柄から配分を考え、その配分を過去価格に当てはめて動きを確認すること。厳密な過去時点のAI判断を再現するものではない。"),
    ]
    for name, explanation in terms:
        with st.expander(name):
            st.write(explanation)
