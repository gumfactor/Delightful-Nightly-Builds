# /portfolio-check

Generates a fresh investment portfolio snapshot from Yahoo Finance and opens it in your browser.

## Steps

1. Run from the repository root:
   ```bash
   python3 builds/2026-06-10-investment-portfolio-snapshot/main.py --open
   ```

2. Wait for all tickers to fetch (10–20 seconds depending on watchlist size).

3. The report opens automatically in your default browser. Confirm: "Portfolio snapshot updated — report.html opened."

## Requirements
- Python 3 with `yfinance` installed: `pip install yfinance`
- Active internet connection

## Customisation
Edit `builds/2026-06-10-investment-portfolio-snapshot/watchlist.json` to change which tickers appear.
