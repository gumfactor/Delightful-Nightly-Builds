# PRD — SiliconWatch

> **Build date:** 2026-07-27
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious Project

---

## Goal

A live, comparative dashboard over the major AI-infrastructure and semiconductor companies — GPUs/accelerators, foundry, equipment, memory, and analog/IP — tracking valuation, margin, and price trend side by side, with history that compounds across repeated runs.

## User Story

As a mid-career researcher and indie founder who names "AI infrastructure and semiconductors" as a recurring rabbit-hole topic and quantitative investing as an active interest, I want a single dashboard that compares the companies building the AI compute stack on valuation, profitability, and price momentum, so that I can track the sector I read about most without manually pulling up a dozen ticker pages.

## Scope

### In Scope
- A curated default list of 12 companies across 6 sub-sectors (GPU/Accelerators, Custom Silicon/Networking, Foundry/IDM, Equipment/EDA, Memory, IP/Architecture & Analog), overridable via `--tickers` or a `--config` JSON file
- `sync` command: fetches live data per ticker via `yfinance` (price, market cap, trailing/forward P/E, PEG ratio, profit margin, revenue growth, analyst mean target, 52-week range) and one year of daily closing prices; persists both to local SQLite, deduplicated so re-running `sync` the same day never creates duplicate rows
- `report` command: renders a self-contained dark-mode HTML dashboard from everything stored in SQLite — no live network call required to view a previously-synced report
- `list` command: prints the configured ticker/subsector list
- Dashboard: KPI summary cards (total market cap, avg trailing P/E, avg profit margin, companies tracked), a market-cap comparison bar chart, a profit-margin comparison bar chart, a sortable/searchable company table (price, 1-day %, 1-year %, P/E, PEG, analyst upside), a per-ticker price history line chart selectable via dropdown, and a sector-P/E-over-time trend chart that appears once at least two distinct sync dates exist
- Optional Claude Haiku sector narrative (`--ai`) synthesizing the aggregated sector numbers into a short paragraph, sent only aggregated public-market numbers and public company names — never personal data; a deterministic template narrative is always available as a fallback and is used automatically when no API key is set or the call fails
- Chart.js 4.4.4 via pinned CDN with a graceful plain-table fallback if the CDN is unreachable

### Out of Scope
- Real-time/intraday streaming quotes (yfinance's free data is delayed/end-of-day-oriented; this is a research dashboard, not a trading terminal)
- Options data, insider transactions, or SEC filing text (a possible future integration, not tonight)
- Portfolio/position tracking (this is a sector-comparison tool, not a personal holdings tracker — that space is already covered by the 2026-06-10 Investment Research Platform)
- Multi-currency normalization (ASML and TSM report in EUR/TWD-linked ADR terms via their US-listed ADR tickers; yfinance already returns USD-denominated ADR prices, so no conversion layer is needed)

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None (stdlib `argparse`, `sqlite3`, `json`, `html`, `urllib.request` + third-party `yfinance` for market data)
- **Dependencies:** `yfinance==1.5.2` (pulls in `pandas` transitively, used only inside `data_fetch.py`), `pytest==9.1.1` for testing
- **Runtime requirement:** `python3 src/main.py sync` then `python3 src/main.py report --ai` (or without `--ai`); opens `siliconwatch_report.html` directly in a browser, no server or build step

## Data Structure

Local SQLite database (default path `./siliconwatch.db`, override with `--db`):

```sql
CREATE TABLE snapshots (
    ticker TEXT NOT NULL,
    name TEXT NOT NULL,
    subsector TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,   -- YYYY-MM-DD, UTC
    price REAL,
    market_cap REAL,
    pe_trailing REAL,
    pe_forward REAL,
    peg_ratio REAL,
    profit_margin REAL,           -- fraction, e.g. 0.55
    revenue_growth REAL,          -- fraction
    target_mean_price REAL,
    week52_low REAL,
    week52_high REAL,
    fetched_at TEXT NOT NULL,     -- ISO 8601 UTC timestamp
    PRIMARY KEY (ticker, snapshot_date)
);

CREATE TABLE price_history (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,           -- YYYY-MM-DD
    close REAL NOT NULL,
    PRIMARY KEY (ticker, date)
);
```

`snapshots` accumulates one row per ticker per UTC day a `sync` is run (re-running the same day upserts, not duplicates), building a valuation/margin trend over weeks of use. `price_history` is refreshed on every `sync` with ~1 year of daily closes, deduplicated by `(ticker, date)`, giving a full price trend chart from the very first run.

## Folder Structure

```
builds/2026-07-27-siliconwatch/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py          # default ticker list + JSON config loader
│   ├── data_fetch.py       # yfinance wrapper (injectable ticker factory for testing)
│   ├── storage.py          # SQLite persistence layer
│   ├── metrics.py          # price-delta and sector-aggregate calculations
│   ├── ai_narrative.py     # optional Claude Haiku call + deterministic fallback
│   ├── dashboard.py        # HTML dashboard renderer
│   └── main.py             # argparse CLI entry point
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_data_fetch.py
    ├── test_storage.py
    ├── test_metrics.py
    ├── test_ai_narrative.py
    ├── test_dashboard.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python3 -m pytest tests/ -v` (from the build folder)
- **What will be tested:**
  - Default ticker config is well-formed; JSON config file overrides it; missing/malformed config files fail clearly
  - `data_fetch` maps a mocked `yfinance.Ticker`-like object's `.info` into a snapshot dict, handles missing optional fields as `None`, and never raises on a fetch exception
  - `price_history` fetch converts a mocked history object into a plain list of `(date, close)` tuples
  - SQLite layer: schema creation, snapshot upsert (insert + same-day update, not duplicate), price-history dedup by date, "latest snapshot per ticker" query, snapshot-date listing for trend charts
  - Metrics: 1-day and 1-year price delta calculation, graceful `None` when history is too short, sector aggregates (total market cap, average P/E/margin) correctly ignore missing fields, top-mover/laggard identification
  - AI narrative: successful mocked API call parses the response text; missing API key, network error, and malformed response all fall back to the deterministic template without raising
  - Dashboard: HTML-escapes a script-injection payload in a company name, embeds the pinned Chart.js version string, shows a placeholder instead of a trend chart when only one snapshot date exists, includes every configured ticker in the rendered output
  - CLI: `sync`/`report`/`list` subcommands each exercise their underlying modules correctly with mocked network/API calls; an unrecognized command exits with a usage message
  - No test makes a live network call — every `yfinance`, SQLite-on-disk (uses a temp file per test), and Anthropic API call is mocked or isolated

## Success Criteria

1. All tests pass (zero failures), minimum 15, run via `python3 -m pytest tests/ -v`
2. `sync` followed by `report` produces a valid, self-contained HTML file that opens directly in a browser with no server, showing all 12 default companies grouped by sub-sector
3. Running `sync` twice on the same UTC day does not create duplicate `snapshots` rows (verified by a test and by manual inspection of the resulting table row count)
4. The dashboard degrades gracefully with zero JavaScript errors when the AI narrative is skipped (no `--ai` flag / no API key) and when Chart.js's CDN is unreachable (falls back to a plain table)
5. Every user-influenced string (custom ticker names/subsectors from a `--config` file) is HTML-escaped in the rendered dashboard — verified by a dedicated XSS-payload test

---

## Scope Changes

None — the full scope above was completed as planned.
