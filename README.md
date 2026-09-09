# Investment AI

AI-assisted investment analysis project.

## Current scope
- Fetch real market data with `yfinance`
- Compare multiple tickers in one run
- Calculate technical indicators such as SMA, EMA, RSI, MACD, and volatility
- Include recent company fundamentals and news context when available
- Run a historical SMA-crossover backtest with configurable trading friction
- Manage a saved paper portfolio with virtual buy/sell transactions
- Generate AI-based paper-portfolio allocation proposals with configurable cash and single-asset limits
- Apply an allocation proposal to the saved paper portfolio through virtual rebalancing
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

Set `OPENAI_MODEL` to a model available to your API account. The code reads the value from `.env` rather than requiring a model name in source code. OpenAI's current model catalog lists GPT-5.6 Luna as a cost-sensitive option available through the Responses API. citeturn720139search0

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

```powershell
python app\paper_portfolio.py --cash 1000000 --buy 7203.T 10 3000
python app\paper_portfolio.py --quote 7203.T
python app\paper_portfolio.py --sell 7203.T 5 3200
```

### 7. Generate an AI allocation proposal

```powershell
python app\allocate.py 7203.T 6758.T 8306.T 9984.T --cash 20 --max-weight 35
```

### 8. Rebalance the paper portfolio from the AI proposal

This command performs only virtual trades. It analyzes the selected tickers, obtains the AI target allocation, then moves the saved paper portfolio toward that target using downloaded prices.

```powershell
python app\rebalance.py 7203.T 6758.T 8306.T 9984.T
```

The saved portfolio is updated locally. No broker connection or real-money order is used.

### Japanese stock ticker examples

- `7203.T` — Toyota
- `6758.T` — Sony Group
- `8306.T` — Mitsubishi UFJ Financial Group
- `9984.T` — SoftBank Group

## Safety and scope

This project is intended for research and paper-trading workflows. It does not place real orders. AI output is not a guarantee of future returns and should be validated with backtests and independent review.

## Output

The analysis command prints market data, technical indicators, and an AI comparison with an attention ranking, reasons, and risks. The backtest command prints strategy return, buy-and-hold return, annualized return, maximum drawdown, win rate, and trading-event count. The paper portfolio prints cash, holdings, market value, unrealized P/L, and transaction count. The allocation command prints proposed weights, reasons, a summary, and key risks. The rebalance command prints target weights, virtual trades, and the resulting portfolio.

## Roadmap

1. Portfolio performance history and charts
2. More robust backtesting with multiple strategies and walk-forward evaluation
3. More asset classes
4. Scheduled analysis
