# PRD — Investment Portfolio Snapshot

> **Build date:** 2026-06-10
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday → Ambitious Project

---

## Goal

Generate a self-contained HTML snapshot of a configurable stock watchlist — prices, key metrics, and 3-month sparklines — from a single `python3 main.py` command.

## User Story

As an academic and solo founder who actively researches investments and needs a fast daily pulse on a personal watchlist, I want to run one command and get a clean, information-dense HTML report showing current prices, 1-day changes, 52-week ranges, P/E ratios, and 3-month price trends, so that I can orient myself in under 30 seconds without opening a brokerage platform.

## Scope

### In Scope
- User-editable `watchlist.json` with ticker symbols and optional display labels
- Fetch per-ticker data via `yfinance`: current price, 1-day % change, 52-week high/low, P/E ratio, market cap, volume, 3-month daily closing prices
- Generate SVG sparklines (90-day price trend) for each ticker — colored green (uptrend), red (downtrend), or gray (flat)
- Generate a self-contained `report.html` with no external dependencies (no CDN, no build step)
- HTML report includes: summary header (date/time, count of gainers vs. losers), sortable-by-eye metrics table, inline sparklines
- Graceful handling of unavailable data (N/A fields, fetch errors per ticker)
- Output file written to the build folder root as `report.html`
- Formatters for market cap (T/B/M suffixes), price, and % change

### Out of Scope
- Real-time / live data (this is a snapshot — run it when you want it)
- Portfolio position tracking (shares held, cost basis, total P&L)
- Alert system or price notifications
- Persistence between runs (each run overwrites `report.html`)
- Authentication or multi-user support
- Any server or background process
- Options, crypto, or alternative asset data

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None
- **Dependencies:** `yfinance` (data), `pytest` (tests)
- **Runtime requirement:** `python3 main.py` — generates `report.html` in the build folder; open in any browser

## Data Structure

**Input: `watchlist.json`**
```json
{
  "tickers": [
    {"symbol": "AAPL", "label": "Apple"},
    {"symbol": "MSFT", "label": "Microsoft"}
  ]
}
```
- `symbol`: Yahoo Finance ticker string (e.g. `BRK-B`, `VFV.TO`)
- `label`: Display name; falls back to `symbol` if omitted

**Runtime data: `TickerData` dataclass (src/fetcher.py)**
```python
@dataclass
class TickerData:
    symbol: str
    name: str
    price: float | None
    change_pct: float | None       # 1-day % change
    week52_high: float | None
    week52_low: float | None
    pe_ratio: float | None
    market_cap: int | None         # raw integer
    volume: int | None
    history: list[float]           # 90 daily closes, oldest first
    currency: str                  # "USD" or "CAD" etc.
    error: str | None              # non-None if fetch failed
```

**Output: `report.html`**
- Single file, all CSS and SVG inline
- No JavaScript dependencies; static HTML

## Folder Structure

```
builds/2026-06-10-investment-portfolio-snapshot/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── watchlist.json
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── fetcher.py          ← yfinance wrapper + TickerData + formatters
│   ├── charts.py           ← SVG sparkline generation
│   └── report.py           ← HTML report assembly
└── tests/
    ├── test_fetcher.py     ← normalization + formatter unit tests
    ├── test_charts.py      ← sparkline SVG unit tests
    └── test_report.py      ← HTML output unit tests
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - SVG sparkline generation: uptrend/downtrend/flat/single-point/empty data
  - Formatter functions: market cap suffixes, price display, % change sign/sign coloring
  - TickerData normalization from raw yfinance dicts (mocked — no network calls in tests)
  - HTML report structure: all symbols present, timestamp present, error tickers handled
  - Edge cases: empty watchlist, all-None fields, zero-price ticker

## Success Criteria

1. All tests pass (zero failures)
2. `python3 main.py` runs without error and writes `report.html` — verified by checking the file exists and has non-trivial content (>1000 bytes)
3. `report.html` contains all ticker symbols from `watchlist.json` and a generated-at timestamp
4. Tickers with partial/missing data (e.g. no P/E for an ETF) render cleanly with `—` placeholders rather than crashing
5. The HTML file opens correctly in a browser with no broken layout — table and sparklines visible

---

## Scope Changes

<!-- Leave blank; updated if scope changes during build. -->
