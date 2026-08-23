# PRD — Trading Book

## Goal

Give the user a real-time, self-hosted dashboard of their actual Interactive Brokers account — net liquidation value, cash, P&L, and position-level detail — built from a live local Trader Workstation / IB Gateway connection, with a persistent daily history so trend actually accumulates over time.

## User Story

As a solo investor who runs Interactive Brokers daily and is building a personal quantitative-investing practice, I want to run one command each day that pulls my real account snapshot from my already-running TWS/IB Gateway session, and open a dashboard that shows my net worth trend, today's P&L, and an allocation breakdown — without opening the IBKR desktop app or a browser-based portal, and without typing anything by hand.

## Scope

### In scope
- A `sync` command that connects to a locally running TWS or IB Gateway instance (via `ib_insync`), pulls account summary (net liquidation, total cash, gross position value, unrealized P&L, realized P&L, buying power) and every open position (symbol, security type, currency, exchange, quantity, average cost, market price, market value, unrealized P&L), and persists one snapshot per UTC calendar day to a local SQLite database (same-day re-syncs update in place rather than duplicating, so multi-day history stays clean).
- A `show` command that prints the latest snapshot as a terminal summary.
- A `history` command that prints the day-over-day net-liquidation and unrealized-P&L trend as a terminal table.
- A `render` command that builds a single self-contained, dark-mode HTML dashboard from everything in the local database: hero stats (net liquidation, cash, unrealized P&L, realized P&L, each red/green colored), a net-liquidation-over-time line chart (Chart.js, with a graceful plain-table fallback if the CDN is unreachable), an asset-class (security type) allocation donut chart, and a sortable/searchable positions table for the latest snapshot.
- An optional Claude Haiku "portfolio note" on `render --ai-briefing`: one short paragraph of plain-English context, built from an aggregate-only prompt (day-over-day % change, asset-class allocation percentages, top 3 movers by % change) — never a dollar figure, account ID, or account number. Falls back to a deterministic template with zero network calls when `ANTHROPIC_API_KEY` is unset.
- Full test coverage of every module using a fake `ib_insync` module injected via `sys.modules`, so tests never require the real package to be installed and never touch a real network socket.

### Out of scope
- Placing, modifying, or cancelling any order — this build is strictly read-only against the IBKR account.
- Historical price charting per position (would require a separate market-data subscription/call pattern beyond account/position snapshots).
- Multi-account consolidation (IBKR Financial Advisor / multi-account setups) — single account only.
- Sector/industry enrichment via a second data source — the asset-class (security type) breakdown IBKR already returns is sufficient for a meaningful allocation view without adding a second live-data dependency.
- Tax-lot-level detail (only the aggregate per-symbol position IBKR's `positions()` call returns).

## Tech Stack

- Python 3, stdlib only for everything except the one runtime-only third-party package: `ib_insync` (pinned in `requirements.txt`), imported lazily inside the connection function so the module itself has zero import-time dependency on it — `import src.ibkr_client` succeeds with or without `ib_insync` installed, matching this build container's constraint (package installation is denied here; `ib_insync` is written for the user's own machine, where they already run IBKR software daily).
- SQLite (stdlib `sqlite3`) for local snapshot/position persistence.
- Chart.js 4.4.4 via CDN for the two dashboard charts, with a verified DOM-table fallback if the CDN is unreachable.
- Anthropic API via `urllib` (no `anthropic` package dependency), optional, runtime-only.
- pytest for the test suite.

## Data Structure

SQLite database at `trading_book.db` (created in the build folder, alongside `main.py`):

```sql
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL UNIQUE,   -- UTC date, YYYY-MM-DD; one row per day
    synced_at TEXT NOT NULL,              -- UTC ISO8601 timestamp of this sync
    account_id TEXT NOT NULL,
    net_liquidation REAL NOT NULL,
    total_cash REAL NOT NULL,
    gross_position_value REAL NOT NULL,
    unrealized_pnl REAL NOT NULL,
    realized_pnl REAL NOT NULL,
    buying_power REAL NOT NULL
);

CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    sec_type TEXT NOT NULL,       -- STK, OPT, FUT, CASH, BOND, FUND, CFD, ...
    currency TEXT NOT NULL,
    exchange TEXT,
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL,
    market_price REAL NOT NULL,
    market_value REAL NOT NULL,
    unrealized_pnl REAL NOT NULL
);
```

A `sync` on a day that already has a snapshot row deletes and re-inserts that day's `positions` rows (cascade) and updates the `snapshots` row in place — same-day re-syncs never duplicate, matching the snapshot pattern used across this catalog's other daily-tracking builds.

