# PRD — Investment Watchlist Dashboard

> **Build date:** 2026-06-12
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Solid Feature
> **Day of week:** Friday → Solid Feature

---

## Goal

Fetch live stock data for a configurable watchlist from Yahoo Finance and render a self-contained HTML dashboard showing current prices, daily changes, 52-week ranges, and key fundamentals.

## User Story

As an academic and solo founder who actively tracks stocks and market movements for personal investing research, I want a single command that pulls fresh Yahoo Finance data for my watchlist and renders it as a polished HTML file I can open immediately in the browser, so that I can scan key metrics at a glance without context-switching into a brokerage or financial site.

## Scope

### In Scope
- Configurable watchlist in `watchlist.json` (list of ticker objects with symbol + optional label/notes)
- Fetch per-ticker data via `yfinance`: current price, previous close, daily change ($, %), volume, 52-week low/high, market cap, trailing P/E, analyst mean target
- Compute 52-week range position (% of way between low and high)
- Self-contained HTML output with embedded CSS and no external CDN dependencies
- Summary header: number of tickers, gainers, losers, last-updated timestamp
- Per-ticker rows: symbol, name, price, daily change (color-coded), volume, 52-week progress bar, market cap, P/E
- Color coding: positive change = green, negative = red, flat = neutral
- Dark/light mode respecting `prefers-color-scheme`
- Optional text/terminal output mode (`--text` flag)
- Save HTML to `output/dashboard.html` by default; `--output` flag overrides path
- Graceful handling of missing/null fields (show "N/A" rather than crashing)

### Out of Scope
- Portfolio position tracking (shares held, cost basis, gains)
- Historical price charts or sparklines
- Push notifications or auto-refresh
- Real-time price streaming
- Options or crypto tickers
- Authentication or multi-user support
- Any data persistence beyond the generated HTML file

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None
- **Dependencies:** `yfinance>=0.2`, `pytest>=7.0` (see requirements.txt)
- **Runtime requirement:** `python3 main.py` — outputs `output/dashboard.html`, then prints path to stdout

## Data Structure

### watchlist.json
```json
[
  { "symbol": "AAPL", "label": "Apple", "notes": "" },
  { "symbol": "NVDA", "label": "NVIDIA", "notes": "AI infrastructure" }
]
```

### Processed ticker record (internal dict passed between modules)
```python
{
    "symbol": "AAPL",
    "label": "Apple",         # from watchlist.json label field
    "name": "Apple Inc.",     # from yfinance longName
    "price": 185.50,          # currentPrice or regularMarketPrice
    "prev_close": 182.30,
    "change_abs": 3.20,       # price - prev_close
    "change_pct": 1.76,       # (change_abs / prev_close) * 100
    "volume": 52_300_000,
    "week52_low": 164.08,
    "week52_high": 199.62,
    "week52_position": 60.3,  # % of way from low to high, 0-100
    "market_cap": 2_850_000_000_000,
    "pe_ratio": 28.4,
    "analyst_target": 210.00,
    "notes": ""
}
```

Missing/unavailable fields are `None`; all display functions handle `None` → "N/A".

## Folder Structure

```
builds/2026-06-12-investment-watchlist-dashboard/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── main.py                    ← CLI entry point; argparse, orchestrates fetch → process → render
├── watchlist.json             ← default sample watchlist (7 public tickers)
├── requirements.txt           ← yfinance>=0.2, pytest>=7.0
├── src/
│   ├── __init__.py
│   ├── fetcher.py             ← yfinance wrapper; returns raw info dict per ticker
│   ├── processor.py           ← pure functions: extract fields, calculate change, format values
│   └── renderer.py            ← pure functions: build HTML string or text table
├── tests/
│   ├── test_processor.py      ← 12 unit tests for all processor functions
│   └── test_renderer.py       ← 3 unit tests for renderer output
└── output/                    ← generated dashboard.html lives here (not committed)
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_processor.py`, `tests/test_renderer.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - `format_price`: normal float, None input
  - `format_change_pct`: positive, negative, zero
  - `format_market_cap`: billions, trillions, None
  - `calc_52week_position`: midpoint, at-low edge case, None inputs
  - `process_ticker_data`: complete info dict extracts all fields correctly
  - `process_ticker_data`: missing fields in info dict → None, no KeyError
  - `render_html`: output string contains all ticker symbols from input
  - `render_html`: positive-change ticker has "positive" CSS class in output
  - `render_html`: negative-change ticker has "negative" CSS class in output

## Success Criteria

1. All tests pass (zero failures) with `python -m pytest tests/ -v`
2. `python3 main.py` produces `output/dashboard.html` that opens in a browser and shows all 7 sample watchlist tickers with prices, daily changes, and 52-week range bars
3. A ticker with a missing field (e.g., no P/E ratio) displays "N/A" rather than crashing
4. The generated HTML file is self-contained — no external CDN links, no JavaScript errors in browser console
5. `python3 main.py --text` prints a readable table to stdout without writing any file

---

## Scope Changes

<!-- Leave blank unless scope changed mid-build. -->
