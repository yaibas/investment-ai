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
from backtest import download_history
from data.multi_market import get_multiple_market_data
from data.ticker_master import DISPLAY_NAMES, display_name, resolve_ticker
from diamond_portfolio import (
    DEFAULT_DIAMONDS,
    DiamondPortfolio,
    fetch_latest_prices,
    load_diamond_portfolio,
    save_diamond_portfolio,
)
from walk_forward import parse_strategy, walk_forward_backtest


st.set_page_config(page_title="Investment AI", page_icon="📈", layout="wide")

st.title("📈 Investment AI")
st.caption("APIキー不要。市場データを集め、自動分析・過去検証・ダイヤで仮想運用できるツール")

PORTFOLIO_PATH = str(APP_DIR.parent / "diamond_portfolio.json")

with st.sidebar:
    st.header("銘柄を選ぶ")
    name_options = sorted(set(DISPLAY_NAMES.values()))
    default_names = ["トヨタ自動車", "ソニーグループ", "三菱UFJフィナンシャル・グループ"]
    selected_names = st.multiselect("銘柄名", name_options, default=default_names)
    st.caption("コードを覚える必要はありません。会社名で選べます。")
    period = st.selectbox("株価を調べる期間", ["3mo", "6mo", "1y", "2y", "5y", "10y"], index=1)
    strategies_text = st.text_input("検証する方法", "10:30, 20:50, 50:200")
    st.info("実際のお金は使いません。ダイヤを使う仮想投資です。")

# Company names are the main UI. Codes remain accepted as an advanced fallback.
tickers = [resolve_ticker(name) for name in selected_names]

try:
    strategies = [parse_strategy(item.strip()) for item in strategies_text.split(",") if item.strip()]
except ValueError as exc:
    st.error(str(exc))
    strategies = []


def load_game() -> DiamondPortfolio:
    path = Path(PORTFOLIO_PATH)
    if path.exists():
        try:
            return load_diamond_portfolio(PORTFOLIO_PATH)
        except Exception:
            pass
    portfolio = DiamondPortfolio()
    save_diamond_portfolio(portfolio, PORTFOLIO_PATH)
    return portfolio


def visible_prices(portfolio: DiamondPortfolio) -> dict[str, float]:
    tickers_for_quote = list(portfolio.positions)
    return fetch_latest_prices(tickers_for_quote) if tickers_for_quote else {}


portfolio = load_game()
try:
    current_prices = visible_prices(portfolio)
    valuation = portfolio.valuation(current_prices)
except Exception:
    current_prices = {}
    valuation = portfolio.valuation({})

st.sidebar.metric("💎 ダイヤ", f"{valuation['diamonds']:,.0f}")
st.sidebar.metric("総資産", f"💎 {valuation['total_value']:,.0f}")

analysis_tab, ai_portfolio_tab, test_tab, diamond_tab, terms_tab = st.tabs(
    ["🔎 自動分析", "🧠 自動ポートフォリオ", "🧪 過去でテスト", "💎 仮想投資", "📚 用語"]
)

with analysis_tab:
    st.subheader("銘柄を比べる")
    st.write("価格・会社情報・テクニカル指標などを取得し、APIなしのルールベース分析で比較します。")
    if st.button("分析を開始", type="primary"):
        if len(tickers) < 1:
            st.error("銘柄を1つ以上選んでください。")
        else:
            try:
                with st.spinner("市場データを取得しています…"):
                    data = get_multiple_market_data(tickers, period=period, news_count=5)
                valid = [item for item in data if "error" not in item]
                errors = [item for item in data if "error" in item]
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
                                "銘柄": display_name(item["ticker"]),
                                "コード": item["ticker"],
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
                    for item in valid:
                        score = explain_score(item)
                        with st.expander(f"{display_name(item['ticker'])}：{score['overall_score']:.1f}点 — {score['label']}"):
                            cols = st.columns(4)
                            for column, (name, value) in zip(cols, score["components"].items()):
                                column.metric(name, f"{value:.1f}")
                            for category, reasons in score["reasons"].items():
                                st.markdown(f"**{category}**")
                                for reason in reasons:
                                    st.write(f"- {reason}")
                            st.caption(score["note"])
                    st.subheader("自動比較")
                    st.write(compare_stocks(valid))
            except Exception as exc:
                st.error(f"エラー: {exc}")
    else:
        st.info("銘柄を選んで「分析を開始」を押してください。")

