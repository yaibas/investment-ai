# Investment AI

AI-assisted investment analysis project.

## Current scope
- Fetch market data with `yfinance`
- Select common Japanese stocks by company name in the dashboard
- Compare multiple stocks with an explainable local rule-based analyzer
- Calculate technical indicators such as SMA, EMA, RSI, MACD, and volatility
- Include recent company fundamentals and news context when available
- Run historical SMA-crossover backtests with trading friction
- Report risk metrics such as volatility, Sharpe ratio, and Sortino ratio
- Compare multiple SMA strategies and run walk-forward validation
- Run multi-asset portfolio backtests with daily/monthly rebalancing and cash reserves
- Generate a local rule-based allocation proposal without an API key
- Check that allocation against historical prices as a historical sensitivity check
- Simulate buying and selling inside the app with virtual 💎 diamonds
- Persist the virtual portfolio and transaction history locally
- Provide a beginner-friendly Streamlit dashboard
- Analysis and simulation only: no real-money order execution

## Important: no OpenAI API key is required

The current dashboard does not call OpenAI or another LLM. The comparison and portfolio allocation screens use deterministic, explainable local rules based on the market data the app retrieves. This keeps the app usable without an API key or API credit.

## Beginner-friendly dashboard (Windows)

After installing dependencies, start the dashboard with:

```powershell
streamlit run app\dashboard.py
```

The dashboard lets you select common Japanese companies by name, compare them, build a rule-based portfolio, test it against historical prices, and trade using virtual diamonds.

## Quick start (Windows)

### 1. Create a virtual environment

```powershell
py -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Start the app

```powershell
streamlit run app\dashboard.py
```

No API key setup is required.

## Virtual diamond simulation

The dashboard starts with **100,000 💎 diamonds**. Diamonds are fictional in-app points and have no cash value.

- Select companies by name
- Buy using a chosen number of diamonds
- Sell held shares
- See current virtual portfolio value, holdings, unrealized profit/loss, and transaction history
- Reset the game to 100,000 diamonds at any time

The virtual portfolio is stored locally in `diamond_portfolio.json`.

## Historical portfolio check

The **自動ポートフォリオ** tab calculates a rule-based allocation from the selected companies, then applies that exact mix to historical prices.

Important: this is a **historical sensitivity check**, not proof that the same allocation could have been generated in the past. The current analysis can use information that was unavailable during the historical period.

## Beginner glossary

- **バックテスト**: 過去の株価を使って「この方法ならどうなったか」を試すこと。
- **最大ドローダウン**: 資産がピークからどれくらい大きく減ったか。
- **ボラティリティ**: 値動きの大きさ。
- **シャープレシオ**: リスクに対してどれくらい成績が出たかを見る目安。
- **ソルティノレシオ**: 下落方向のブレを重く見た効率の目安。
- **ウォークフォワード検証**: 過去だけで方法を選び、その後のまだ使っていないデータで検証すること。
- **ダイヤ**: このアプリ内だけで使う仮想ポイント。実際のお金ではありません。
- **自動ポートフォリオ**: 取得できた市場データを単純なルールで点数化し、配分を計算する機能。将来の値上がりを保証する予測ではありません。

## Safety and scope

This project is intended for research and paper-trading workflows. It does not place real orders. Historical results and local analysis do not guarantee future performance.
