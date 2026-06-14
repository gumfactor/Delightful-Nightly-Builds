# PRD — Investment Research Platform

> **Build date:** 2026-06-10 (extended 2026-06-14)
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious Project

---

## Goal

A unified investment research platform: one command generates a self-contained HTML report showing live watchlist metrics alongside your own thesis notes per ticker, including the price when each note was written and the percentage move since.

## User Story

As an academic and solo founder who actively researches investments, I want a single tool that combines a live market snapshot with my running investment thesis journal — so I can open one HTML file in the morning and immediately see both what the market did and how each position has moved since I wrote my thesis.

## Scope

### In Scope
- User-editable `watchlist.json` with ticker symbols and optional display labels
- Fetch per-ticker data via `yfinance`: current price, 1-day % change, 52-week high/low, P/E ratio, market cap, volume, 3-month daily closing prices
- Generate SVG sparklines (90-day price trend) for each ticker — colored green (uptrend), red (downtrend), or gray (flat)
- Generate a self-contained `report.html` with no external dependencies (no CDN, no build step)
- HTML report includes: summary header (date/time, gainers/losers), metrics table with inline sparklines, **Currency column**, **Thesis column** showing the latest note and % move since it was written
- Table columns are **sortable** via an inline `<script>` block (no CDN); handles numeric values with T/B/M/K suffixes and $/%/+ prefixes
- Optional `"group"` field per watchlist entry enables **visual grouping** of tickers under labeled section headers in the table
- **Thesis journal CLI** — `add`, `show`, `list`, `search`, `delete` subcommands via `main.py`
- Thesis notes stored in `theses.json` (local JSON, persists across runs)
- Each note records the live price at time of writing (fetched automatically)
- Graceful handling of unavailable data (N/A fields, fetch errors per ticker)
- `html.escape()` applied to all user-supplied content rendered into HTML (XSS-safe)

### Out of Scope
- Real-time / live data (snapshot on demand)
- Portfolio position tracking (shares held, cost basis, P&L)
- Alert system or price notifications
- Authentication or multi-user support
- Any server or background process
- Options, crypto, or alternative asset data

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None
- **Dependencies:** `yfinance` (data), `pytest` (tests)
- **Runtime:** `python3 main.py` — generates `report.html`; `python3 main.py add TICKER "note"` — adds a thesis note

## Data Structure

**Input: `watchlist.json`**
```json
{
  "tickers": [
    {"symbol": "AAPL", "label": "Apple", "group": "Core Positions"},
    {"symbol": "MSFT", "label": "Microsoft", "group": "Core Positions"},
    {"symbol": "SPY", "label": "S&P 500 ETF", "group": "ETFs"}
  ]
}
```
`group` is optional; omitting it places the ticker in the ungrouped flow.

**Persisted: `theses.json`** (written by `ThesisStore`)
```json
{
  "NVDA": [
    {
      "id": 1,
      "date": "2026-06-14T20:00:00+00:00",
      "note": "AI infrastructure play.",
      "price_at_note": 1100.0
    }
  ]
}
```

**Runtime: `TickerData` dataclass (src/fetcher.py)**
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
    market_cap: int | None
    volume: int | None
    history: list[float]           # 90 daily closes, oldest first
    currency: str
    error: str | None
```

**Output: `report.html`** — single file, all CSS, SVG, and sort JS inline, no external dependencies

## Folder Structure

```
builds/2026-06-10-investment-portfolio-snapshot/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── watchlist.json
├── theses.json          ← created on first `add` command (gitignored)
├── requirements.txt
├── main.py              ← report mode + thesis subcommands
├── src/
│   ├── __init__.py
│   ├── fetcher.py       ← yfinance wrapper + TickerData + formatters
│   ├── charts.py        ← SVG sparkline generation
│   ├── report.py        ← HTML report assembly (includes thesis column)
│   └── theses.py        ← ThesisStore: JSON persistence + CRUD
└── tests/
    ├── test_fetcher.py  ← normalization + formatter unit tests
    ├── test_charts.py   ← sparkline SVG unit tests
    ├── test_report.py   ← HTML output unit tests (incl. thesis column)
    └── test_theses.py   ← ThesisStore CRUD and persistence tests
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What is tested:**
  - SVG sparkline generation: uptrend/downtrend/flat/single-point/empty
  - Formatter functions: market cap suffixes, price display, % change
  - TickerData normalization (no network calls — pure functions)
  - HTML report structure: symbols, timestamp, error rows, thesis column
  - Thesis cell rendering: note text, price-at-note, ±% since, truncation, empty state
  - ThesisStore: add/get/get_latest/list/search/delete, ID sequencing, persistence, copy isolation

## Success Criteria

1. All 103 tests pass (zero failures)
2. `python3 main.py` runs without error and writes `report.html`
3. `report.html` contains all ticker symbols and a generated-at timestamp
4. Tickers with partial/missing data render cleanly with `—` placeholders rather than crashing
5. Thesis notes added via `python3 main.py add TICKER "note"` appear in the next report run
6. All user-supplied content rendered into HTML is escaped (XSS-safe)

---

## Scope Changes

**2026-06-14 — Extended from Portfolio Snapshot to Investment Research Platform**

The original build (2026-06-10, PR #2) delivered the watchlist snapshot and sparklines. A separate thesis journal (PR #6) was built on 2026-06-14 but kept the journal isolated from the report. This extension merges them:

- Added `src/theses.py` — `ThesisStore` with full CRUD + JSON persistence
- Extended `src/report.py` — added Thesis column, `_format_thesis_cell()`, price-at-note + % since calculation
- Rewrote `main.py` — unified entry point routing report mode and five thesis subcommands
- Added `tests/test_theses.py` — 17 new tests
- Added 11 new thesis-related tests to `tests/test_report.py`
- Applied `html.escape()` throughout report generation (XSS hardening from adversarial review)