## Folder Structure

```
builds/2026-08-23-trading-book/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py                    # CLI entry point: sync / show / history / render
├── src/
│   ├── __init__.py
│   ├── ibkr_client.py         # lazy ib_insync import, fetch_snapshot(), IBKRConnectionError
│   ├── storage.py             # SQLite init + upsert-by-day + query helpers
│   ├── ai_briefing.py         # optional Claude Haiku call via urllib, deterministic fallback
│   └── report.py              # renders the self-contained dark-mode HTML dashboard
└── tests/
    ├── __init__.py
    ├── test_ibkr_client.py
    ├── test_storage.py
    ├── test_ai_briefing.py
    ├── test_report.py
    └── test_main.py
```

## Testing Strategy

All tests run via `python -m pytest tests/ -v` from the build folder, with zero real network calls and zero dependency on `ib_insync` actually being installed.

- **test_ibkr_client.py** — injects a fake `ib_insync` module (fake `IB` class with scripted `connect`/`accountSummary`/`portfolio`/`disconnect` methods) into `sys.modules` before calling `fetch_snapshot()`. Covers: a successful fetch returns the expected shaped dict; a connection refusal raises `IBKRConnectionError` with a message pointing at TWS/Gateway setup; an empty-positions account returns an empty list rather than erroring; `disconnect()` is always called, including when an exception is raised mid-fetch (verified via a call-count assertion, not by trusting a happy-path mock).
- **test_storage.py** — real (temp-file) SQLite database per test via a pytest fixture. Covers: `init_db` creates both tables; a `sync` on a new day inserts a new snapshot row; a second `sync` on the *same* UTC day updates that row in place (row count stays 1) and fully replaces its positions rather than appending; `get_latest_snapshot` returns the most recent day; `get_history(days=N)` returns at most N rows in ascending date order; `get_history` on an empty database returns `[]` without raising.
- **test_ai_briefing.py** — patches `urllib.request.urlopen`. Covers: with no `ANTHROPIC_API_KEY` set, the briefing is the deterministic template and `urlopen` is never called (call-count assertion); with a key set and a mocked successful response, the AI text is returned; a malformed/error response falls back to the deterministic template rather than raising; the built prompt payload is asserted (via string search) to contain no `$` dollar-amount patterns or the account ID.
- **test_report.py** — Covers: a `<script>` payload and an `<img onerror>` payload placed in a position's symbol render as inert escaped text in the generated HTML, never as executable markup; rendering with zero snapshots produces a valid HTML page with a "run sync first" placeholder instead of raising; positive vs. negative P&L values get the correct red/green CSS class; the embedded JSON data blob round-trips through `json.loads` unchanged.
- **test_main.py** — Covers: each CLI subcommand's argparse wiring calls the right function with the right arguments (mocked); `sync` on a simulated `IBKRConnectionError` prints a friendly message and exits non-zero instead of crashing with a traceback; `render` with no prior `sync` still produces `dashboard.html` rather than failing; `history --days` passes the limit through correctly.

Minimum 15 tests required; this plan produces at least 20 across the five files, each tied to a real failure mode (connection failure, same-day upsert correctness, XSS, missing-data rendering, AI fallback) rather than padding for count.

## Success Criteria

1. `python -m pytest tests/ -v` passes with zero failures (minimum 15 tests, each covering a real behavior).
2. `main.py sync` against a real TWS/IB Gateway connection (documented for the user in `Manual.md`, not verifiable inside this build container) persists exactly one snapshot row per UTC day, updating rather than duplicating on a same-day re-run — verified in tests against a real temp SQLite file.
3. `main.py render` produces a single self-contained HTML file that opens directly via `file://` with no server, shows the net-liquidation trend and asset-class allocation, and degrades gracefully (DOM-table fallback, no page errors) if the Chart.js CDN is unreachable — verified live in headless Chromium.
4. A `<script>`/`<img onerror>` payload placed in a position symbol renders as inert text in the dashboard, never as executable markup — verified live in headless Chromium, not just by a string-based unit test.
5. With no `ANTHROPIC_API_KEY` set, `render --ai-briefing` makes zero network calls and still produces a complete, readable dashboard — verified by a real `urlopen` call-count assertion in tests.

## Idea Brief Traceability

Not applicable — tonight's idea was freshly generated (Category A backlog lottery missed: roll 66 against a 27% draw chance; no linked Idea Brief exists for this idea). See `WhyThis.md` for full reasoning.
