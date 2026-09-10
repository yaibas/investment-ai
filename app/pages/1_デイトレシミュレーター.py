from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data.ticker_master import DISPLAY_NAMES, display_name, resolve_ticker
from diamond_portfolio import (
    DEFAULT_DIAMONDS,
    DiamondPortfolio,
    fetch_latest_prices,
    load_diamond_portfolio,
    save_diamond_portfolio,
)
from intraday import INTERVALS, add_intraday_indicators, fetch_intraday_history, intraday_summary
from realtime_market import fetch_realtime_history, fetch_realtime_snapshot, realtime_enabled


st.set_page_config(page_title="デイトレ・シミュレーター", page_icon="📊", layout="wide")
st.title("📊 デイトレ・シミュレーター")
st.caption("実際のお金は使わず、💎ダイヤで短期売買を体験する画面です")

PORTFOLIO_PATH = str(APP_DIR.parent / "diamond_portfolio.json")


def load_game() -> DiamondPortfolio:
    path = Path(PORTFOLIO_PATH)
    if path.exists():
        try:
            return load_diamond_portfolio(PORTFOLIO_PATH)
        except Exception:
            pass
    portfolio = DiamondPortfolio(diamonds=DEFAULT_DIAMONDS)
    save_diamond_portfolio(portfolio, PORTFOLIO_PATH)
    return portfolio


def realtime_interval(interval: str) -> str:
    return {
        "1m": "1",
        "2m": "1",
        "5m": "5",
        "15m": "15",
        "30m": "15",
        "60m": "60",
    }.get(interval, "1")


def load_market_data(ticker: str, interval: str, period: str) -> tuple[pd.DataFrame, dict, str]:
    if realtime_enabled():
        count = 400 if interval in ("1m", "2m", "5m", "15m") else 250
        data = fetch_realtime_history(ticker, interval=realtime_interval(interval), count=count)
        if interval == "2m":
            data = data.resample("2min", label="left", closed="left").agg(
                {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
            ).dropna(subset=["Open", "High", "Low", "Close"])
        elif interval == "30m":
            data = data.resample("30min", label="left", closed="left").agg(
                {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
            ).dropna(subset=["Open", "High", "Low", "Close"])
        if period == "1d":
            cutoff = data.index[-1].normalize()
            data = data[data.index >= cutoff]
        elif period == "5d":
            data = data[data.index >= data.index[-1] - pd.Timedelta(days=5)]
        elif period == "7d":
            data = data[data.index >= data.index[-1] - pd.Timedelta(days=7)]
        summary = intraday_summary(add_intraday_indicators(data))
        return data, summary, "リアルタイム市場データ"

    history = fetch_intraday_history(ticker, interval=interval, period=period)
    data = add_intraday_indicators(history)
    return data, intraday_summary(data), "Yahoo Finance（遅延する場合があります）"


portfolio = load_game()

with st.sidebar:
    st.subheader("銘柄")
    names = sorted(set(DISPLAY_NAMES.values()))
    selected_name = st.selectbox(
        "会社名",
        names,
        index=names.index("トヨタ自動車") if "トヨタ自動車" in names else 0,
    )
    ticker = resolve_ticker(selected_name)

    interval_label = st.selectbox("時間足", list(INTERVALS.keys()), index=0)
    interval = INTERVALS[interval_label]
    period_options = ["1d", "5d", "7d"] if interval == "1m" else ["1d", "5d", "30d", "60d"]
    period = st.selectbox("表示期間", period_options, index=0)
    refresh_seconds = st.select_slider(
        "自動更新",
        options=[1, 2, 5, 10, 15, 30, 60],
        value=2 if realtime_enabled() else 10,
        format_func=lambda x: f"{x}秒ごと",
    )

    st.divider()
    st.metric("💎 ダイヤ", f"{portfolio.diamonds:,.0f}")
    if realtime_enabled():
        st.success("🟢 リアルタイムデータ接続中")
        st.caption("TSE対応のリアルタイム市場データAPIを使用しています。")
    else:
        st.warning("🟡 Yahoo Financeモード")
        st.caption("KUN_DATA_TOKENを設定すると、リアルタイム市場データAPIへ切り替えられます。")


@st.fragment(run_every=refresh_seconds)
def show_market():
    try:
        data, summary, source = load_market_data(ticker, interval, period)
        data = add_intraday_indicators(data)
        summary = intraday_summary(data)
    except Exception as exc:
        st.error(f"株価データを取得できませんでした: {exc}")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("現在値", f"{summary['latest_price']:,.2f}", f"{summary['change_percent']:+.2f}%")
    c2.metric("表示期間の高値", f"{summary['high']:,.2f}")
    c3.metric("表示期間の安値", f"{summary['low']:,.2f}")
    c4.metric("出来高", f"{summary['volume']:,}")

    st.subheader(f"{display_name(ticker)} — {interval_label}")
    chart = go.Figure()
    chart.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="ローソク足",
        )
    )
    chart.add_trace(go.Scatter(x=data.index, y=data["EMA9"], mode="lines", name="EMA9"))
    chart.add_trace(go.Scatter(x=data.index, y=data["EMA20"], mode="lines", name="EMA20"))
    chart.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        yaxis_title="株価",
        legend_title="指標",
    )
    st.plotly_chart(chart, use_container_width=True, config={"displaylogo": False})

    volume_chart = go.Figure(go.Bar(x=data.index, y=data["Volume"], name="出来高"))
    volume_chart.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        yaxis_title="出来高",
    )
    st.plotly_chart(volume_chart, use_container_width=True, config={"displaylogo": False})

    latest = data.iloc[-1]
    rsi = latest.get("RSI14")
    ema9 = latest.get("EMA9")
    ema20 = latest.get("EMA20")
    c5, c6, c7 = st.columns(3)
    c5.metric("EMA9", f"{float(ema9):,.2f}" if pd.notna(ema9) else "—")
    c6.metric("EMA20", f"{float(ema20):,.2f}" if pd.notna(ema20) else "—")
    c7.metric("RSI14", f"{float(rsi):.1f}" if pd.notna(rsi) else "—")

    st.caption(f"データソース: {source} / 最新データ時刻: {summary['timestamp']}")
    if realtime_enabled():
        st.info(
            "🟢 リアルタイム市場データを使用しています。価格更新はデータ提供元の配信状況に依存します。"
            "この画面は仮想売買の練習用で、自動売買や実際の注文は行いません。"
        )
    else:
        st.info(
            "🟡 現在はYahoo Financeのデータです。完全なリアルタイム表示にするには、"
            "リアルタイム市場データAPIの認証情報が必要です。"
            "この画面は仮想売買の練習用で、自動売買や実際の注文は行いません。"
        )


