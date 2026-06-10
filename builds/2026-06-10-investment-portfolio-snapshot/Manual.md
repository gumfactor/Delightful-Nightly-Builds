# Manual — Investment Portfolio Snapshot

> **Version:** 1.0 (built 2026-06-10)
> **Complexity:** Ambitious Project

---

## What This Is

A Python script that fetches current prices, key metrics, and 3-month price trends for a configurable stock watchlist and generates a self-contained HTML report you can open in any browser. Run it once to get a snapshot; run it each morning as part of your routine. No server, no login, no browser extension — one command, one file.

---

## Quick Start

1. Edit `watchlist.json` with the tickers you want to track (Yahoo Finance symbols; append `.TO` for TSX-listed stocks)
2. From the build folder: `python3 main.py`
3. Open `report.html` in your browser

---

## How to Use It

### Editing Your Watchlist

Edit `watchlist.json` to control which stocks appear:

```json
{
  "tickers": [
    {"symbol": "AAPL", "label": "Apple"},
    {"symbol": "BRK-B", "label": "Berkshire B"},
    {"symbol": "XIU.TO", "label": "iShares S&P/TSX 60"}
  ]
}
```

- `symbol` — Yahoo Finance ticker. US stocks: plain symbol (e.g. `MSFT`). TSX: append `.TO` (e.g. `VFV.TO`).
- `label` — Display name in the report. Optional; defaults to the symbol if omitted.

### Running the Tool

From the build folder root:

```bash
python3 main.py
```

Progress is printed to the terminal as each ticker is fetched. The report is written to `report.html` in the same folder.

**Custom paths:**
```bash
python3 main.py --watchlist ~/my-watchlist.json --output ~/Desktop/snapshot.html
```

### Reading the Report

The HTML report opens in any browser — double-click `report.html` or run `open report.html` (macOS) / `start report.html` (Windows). No internet connection required once the file is generated.

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
| 3M Trend | 90-day SVG sparkline; green=uptrend from 90d ago, red=downtrend, gray=flat |

Missing fields (P/E for ETFs, etc.) display as `—` — the tool never crashes on missing data.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--watchlist` | `watchlist.json` in build folder | Path to a valid watchlist JSON file |
| `--output` | `report.html` in build folder | Path where the HTML report is written |

---

## Running Tests

From the build folder:

```bash
python -m pytest tests/ -v
```

All tests run without network access — Yahoo Finance is mocked so the test suite is fast and portable.

**Expected output:** 65 tests, 0 failures.

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