with ai_portfolio_tab:
    st.subheader("自動ポートフォリオを作る")
    st.write("選んだ銘柄の説明用スコアを使い、APIなしで配分案を計算します。")
    cash_weight = st.slider("現金比率（%）", 0, 50, 10, 5)
    max_weight = st.slider("1銘柄の上限（%）", 10, 100, 40, 5)
    rebalance = st.selectbox("再配分の頻度", ["monthly", "daily"], format_func=lambda x: "毎月" if x == "monthly" else "毎日")
    st.warning("過去検証は現在の配分を過去価格へ当てはめる感度チェックです。過去時点の判断を再現するものではありません。")

    if st.button("配分を作って過去検証", type="primary"):
        if len(tickers) < 2:
            st.error("2銘柄以上を選んでください。")
        elif len(tickers) * max_weight < 100 - cash_weight:
            st.error("1銘柄の上限が小さすぎます。候補数を増やすか上限を上げてください。")
        else:
            try:
                with st.spinner("データを集めて配分を計算しています…"):
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
                rows = [
                    {"銘柄": display_name(item["ticker"]), "比率(%)": item["weight_percent"], "理由": item["reason"]}
                    for item in allocation["portfolio"]
                ]
                rows.append({"銘柄": "現金", "比率(%)": allocation["cash_percent"], "理由": "価格変動に備える待機資金"})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.write(f"**方針:** {allocation['summary']}")
                st.write("**主なリスク**")
                for risk in allocation["key_risks"]:
                    st.write(f"- {risk}")
                c1, c2, c3 = st.columns(3)
                c1.metric("累積リターン", f"{backtest['total_return_percent']:.2f}%")
                c2.metric("年率リターン", f"{backtest['annualized_return_percent']:.2f}%")
                c3.metric("最大下落", f"{backtest['max_drawdown_percent']:.2f}%")
                c4, c5, c6 = st.columns(3)
                c4.metric("値動きの大きさ", f"{backtest['annualized_volatility_percent']:.2f}%")
                c5.metric("シャープレシオ", f"{backtest['sharpe_ratio']}")
                c6.metric("ソルティノレシオ", f"{backtest['sortino_ratio']}")
                st.caption(f"検証期間: {backtest['start']} ～ {backtest['end']} / 現金: {backtest['cash_weight_percent']:.1f}%")
                st.info(result["test_warning"])
            except Exception as exc:
                st.error(f"エラー: {exc}")
    else:
        st.info("2銘柄以上を選んでください。")

with test_tab:
    st.subheader("過去の株価で試す")
    if not tickers:
        st.info("銘柄を選んでください。")
    else:
        selected_ticker = tickers[0]
        col1, col2 = st.columns(2)
        with col1:
            train_years = st.number_input("過去を見て方法を選ぶ期間（年）", min_value=1, max_value=5, value=2, step=1)
        with col2:
            test_months = st.number_input("その後をテストする期間（月）", min_value=1, max_value=12, value=6, step=1)
        if st.button("過去テストを開始") and strategies:
            try:
                with st.spinner("過去の株価を計算しています…"):
                    history = download_history(selected_ticker, period="10y")
                    wf = walk_forward_backtest(history, strategies, train_days=int(train_years * 252), test_days=int(test_months * 21))
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
            except Exception as exc:
                st.error(f"エラー: {exc}")

