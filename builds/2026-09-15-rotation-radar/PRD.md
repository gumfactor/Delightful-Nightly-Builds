# PRD — Rotation Radar

## Goal
Give a self-directed investor a live, visual read on which market sectors are gaining or losing relative strength, using a real Relative Rotation Graph (RRG)-style analysis computed from free Yahoo Finance data — not a per-ticker watchlist, and not another financial-statement report.

## User Story
As someone who does personal quantitative investing research, I want to run one command each morning (or a few times a week) and see, at a glance, which of the 11 S&P sector ETFs are Leading, Weakening, Lagging, or Improving relative to the broad market, with a trail showing how each sector got there over the last two weeks — so I can spot rotation early instead of reading it after the fact in financial media.

## Scope

### In scope
- Fetch daily close prices for a benchmark (default `SPY`) and 11 SPDR sector ETFs (`XLK`, `XLF`, `XLE`, `XLV`, `XLI`, `XLY`, `XLP`, `XLU`, `XLB`, `XLRE`, `XLC`) via `yfinance`, default 9-month lookback.
- Compute, per sector, a full time series of:
  - Relative Strength (RS) vs. the benchmark
  - A smoothed RS-Ratio (cross-sectionally z-scored, centered at 100)
  - An RS-Momentum (rate of change of RS-Ratio, cross-sectionally z-scored, centered at 100)
  - A quadrant classification (Leading / Weakening / Lagging / Improving) at every point
- Render a self-contained dark-mode HTML dashboard with:
  - A quadrant scatter plot showing each sector's latest position plus a trailing "tail" of its last N days (the defining RRG visual)
  - A sortable table of current Ratio/Momentum/quadrant/day-over-day change per sector
  - A "since last run" panel showing which sectors changed quadrant since the previous saved run (via local SQLite history)
  - A CSV export of the full per-sector history
  - An optional AI commentary panel (Claude Haiku) summarizing the current rotation regime in plain English, built strictly from the computed numbers, with a deterministic template fallback when no API key is set
- A CLI (`main.py`) with flags for lookback window, tail length, benchmark ticker, sector list override, AI on/off, and output paths.
- Local SQLite persistence of each run's per-sector snapshot so rotation can be tracked across multiple runs over time.

### Out of scope
- Individual-stock (non-ETF) analysis
- Backtesting or trade signal generation / execution
- Any brokerage integration (IBKR etc.) — this is a market-structure data explorer, not a portfolio tool
- Real-time/intraday data (daily closes only)

## Tech Stack
- Python 3 (stdlib + `yfinance`, `pandas`)
- SQLite (stdlib `sqlite3`) for run history
- Chart.js 4.4.4 (CDN) for the quadrant scatter/tail plot and table sort UI (vanilla JS, no bundler)
- Anthropic API via `urllib.request` (stdlib, optional, `ANTHROPIC_API_KEY` from environment) for AI commentary — no SDK dependency
- pytest for tests, with all `yfinance` and Anthropic calls mocked

## Data Structure
- `PriceSeries`: `dict[str, pandas.Series]` — ticker → date-indexed close prices
- `SectorSnapshot` (dataclass): `ticker, date, rs_ratio, rs_momentum, quadrant`
- `RunRecord` (SQLite table `runs`): `id, run_timestamp` — one row per CLI invocation
- `SnapshotRecord` (SQLite table `snapshots`): `run_id, ticker, rs_ratio, rs_momentum, quadrant` — one row per sector per run
- Dashboard embeds a single escaped `<script type="application/json">` block containing: per-sector tail arrays `[{date, ratio, momentum}, ...]`, current snapshot table rows, quadrant-transition deltas, and AI commentary text.

## Folder Structure
```
builds/2026-09-15-rotation-radar/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── data.py         — yfinance fetch wrapper
│   ├── analytics.py    — RS/RS-Ratio/RS-Momentum/quadrant/tail math (pure functions)
│   ├── storage.py      — SQLite persistence + history/delta queries
│   ├── ai.py            — optional Claude Haiku commentary + deterministic fallback
│   ├── report.py        — HTML dashboard generation (escaping, CSV export)
│   └── cli.py            — argparse CLI entry point wiring the above together
├── tests/
│   ├── test_analytics.py
│   ├── test_storage.py
│   ├── test_ai.py
│   ├── test_report.py
│   └── test_cli.py
└── sample_output/       — a rendered example (synthetic data) since this build
    ├── rotation_radar_demo.html   container has no route to Yahoo Finance
    └── rotation_radar_demo_history.csv
```

