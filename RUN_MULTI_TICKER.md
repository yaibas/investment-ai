# Run multi-ticker analysis

Install dependencies:

```bash
pip install -r requirements-market.txt
```

Set `OPENAI_API_KEY` in `.env`.

Run from the `app` directory or configure your Python path so `analysis` and `data` are importable:

```bash
python -m app.compare
```

The default tickers are:
- 7203.T — Toyota
- 6758.T — Sony Group
- 9984.T — SoftBank Group
- 8306.T — Mitsubishi UFJ Financial Group
