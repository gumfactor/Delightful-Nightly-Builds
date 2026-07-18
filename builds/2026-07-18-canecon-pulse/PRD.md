# PRD — CanEcon Pulse

> **Build date:** 2026-07-18
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious Project
> **Day of week:** Saturday

---

## Goal

A Python tool that fetches live Canadian macroeconomic indicators (exchange rates, policy interest rate, CPI, unemployment) from free public government APIs, builds a growing local history of them, and renders a self-contained dark-mode HTML dashboard with trend charts, period-over-period deltas, and an optional AI-generated plain-English briefing on what the latest movements mean for the cost of imported goods versus Canadian-made products.

## User Story

As a founder building The Canada List (a Canadian-ownership consumer advocacy platform) who also follows Canadian economic policy as a personal interest, I want a always-current, one-glance view of the handful of macro indicators that actually move the "buy Canadian vs. buy imported" cost calculus (CAD/USD, the policy rate, CPI, unemployment), so that I have real economic context on hand for editorial writing and my own reading without hunting across Bank of Canada and StatsCan's own web tools.

## Scope

### In Scope
- `sync` command: fetches current data for 5 curated indicators — USD/CAD exchange rate, EUR/CAD exchange rate, Bank of Canada policy interest rate, Canada All-Items CPI, and the national unemployment rate — from the Bank of Canada Valet API (FX + interest rate, no auth) and Statistics Canada's Web Data Service (CPI + unemployment, no auth), and stores each dated observation in a local SQLite database, deduplicated by (series, date) so re-running never creates duplicate rows and a real multi-day history accumulates over repeated use.
- Per-indicator graceful degradation: if one indicator's fetch fails or returns a shape the parser doesn't recognize, that indicator is skipped with a logged warning and every other indicator still syncs — a single bad endpoint never aborts the whole sync.
- `show` command: fast terminal summary of the latest value and day-over-day / week-over-week / month-over-month deltas for every indicator with stored history.
- `render` command: generates a self-contained dark-mode HTML dashboard (opens via `file://`, no server) with one Chart.js line-chart panel per indicator (trend over all locally stored history), a latest-value hero stat with delta badges, a data-freshness ("as of") timestamp per indicator, and a "data unavailable yet — run `sync`" empty state for indicators with no history.
- Optional AI briefing: when `ANTHROPIC_API_KEY` is set, `render --briefing` calls Claude Haiku with only the aggregated numeric deltas (never raw text scraped from any source) to produce a short, plain-English paragraph on what the latest movements imply for consumer purchasing power and the relative cost of imported vs. Canadian-made goods. A deterministic template-based fallback (built from the same deltas) is used whenever no key is set or the call fails for any reason, so the dashboard is always complete without a key.
- `run` command: convenience wrapper that does `sync` followed by `render`.
- CLI built with `argparse`; clear error messages for common failure modes (no network, empty database on `show`/`render` before any `sync`, malformed API responses).

### Out of Scope
- Historical backfill beyond what the Bank of Canada / StatsCan "recent observations" endpoints return per call — the dashboard's real value compounds the more nights the user runs `sync`, not from a one-time bulk import.
- Any indicator requiring an API key not listed in PROFILE.md's Data Sources (e.g. paid data vendors).
- Editing/annotating the data, alerts/notifications, or scheduling `sync` automatically — a future Routine wrapper is a natural follow-on (see FutureFeatures.md), not tonight's scope.
- Any user-entered personal data — this tool sends nothing but aggregated public macro numbers to Claude, and only when the user has supplied a key.

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None (stdlib only)
- **Dependencies:** stdlib only — `sqlite3`, `urllib.request`, `urllib.error`, `json`, `argparse`, `html`, `datetime`, `dataclasses`. Generated HTML loads Chart.js 4.4.4 from a pinned CDN URL at view time only.
- **Runtime requirement:** `python3 canecon_pulse.py run` from the build folder; opens the resulting HTML file directly in any browser, no server or build step needed.

