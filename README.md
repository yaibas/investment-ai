# Investment AI

AI-assisted investment analysis project.

## Current scope
- Fetch real market data with `yfinance`
- Compare multiple tickers in one run
- Calculate technical indicators such as SMA, EMA, RSI, MACD, and volatility
- Include recent company fundamentals and news context when available
- Run a historical SMA-crossover backtest with configurable trading friction
- Compare multiple SMA strategies across multiple tickers in one batch
- Export batch backtest results to CSV
- Manage a saved paper portfolio with virtual buy/sell transactions
- Generate AI-based paper-portfolio allocation proposals with configurable cash and single-asset limits
- Apply an allocation proposal to the saved paper portfolio through virtual rebalancing
- Record paper-portfolio valuation history and calculate cumulative return and maximum drawdown
- Ask an LLM to rank attention candidates and explain risks
- Analysis only: no real-money order execution

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

### 7. Generate and apply an AI paper allocation

```powershell
python app\rebalance.py 7203.T 6758.T 8306.T 9984.T --cash 20 --max-weight 35
```

This analyzes the selected tickers, proposes constrained research weights, and applies them to `paper_portfolio.json` through virtual trades only.

### 8. Record portfolio performance history

After a paper portfolio exists, record today's valuation:

```powershell
python app\portfolio_history.py --record
```

View the saved history and metrics:

```powershell
python app\portfolio_history.py
```

History is stored in `portfolio_history.json` by default. Re-running `--record` on the same day updates that day's snapshot instead of adding a duplicate.

## Safety and scope

This project is intended for research and paper-trading workflows. It does not place real orders. AI output and historical backtests do not guarantee future performance.
