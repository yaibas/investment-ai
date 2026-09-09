# Investment AI

AI-assisted investment analysis project.

## Current scope
- Fetch real market data with `yfinance`
- Compare multiple tickers in one run
- Calculate technical indicators such as SMA, EMA, RSI, MACD, and volatility
- Include recent company fundamentals and news context when available
- Run a historical SMA-crossover backtest with configurable trading friction
- Report risk metrics such as volatility, Sharpe ratio, and Sortino ratio
- Compare multiple SMA strategies across multiple tickers in one batch
- Export batch backtest results to CSV
- Run walk-forward validation so strategy selection is tested on later unseen periods
- Manage a saved paper portfolio with virtual buy/sell transactions
- Generate AI-based paper-portfolio allocation proposals with configurable cash and single-asset limits
- Apply an allocation proposal to the saved paper portfolio through virtual rebalancing
- Record paper-portfolio valuation history and calculate cumulative return and maximum drawdown
- Provide a beginner-friendly Streamlit dashboard
- Explain analysis scores and the evidence behind them
- Ask an LLM to rank attention candidates and explain risks
- Analysis only: no real-money order execution

## Beginner-friendly dashboard (Windows)

After installing dependencies, start the dashboard with:

```powershell
streamlit run app\dashboard.py
```

The dashboard lets you enter ticker codes, run AI comparisons, test strategies on historical data, see risk metrics, and open a built-in glossary for difficult terms.

## Quick start (Windows)

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Set your API key

Copy `.env.example` to `.env`, then put your API key in `.env`:

```env
OPENAI_API_KEY=your_api_key_here
```

Set `OPENAI_MODEL` to a model available to your API account. The code reads the value from `.env` rather than requiring a model name in source code.

### 4. Run a multi-ticker analysis

```powershell
python app\run_analysis.py 7203.T 6758.T 9984.T 8306.T
```

### 5. Run a single backtest

```powershell
python app\backtest.py 7203.T --period 5y --fast 20 --slow 50
```

The result now includes both performance and risk information, such as annualized volatility, Sharpe ratio, and Sortino ratio.

### 6. Run a multi-ticker × multi-strategy backtest

The batch command evaluates every requested SMA configuration against every ticker and ranks the results by annualized return.

```powershell
python app\batch_backtest.py 7203.T 6758.T 8306.T 9984.T --period 5y
```

Specify strategies explicitly:

```powershell
python app\batch_backtest.py 7203.T 6758.T 8306.T --period 10y --strategy 10:30 --strategy 20:50 --strategy 50:200
```

Export the same results to CSV:

```powershell
python app\batch_backtest.py 7203.T 6758.T 8306.T --csv backtest_results.csv
```

### 7. Run a walk-forward validation

This first chooses the better strategy from an older training period, then tests that choice on the following period that was not used for selection. It also reports risk metrics for the unseen periods.

```powershell
python app\walk_forward.py 7203.T --period 10y
```

### 8. Generate and apply an AI paper allocation

```powershell
python app\rebalance.py 7203.T 6758.T 8306.T 9984.T --cash 20 --max-weight 35
```

This analyzes the selected tickers, proposes constrained research weights, and applies them to `paper_portfolio.json` through virtual trades only.

### 9. Record portfolio performance history

After a paper portfolio exists, record today's valuation:

```powershell
python app\portfolio_history.py --record
```

View the saved history and metrics:

```powershell
python app\portfolio_history.py
```

History is stored in `portfolio_history.json` by default. Re-running `--record` on the same day updates that day's snapshot instead of adding a duplicate.

## Beginner glossary

- **バックテスト**: 過去の株価を使って「この方法ならどうなったか」を試すこと。
- **SMA**: 一定期間の株価の平均。たとえば 20日SMA は直近20日間の平均。
- **最大ドローダウン**: 資産がピークからどれくらい大きく減ったか。
- **ボラティリティ**: 値動きの大きさ。大きいほど結果がブレやすい。
- **シャープレシオ**: リスクに対してどれくらい成績が出たかを見る目安。
- **ソルティノレシオ**: 下落方向のブレを重く見て、成績の効率を確認する目安。
- **スリッページ**: 注文したい価格と、実際に成立すると仮定した価格のズレ。
- **ウォークフォワード検証**: 過去だけで方法を選び、その後のまだ使っていないデータで検証すること。
- **ペーパー運用**: 実際のお金を使わず、仮想のお金で運用を試すこと。

## Safety and scope

This project is intended for research and paper-trading workflows. It does not place real orders. AI output and historical backtests do not guarantee future performance.