## Data Structure

Local SQLite database at `output/canecon.db` (created on first `sync`), one table:

```sql
CREATE TABLE observations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id    TEXT NOT NULL,     -- e.g. "FXUSDCAD", "STATCAN_CPI_ALL"
    series_label TEXT NOT NULL,     -- e.g. "USD/CAD Exchange Rate"
    unit         TEXT NOT NULL,     -- e.g. "CAD per USD", "%", "index (2002=100)"
    source       TEXT NOT NULL,     -- "Bank of Canada Valet" | "Statistics Canada WDS"
    obs_date     TEXT NOT NULL,     -- ISO date "YYYY-MM-DD"
    value        REAL NOT NULL,
    fetched_at   TEXT NOT NULL,     -- ISO datetime this row was synced
    UNIQUE(series_id, obs_date)
);
```

The 5 tracked indicators are defined in a single `INDICATORS` config list in `src/indicators.py` (series id, human label, unit, fetch function) so a stale StatsCan vector ID can be corrected in one place without touching fetch/storage/render logic.

## Folder Structure

```
builds/2026-07-18-canecon-pulse/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── canecon_pulse.py
├── src/
│   ├── __init__.py
│   ├── indicators.py
│   ├── boc_client.py
│   ├── statcan_client.py
│   ├── storage.py
│   ├── deltas.py
│   ├── briefing.py
│   └── html_report.py
└── tests/
    ├── __init__.py
    ├── test_boc_client.py
    ├── test_statcan_client.py
    ├── test_storage.py
    ├── test_deltas.py
    ├── test_briefing.py
    ├── test_html_report.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Bank of Canada Valet response parsing (valid payload → correct observations; malformed/empty payload → empty list, no crash)
  - StatsCan WDS response parsing (valid payload → correct observations; error-status payload → empty list, no crash)
  - Network failures (`urllib.error.URLError`, HTTP error status) are caught and produce an empty result rather than propagating
  - SQLite storage: insert, duplicate (series, date) is a no-op (idempotent re-sync), multiple series coexist, retrieval ordered by date
  - Delta computation: day/week/month deltas correct given a known observation history; missing comparison points handled (returns `None`, not an exception)
  - HTML report renders all indicators with data; renders the correct "no data yet" empty state for an indicator with zero rows; user-derived text (series labels) is HTML-escaped
  - AI briefing: mocked successful Claude call is used; missing API key falls back to template; a mocked API failure (bad status, malformed JSON) also falls back to template without raising
  - CLI: `sync` with no network handled gracefully; `show`/`render` on an empty database produce a clear message instead of crashing; `run` chains sync + render

## Success Criteria

1. All tests pass (zero failures)
2. `sync` stores deduplicated observations per indicator and never crashes when an individual indicator's API call fails
3. `render` produces a self-contained dark-mode HTML dashboard with a live Chart.js trend chart, latest value, and delta badges for every indicator that has stored history, verified with zero console errors in headless Chromium
4. The optional AI briefing path and its deterministic fallback both produce complete, non-empty output, verified via mocked tests since no Anthropic key is present in the build container
5. Every indicator fetch failure degrades gracefully (skips that indicator, logs a warning, does not abort the rest of `sync` or crash `render`)

---

## Scope Changes

None — full in-scope feature set as specified above was completed as planned. One documented constraint: this build container's egress proxy denies outbound requests to `bankofcanada.ca` and `statcan.gc.ca` at the Bash tool permission layer (confirmed by a direct test during orientation), so the fetch clients could not be exercised against live traffic during the build session. This is a build-environment constraint per CLAUDE.md, not a design signal — both clients are written and tested against each API's documented response schema, all live-network paths are exercised only through mocks in `tests/`, and the code will make real requests when the user runs it locally where these public, no-auth government APIs are reachable.
