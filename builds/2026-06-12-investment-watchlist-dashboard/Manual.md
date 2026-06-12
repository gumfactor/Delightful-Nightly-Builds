# Manual — Investment Watchlist Dashboard

## What It Does

Fetches live stock data from Yahoo Finance for a configurable list of tickers and generates a self-contained HTML dashboard you can open in any browser. Shows current price, daily change, 52-week range position, volume, market cap, P/E ratio, and analyst target price.

---

## Requirements

- Python 3.10+
- `yfinance` and `pytest` (install once):

```bash
pip install yfinance pytest
```

---

## Quick Start

```bash
# From this folder:
python3 main.py
# → Writes output/dashboard.html
# → Open that file in your browser
```

---

## All Options

```
python3 main.py                          # Generate HTML dashboard (default)
python3 main.py --text                   # Print text table to terminal instead
python3 main.py --output ~/Desktop/wl.html   # Save HTML to a custom path
python3 main.py --watchlist ~/my-tickers.json  # Use a different watchlist file
```

---

## Configuring Your Watchlist

Edit `watchlist.json` in this folder. It's a JSON array of objects:

```json
[
  { "symbol": "AAPL",  "label": "Apple",  "notes": "core holding" },
  { "symbol": "NVDA",  "label": "NVIDIA", "notes": "AI infrastructure" }
]
```

| Field | Required | Description |
|-------|----------|-------------|
| `symbol` | Yes | Yahoo Finance ticker symbol (e.g. `AAPL`, `BRK-B`, `TSM`) |
| `label` | No | Short display name shown under the symbol |
| `notes` | No | Brief annotation shown as a tooltip or sub-label |

---

## Dashboard Columns

| Column | What It Shows |
|--------|---------------|
| Symbol | Ticker + optional label |
| Name | Company long name from Yahoo Finance |
| Price | Current market price |
| Day Change | Daily change in % and $ vs previous close |
| 52-Week Range | Progress bar showing where price sits in the 52-week range |
| Volume | Today's traded volume |
| Mkt Cap | Market capitalisation |
| P/E | Trailing twelve-month price-to-earnings ratio |
| Target | Analyst mean price target |

Missing or unavailable fields display as **N/A** — the dashboard never crashes on incomplete data.

---

## Dark / Light Mode

The HTML dashboard uses `prefers-color-scheme` CSS media query. It automatically displays in dark mode on systems with dark mode enabled, and light mode otherwise.

---

## Running Tests

```bash
# From this folder:
python -m pytest tests/ -v
```

All 35 tests run in under 1 second (no network calls — processor and renderer functions are tested with synthetic data).

---

## Troubleshooting

**"Warning: could not fetch TICKER"** — The ticker symbol may be invalid, or Yahoo Finance is temporarily rate-limiting requests. Check the symbol spelling and retry after a few minutes.

**All values show N/A** — Your network is blocking `query2.finance.yahoo.com`. This is expected in sandboxed environments. The tool works correctly on a machine with open internet access.

**`ModuleNotFoundError: No module named 'yfinance'`** — Run `pip install yfinance` first.
