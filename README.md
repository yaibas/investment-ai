# Investment AI

AI-assisted investment analysis project.

## Current scope
- Fetch real market data with `yfinance`
- Compare multiple tickers in one run
- Calculate technical indicators such as SMA, EMA, RSI, MACD, and volatility
- Include recent company fundamentals and news context when available
- Run a historical SMA-crossover backtest
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

The current backtest is a simple long-only SMA crossover strategy. It is for historical research only; transaction costs, taxes, slippage, and other real-world effects are not modeled yet.

```powershell
python app\backtest.py 7203.T --period 5y
```

You can change the fast and slow moving-average windows:

```powershell
python app\backtest.py 7203.T --period 10y --fast 20 --slow 50
```

### Japanese stock ticker examples

- `7203.T` — Toyota
- `6758.T` — Sony Group
- `8306.T` — Mitsubishi UFJ Financial Group
- `9984.T` — SoftBank Group

## Output

The analysis command prints market data, technical indicators, and an AI comparison with an attention ranking, reasons, and risks. The backtest command prints strategy return, buy-and-hold return, annualized return, maximum drawdown, and win rate.

## Roadmap

1. Improve backtesting with transaction costs and more strategies
2. Paper portfolio
3. More asset classes
4. Automated scheduled analysis