with diamond_tab:
    st.subheader("💎 ダイヤで仮想投資")
    st.write("ここでは実際のお金を一切使わず、アプリ内のダイヤだけで売買を体験できます。")
    if st.button("💎 100,000ダイヤにリセット"):
        portfolio = DiamondPortfolio(diamonds=DEFAULT_DIAMONDS)
        save_diamond_portfolio(portfolio, PORTFOLIO_PATH)
        st.rerun()

    try:
        quote_tickers = sorted(set(tickers) | set(portfolio.positions))
        quotes = fetch_latest_prices(quote_tickers) if quote_tickers else {}
    except Exception as exc:
        quotes = {}
        st.warning(f"価格取得に失敗しました: {exc}")

    c1, c2, c3 = st.columns(3)
    live = portfolio.valuation(quotes)
    c1.metric("💎 手持ちダイヤ", f"{live['diamonds']:,.0f}")
    c2.metric("保有株評価額", f"{live['positions_value']:,.0f}")
    c3.metric("総資産", f"💎 {live['total_value']:,.0f}")

    buy_names = [display_name(t) for t in tickers]
    if buy_names:
        st.subheader("買う")
        buy_name = st.selectbox("銘柄", buy_names, key="buy_name")
        buy_ticker = resolve_ticker(buy_name)
        buy_price = quotes.get(buy_ticker)
        if buy_price is not None:
            st.write(f"現在価格: {buy_price:,.2f}")
            buy_amount = st.number_input("使うダイヤ", min_value=100.0, max_value=float(max(live['diamonds'], 100.0)), value=min(10_000.0, max(live['diamonds'], 100.0)), step=100.0)
            if st.button("買う", key="buy_action"):
                try:
                    portfolio.buy_with_diamonds(buy_ticker, buy_amount, buy_price)
                    save_diamond_portfolio(portfolio, PORTFOLIO_PATH)
                    st.success(f"{display_name(buy_ticker)}を💎 {buy_amount:,.0f}で購入しました。")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        else:
            st.info("価格を取得できませんでした。")
    else:
        st.info("まず左側で仮想投資する銘柄を選んでください。")

    if portfolio.positions:
        st.subheader("売る")
        sell_tickers = list(portfolio.positions)
        sell_ticker = st.selectbox("保有銘柄", sell_tickers, format_func=display_name)
        sell_position = portfolio.positions[sell_ticker]
        sell_price = quotes.get(sell_ticker)
        if sell_price is not None:
            sell_shares = st.number_input("売る株数", min_value=0.000001, max_value=float(sell_position.shares), value=float(sell_position.shares), step=max(float(sell_position.shares) / 10, 0.000001), format="%.6f")
            if st.button("売る", key="sell_action"):
                try:
                    portfolio.sell_shares(sell_ticker, sell_shares, sell_price)
                    save_diamond_portfolio(portfolio, PORTFOLIO_PATH)
                    st.success(f"{display_name(sell_ticker)}を売却しました。")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        holdings_df = pd.DataFrame(live["holdings"])
        if not holdings_df.empty:
            st.subheader("保有状況")
            st.dataframe(holdings_df[["name", "shares", "avg_price", "price", "market_value", "unrealized_pnl"]], use_container_width=True, hide_index=True)

    if live["transactions"]:
        st.subheader("取引履歴")
        tx = pd.DataFrame(live["transactions"])
        if not tx.empty:
            tx["銘柄"] = tx["ticker"].map(display_name)
            st.dataframe(tx, use_container_width=True, hide_index=True)

with terms_tab:
    st.subheader("難しい言葉をかんたんに")
    terms = [
        ("バックテスト", "過去の株価を使って、投資方法を試すこと。"),
        ("最大下落", "資産がピークからどれくらい大きく減ったか。"),
        ("ボラティリティ", "値動きの大きさ。"),
        ("シャープレシオ", "リスクに対してどれくらい成績が出たかを見る目安。"),
        ("ソルティノレシオ", "下落方向のブレを重く見た効率の目安。"),
        ("ダイヤ", "このアプリだけで使う仮想通貨。実際の円やドルではありません。"),
        ("自動ポートフォリオ", "APIを使わず、取得できたデータをルール化して銘柄配分を計算する機能。将来の値上がりを保証する予測ではありません。"),
    ]
    for name, explanation in terms:
        with st.expander(name):
            st.write(explanation)