show_market()

st.divider()
st.subheader("💎 仮想売買")

try:
    if realtime_enabled():
        live_quote = fetch_realtime_snapshot(ticker)
        latest_price = float(live_quote["price"])
        quotes = {ticker: latest_price}
    else:
        quotes = fetch_latest_prices([ticker])
        latest_price = quotes[ticker]
except Exception as exc:
    quotes = {}
    latest_price = None
    st.warning(f"売買用の最新価格を取得できませんでした: {exc}")

live = portfolio.valuation(quotes)
c1, c2, c3 = st.columns(3)
c1.metric("手持ちダイヤ", f"{live['diamonds']:,.0f}")
c2.metric("この銘柄の保有額", f"{next((x['market_value'] for x in live['holdings'] if x['ticker'] == ticker), 0):,.0f}")
c3.metric("総資産", f"💎 {live['total_value']:,.0f}")

buy_col, sell_col = st.columns(2)
with buy_col:
    st.write("**買う**")
    if latest_price is not None:
        buy_amount = st.number_input(
            "使うダイヤ",
            min_value=100.0,
            max_value=max(100.0, float(live["diamonds"])),
            value=min(10_000.0, max(100.0, float(live["diamonds"]))),
            step=100.0,
            key="day_buy_amount",
        )
        st.caption(f"1株あたり: {latest_price:,.2f} / 約 {buy_amount / latest_price:.6f} 株")
        if st.button("💎 買う", key="day_buy"):
            try:
                portfolio.buy_with_diamonds(ticker, buy_amount, latest_price)
                save_diamond_portfolio(portfolio, PORTFOLIO_PATH)
                st.success(f"{display_name(ticker)}を💎 {buy_amount:,.0f}で購入しました。")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with sell_col:
    st.write("**売る**")
    held = next((x for x in live["holdings"] if x["ticker"] == ticker), None)
    if latest_price is not None and held:
        sell_shares = st.number_input(
            "売る株数",
            min_value=0.000001,
            max_value=float(held["shares"]),
            value=float(held["shares"]),
            format="%.6f",
            key="day_sell_shares",
        )
        st.caption(f"売却予定額: 💎 {sell_shares * latest_price:,.0f}")
        if st.button("💎 売る", key="day_sell"):
            try:
                portfolio.sell_shares(ticker, sell_shares, latest_price)
                save_diamond_portfolio(portfolio, PORTFOLIO_PATH)
                st.success(f"{display_name(ticker)}を{sell_shares:.6f}株売却しました。")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    else:
        st.info("この銘柄をまだ保有していません。")

st.subheader("保有状況")
if live["holdings"]:
    holdings_df = pd.DataFrame(live["holdings"]).rename(
        columns={
            "ticker": "銘柄コード",
            "name": "銘柄名",
            "shares": "保有株数",
            "avg_price": "平均取得価格",
            "price": "現在価格",
            "market_value": "評価額",
            "unrealized_pnl": "含み損益",
        }
    )
    st.dataframe(holdings_df, use_container_width=True, hide_index=True)
else:
    st.info("まだ株を保有していません。")

st.subheader("取引履歴")
if live["transactions"]:
    history_rows = []
    for tx in reversed(live["transactions"][-30:]):
        history_rows.append(
            {
                "日付": tx.get("date"),
                "売買": "買い" if tx.get("side") == "BUY" else "売り",
                "銘柄": display_name(tx.get("ticker", "")),
                "株数": tx.get("shares"),
                "価格": tx.get("price"),
                "ダイヤ": tx.get("diamonds"),
            }
        )
    st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
else:
    st.info("取引履歴はありません。")
