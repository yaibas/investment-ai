# Investment AI

AI-assisted investment analysis project.

## Current scope
- Fetch real market data with `yfinance`
- Compare multiple tickers in one run
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

You can optionally choose the model with:

```env
OPENAI_MODEL=gpt-5.6
```

### 4. Run a multi-ticker analysis

```powershell
python app\run_analysis.py 7203.T 6758.T 9984.T 8306.T
```

Change the tickers to the companies or ETFs you want to analyze. You can also change the history window:

```powershell
python app\run_analysis.py 7203.T 6758.T --period 3mo
```

### Japanese stock ticker examples

- `7203.T` — Toyota
- `6758.T` — Sony Group
- `8306.T` — Mitsubishi UFJ Financial Group
- `9984.T` — SoftBank Group

## Output

The program prints the latest market data for each ticker and then an AI comparison with an attention ranking, reasons, and risks.

## Roadmap

1. Technical indicators
2. News and earnings data
3. Backtesting
4. Paper portfolio
5. More asset classes