## Algorithm (exact formulas, hand-verified before tests were written)

For each sector ticker *i* and benchmark *b*, at trading day *t*:

1. `RS_i(t) = 100 * close_i(t) / close_b(t)`
2. `SMA_RS_i(t) = mean(RS_i(t-w+1 .. t))` where `w` = `ratio_window` (default 10)
3. At each *t*, across all sectors with a valid `SMA_RS(t)`: compute the cross-sectional mean and sample standard deviation (`ddof=1`). If fewer than 2 sectors have valid data, or the standard deviation is exactly 0, every z-score at that *t* is defined as 0.0 (documented degenerate-case guard, not silently propagated NaN).
4. `RS-Ratio_i(t) = 100 + zscore(SMA_RS_i(t))`
5. `raw_momentum_i(t) = RS-Ratio_i(t) - RS-Ratio_i(t - m)` where `m` = `momentum_window` (default 10)
6. `RS-Momentum_i(t) = 100 + zscore(raw_momentum_i(t))` (same cross-sectional z-score rule as step 3/4)
7. Quadrant at *t*: `Ratio>=100 & Momentum>=100` → **Leading**; `Ratio>=100 & Momentum<100` → **Weakening**; `Ratio<100 & Momentum<100` → **Lagging**; `Ratio<100 & Momentum>=100` → **Improving**. The `>=100` boundary is a fixed, documented convention (a sector sitting exactly at 100 on both axes is Leading).
8. The "tail" is the last `tail_length` (default 10) valid `(Ratio, Momentum)` points per sector, in date order, for plotting the trajectory.

This is a standard, publicly documented cross-sectional-z-score approximation of Julius de Kempenaer's RRG methodology (the exact proprietary StockCharts/Bloomberg formula is not public); it is internally consistent and was hand-verified against a small synthetic fixture (3 sectors, 25 days) before any test assertion was written — see BUILD_LOG.md.

## Testing Strategy
- All `yfinance` calls are wrapped in `src/data.py` and mocked in every test — no live network calls in the test suite.
- `test_analytics.py`: RS calculation, SMA, cross-sectional z-score (including the zero-std and single-sector degenerate cases), RS-Ratio/RS-Momentum against a hand-computed fixture, quadrant classification at and around the 100 boundary, tail extraction length and ordering, insufficient-history error handling.
- `test_storage.py`: SQLite schema creation, snapshot insertion, run history retrieval, quadrant-transition delta computation between two runs (including the first-ever-run case with no prior history).
- `test_ai.py`: deterministic fallback with no `ANTHROPIC_API_KEY`, mocked successful Anthropic call, mocked malformed/error response falling back to the deterministic template, and a check that no network call is attempted when no key is set.
- `test_report.py`: HTML output contains no unescaped user/API-derived strings (XSS guard via an injected hostile ticker-like string in a fixture), CSV export correctness, presence of all required dashboard sections.
- `test_cli.py`: argument parsing and defaults, end-to-end run against fully mocked data/AI/storage producing a valid HTML file and DB row.
- Run with `python -m pytest tests/ -v`. Minimum 15 tests, all passing before commit.

## Success Criteria
1. Given a mocked 9-month price history for the benchmark and 11 sectors, the CLI produces a valid, escaped, self-contained HTML dashboard file and a populated SQLite database — verified by `test_cli.py`.
2. RS-Ratio, RS-Momentum, and quadrant classification match hand-computed values on a fixed fixture to floating-point tolerance — verified by `test_analytics.py`.
3. Running the CLI twice against different mocked snapshots correctly reports which sectors changed quadrant between runs, and the first run correctly reports no prior history to compare against — verified by `test_storage.py`.
4. The AI commentary module never makes a network call when `ANTHROPIC_API_KEY` is unset, and falls back to a deterministic, factually-grounded template in that case and on any API error — verified by `test_ai.py`.
5. The rendered dashboard contains zero unescaped injection vectors even when fed a hostile ticker-shaped string, and opens directly via `file://` with a working quadrant plot, sortable table, and CSV export — verified by `test_report.py` and a manual headless-browser check.
