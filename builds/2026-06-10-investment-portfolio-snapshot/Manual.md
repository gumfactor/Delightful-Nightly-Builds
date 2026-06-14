# Manual — Investment Research Platform

> **Version:** 2.0 (updated 2026-06-14)
> **Complexity:** Ambitious Project

---

## What This Is

A unified investment research platform. One command fetches live market data for your watchlist and generates a self-contained HTML report — prices, key metrics, 3-month sparklines, and your own thesis notes per ticker including the price when each note was written and the % move since. A built-in thesis journal CLI lets you add and review investment notes that automatically appear in every subsequent report.

---

## Quick Start

1. Edit `watchlist.json` with the tickers you want to track (Yahoo Finance symbols; append `.TO` for TSX-listed stocks)
2. Optionally add some thesis notes: `python3 main.py add NVDA "AI infrastructure play."`
3. From the build folder: `python3 main.py`
4. Open `report.html` in your browser — or use `python3 main.py --open` to open it automatically

---

## How to Use It

### Editing Your Watchlist

Edit `watchlist.json` to control which stocks appear:

```json
{
  "tickers": [
    {"symbol": "AAPL", "label": "Apple", "group": "Core Positions"},
    {"symbol": "BRK-B", "label": "Berkshire B", "group": "Core Positions"},
    {"symbol": "SPY", "label": "S&P 500 ETF", "group": "ETFs"},
    {"symbol": "XIU.TO", "label": "iShares S&P/TSX 60", "group": "ETFs"}
  ]
}
```

- `symbol` — Yahoo Finance ticker. US stocks: plain symbol (e.g. `MSFT`). TSX: append `.TO` (e.g. `VFV.TO`).
- `label` — Display name in the report. Optional; defaults to the symbol if omitted.
- `group` — Optional section label. Tickers that share a group value are rendered together under a group header row. Tickers without a `group` field appear ungrouped at the top or bottom depending on their position in the list.

### Generating the Report

From the build folder root:

```bash
# Generate report
python3 main.py

# Generate and open in browser immediately
python3 main.py --open

# Custom paths
python3 main.py --watchlist ~/my-watchlist.json --output ~/Desktop/snapshot.html --open
```

Progress is printed to the terminal as each ticker is fetched.

### Managing Thesis Notes

Notes are stored in `theses.json` in the build folder and automatically appear in the Thesis column of every report.

```bash
# Add a note (fetches and records today's live price automatically)
python3 main.py add NVDA "AI infrastructure play — datacenter capex cycle still early."

# View all notes for a ticker with live price and % change since each note
python3 main.py show NVDA

# List all tickers that have notes
python3 main.py list

# Search notes by keyword (case-insensitive)
python3 main.py search "infrastructure"

# Delete a specific note by ID
python3 main.py delete NVDA 1
```

Notes that have a recorded price show the % move since the note was written — in `show` output and in the report's Thesis column.

### Reading the Report

The HTML report opens in any browser — double-click `report.html`, or use `--open` to launch it automatically. No internet connection required once the file is generated.

**Summary row:** Shows total tickers, gainers, and losers for a quick glance.

**Table columns:**
| Column | What it shows |
|--------|---------------|
| Symbol | Ticker symbol and display name |
| Price | Current/last price in local currency |
| 1D Change | Percentage change since previous close; green=up, red=down |
| 52W Range | 52-week low — 52-week high |
| P/E | Trailing P/E ratio (blank for ETFs and non-profitable companies) |
| Mkt Cap | Market capitalization with T/B/M suffix |
| Volume | Daily volume with M/K suffix |
| Currency | Trading currency (USD, CAD, etc.) — useful for mixed US/TSX watchlists |
| 3M Trend | 90-day SVG sparkline; green=uptrend from 90d ago, red=downtrend, gray=flat |
| Thesis | Latest note text, price at time of writing, and % move since (green=up, red=down) |

Missing fields display as `—` — the tool never crashes on missing data. If no thesis note exists for a ticker, the Thesis column shows `—`.

**Sorting:** Click any column header with an arrow cursor to sort the table by that column. Click again to reverse. Group headers are hidden while a sort is active (they reappear on page reload). The 52W Range and 3M Trend columns are not sortable.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--watchlist` | `watchlist.json` in build folder | Path to a valid watchlist JSON file |
| `--output` | `report.html` in build folder | Path where the HTML report is written |
| `--open` | off | Open the report in the default browser after generating |

---

## Running Tests

From the build folder:

```bash
python -m pytest tests/ -v
```

All tests run without network access — Yahoo Finance is mocked so the test suite is fast and portable.

**Expected output:** 103 tests, 0 failures.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `HTTP Error 403: Host not in allowlist` | Network policy blocks Yahoo Finance (e.g. in sandboxed CI) | Run from your local machine instead of a restricted environment |
| Ticker shows "Fetch error" in the report | Yahoo Finance couldn't fetch that symbol | Check the ticker symbol is valid on finance.yahoo.com; some symbols differ between markets |
| `watchlist.json not found` | Running from the wrong directory | Run `python3 main.py` from inside the `builds/2026-06-10-investment-portfolio-snapshot/` folder |
| P/E shows `—` for a stock | yfinance returned N/A for trailingPE (common for companies with negative earnings) | Expected behavior; no action needed |
| TSX ticker prices look wrong | Currency mismatch — TSX tickers return CAD | Correct; the `$` symbol is used for both USD and CAD; the 52W range will also be in CAD |

---

## Known Limitations

- Prices reflect the last market close or 15–20 minute delayed quote (Yahoo Finance policy) — not real-time
- The report overwrites `report.html` each run; no history is kept (see FutureFeatures.md #6 for a snapshot archive)
- In sandboxed or network-restricted environments (e.g. GitHub Actions), the Yahoo Finance API is blocked; the tool generates an error-state report rather than crashing
- Large watchlists (20+ tickers) may be rate-limited by Yahoo Finance; fetching is sequential with no delay between requests
