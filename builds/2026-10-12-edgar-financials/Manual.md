# Manual — EDGAR Financials

## Setup
Python 3.11+. No third-party packages. SEC requires a User-Agent that identifies you:

```bash
export EDGAR_USER_AGENT="Your Name you@example.com"      # Windows PowerShell: $env:EDGAR_USER_AGENT="Your Name you@example.com"
```

## Run
From this folder:

```bash
PYTHONPATH=src python -m edgar_fin AAPL MSFT NVDA --years 5 --out output
```

(PowerShell: `$env:PYTHONPATH="src"; python -m edgar_fin AAPL MSFT`.)

Options: `--years N` (1–15), `--out DIR`, `--refresh` (ignore cache), `--ai` (add Claude commentary; needs `ANTHROPIC_API_KEY`, optional `EDGAR_AI_MODEL`), `--demo` (synthetic data, no network, no env vars).

Exit codes: 0 ok, 1 nothing to report, 2 usage/config error, 3 report written but some tickers were skipped.

## Outputs (in `--out`)
- `report.html` — open in a browser. Pick a metric to chart all companies; click a summary column header to sort; per-company statements below. Works on a phone; follows system dark/light mode. Chart.js loads from a pinned CDN, so the chart needs internet (tables do not).
- `financials_long.csv` — one row per ticker/year/metric (good for pandas or R).
- `<TICKER>_financials.csv` — metrics by year.
- `summary.csv` — latest year plus revenue / net income / EPS CAGR per company.
- `.cache/` — raw SEC JSON. Re-runs are offline until `--refresh`.

## How numbers are normalised
- Annual 10-K / 20-F / 40-F facts only, 340–380 day durations for flow items.
- If a period was restated, the latest filing wins.
- Each metric tries several XBRL tags per year, in priority order.
- Fiscal year is the year of the period end; January/February year-ends belong to the prior year.
- Free cash flow = operating cash flow − capex. Growth is blank when the prior value is ≤ 0. ROE and debt/equity are blank when equity ≤ 0.
- Gaps show as "–". Check the filing if a gap looks wrong; the company may use a custom tag.

## Tests
```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
(also runs under `pytest tests/` if installed). All SEC and Anthropic calls are mocked.
