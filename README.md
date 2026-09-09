# Investment AI

AI-assisted investment analysis project.

## Current scope
- Fetch real market data with `yfinance`
- Compare multiple tickers in one run
- Calculate technical indicators such as SMA, EMA, RSI, MACD, and volatility
- Include recent company fundamentals and news context when available
- Run a historical SMA-crossover backtest with configurable trading friction
- Manage a saved paper portfolio with virtual buy/sell transactions
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

You can change the tickers and history window:

```powershell
python app\run_analysis.py 7203.T 6758.T --period 3mo
```

### 5. Run a backtest

The backtest is a long-only SMA crossover strategy. It shifts signals by one day to reduce look-ahead bias and can model configurable transaction costs and slippage. It is for historical research only and does not model taxes, market impact, liquidity limits, dividends, or all corporate actions.

```powershell
python app\backtest.py 7203.T --period 5y
```

### 6. Run a paper portfolio

The paper portfolio uses virtual transactions only. The state is saved in `paper_portfolio.json` by default.

Create a virtual position:

```powershell
python app\paper_portfolio.py --cash 1000000 --buy 7203.T 10 3000
```

Refresh the valuation using the latest downloaded price:

```powershell
python app\paper_portfolio.py --quote 7203.T
```

Sell virtually:

```powershell
python app\paper_portfolio.py --sell 7203.T 5 3200
```

### Japanese stock ticker examples

- `7203.T` — Toyota
- `6758.T` — Sony Group
- `8306.T` — Mitsubishi UFJ Financial Group
- `9984.T` — SoftBank Group

## Output

The analysis command prints market data, technical indicators, and an AI comparison with an attention ranking, reasons, and risks. The backtest command prints strategy return, buy-and-hold return, annualized return, maximum drawdown, win rate, and trading-event count. The paper portfolio prints cash, holdings, market value, unrealized P/L, and transaction count.

## Roadmap

1. Connect AI analysis to portfolio allocation proposals
2. More robust backtesting and strategy comparison
3. More asset classes
4. Automated scheduled analysis
