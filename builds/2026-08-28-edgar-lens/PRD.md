# PRD — EDGAR Lens

> **Build date:** 2026-08-28
> **Category:** F — Data Explorer
> **Complexity:** Ambitious Project
> **Day of week:** Friday

---

## Goal

A Python CLI that pulls a watchlist of companies' real, multi-year financial statement history directly from the free SEC EDGAR XBRL API and renders an interactive dashboard for exploring revenue/margin/leverage trends and deterministically flagged year-over-year anomalies (revenue declines, margin compression, leverage spikes, negative equity, swings to loss).

## User Story

As a solo founder and investing-focused researcher who tracks a personal watchlist of companies, I want to pull each company's actual filed financial statement history (not just current-quarter price data) and see multi-year trends and red flags surfaced automatically, so that I can spot deteriorating fundamentals without manually reading 10-Ks or re-deriving ratios by hand every time I check a ticker.

## Scope

### In Scope
- `sync --tickers TICK1,TICK2,...` — resolve each ticker to its SEC CIK via the public `company_tickers.json` index (cached locally in SQLite so repeat syncs skip the network round trip for tickers already resolved), then fetch that company's full XBRL `companyfacts` document from `data.sec.gov`
- A tag-resolution layer that tries a documented priority list of alternate US-GAAP tags per financial concept (revenue, net income, operating income, assets, liabilities, stockholders' equity, cash), since filers do not all use the same XBRL tag for the same line item
- Extraction of one annual value per concept per fiscal year, restricted to `form == "10-K"` and `fp == "FY"` facts, with duration-concept values (revenue, net/operating income) matched to their instant-concept counterparts (assets, liabilities, equity, cash) by fiscal year
- Local SQLite persistence, deduplicated by `(cik, fiscal_year)` — a re-sync upserts rather than duplicating, so the store reflects the latest-filed values for a year (e.g. after a 10-K/A restatement)
- Deterministic metric computation per company-year: revenue YoY growth, net margin, operating margin, debt-to-equity, and their year-over-year deltas
- Deterministic anomaly flagging with fixed, documented, unit-tested thresholds: revenue decline ≥10% YoY, net-margin compression ≥5 percentage points YoY, debt-to-equity increase ≥0.5x YoY, negative stockholders' equity, and a swing from profit to loss
- `list` / `show TICKER` / `flags` terminal views
- `render [--ai]` — a self-contained dark-mode HTML dashboard: hero stats, a cross-company latest-FY comparison table, a per-company multi-year Chart.js trend chart (revenue/net income/margin) with a graceful DOM-table fallback if the CDN is unreachable, and an Anomalies panel listing every flagged company-year with its reason and numbers
- Optional Claude Haiku one-sentence plain-English note per flagged anomaly (`--ai`), built only from the aggregate numbers already computed (ticker, fiscal year, metric name, values) — never raw filing text — with an unconditional deterministic-template fallback so the dashboard is fully functional with zero network calls and no `ANTHROPIC_API_KEY`
- A configurable SEC-compliant `User-Agent` header (`--user-agent` flag or `EDGAR_USER_AGENT` env var), defaulting to a generic non-personal placeholder, since SEC's fair-access policy asks API clients to self-identify
- Respect for SEC's documented rate guidance via a fixed inter-request delay

### Out of Scope
- Quarterly (10-Q) statement history — annual 10-K figures only, to keep fiscal-year alignment unambiguous
- Non-US-GAAP filers (IFRS-only foreign private issuers use a different taxonomy) — out of scope for tonight, documented as a known limitation
- Automatic ticker discovery/screening — the user supplies the watchlist explicitly
- Any brokerage/account integration (already covered by the 2026-08-23 Trading Book build) — this build is about public filed financial history, not live account state

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`urllib` for HTTP, `sqlite3` for storage, `json`, `argparse`); Chart.js 4.4.4 via CDN in the generated HTML only
- **Runtime requirement:** `python3 main.py sync --tickers AAPL,MSFT` then `python3 main.py render`; opens `dashboard.html` directly in a browser, no server needed

## Data Structure

SQLite database (`edgar_lens.db`, created in the build folder at runtime, not committed):

```sql
CREATE TABLE tickers (
    ticker TEXT PRIMARY KEY,
    cik TEXT NOT NULL,
    company_name TEXT NOT NULL,
    resolved_at TEXT NOT NULL
);

CREATE TABLE financials (
    cik TEXT NOT NULL,
    ticker TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    company_name TEXT NOT NULL,
    revenue REAL,
    net_income REAL,
    operating_income REAL,
    assets REAL,
    liabilities REAL,
    equity REAL,
    cash REAL,
    filed_date TEXT,
    accn TEXT,
    synced_at TEXT NOT NULL,
    PRIMARY KEY (cik, fiscal_year)
);
```

A bundled fixture (`tests/fixtures/sample_companyfacts.json`) mimics the real SEC `companyfacts` JSON shape for extraction/parsing tests, since live SEC calls are never made in tests.

## Folder Structure

```
builds/2026-08-28-edgar-lens/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── edgar_client.py    # ticker→CIK resolution + companyfacts fetch (urllib, rate-limited)
│   ├── extract.py         # XBRL tag-resolution + fiscal-year alignment
│   ├── metrics.py         # YoY growth, margins, leverage, anomaly flags
│   ├── storage.py         # SQLite schema + upsert/query helpers
│   ├── ai_narrative.py    # optional Claude Haiku call + deterministic fallback
│   ├── render.py          # HTML dashboard generation
│   └── cli.py             # argparse CLI: sync / list / show / flags / render
└── tests/
    ├── test_extract.py
    ├── test_metrics.py
    ├── test_storage.py
    ├── test_edgar_client.py
    ├── test_ai_narrative.py
    ├── test_render.py
    ├── test_cli.py
    └── fixtures/
        └── sample_companyfacts.json
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Tag-resolution priority chain picks the first present US-GAAP tag per concept, and correctly skips a tag present in the facts but with no USD unit
  - Fiscal-year extraction only accepts `form == "10-K"` and `fp == "FY"` facts, ignoring 10-Q/8-K entries and non-FY facts in the same tag's fact list
  - Duration vs. instant concept handling (revenue/net income keyed by fiscal year end; assets/liabilities/equity/cash matched to the same fiscal year by `end` date)
  - Metric math: revenue YoY growth, net margin, operating margin, debt-to-equity — each against a hand-worked reference calculation
  - Every anomaly threshold at and around its exact boundary (e.g. -9.9% vs -10.0% revenue YoY; equity of $1 vs $0 vs -$1)
  - Division-by-zero / missing-denominator guards (zero revenue, zero/negative equity) never raise and produce a labeled "not meaningful" result instead of crashing
  - SQLite upsert: a second sync for the same ticker/fiscal-year replaces rather than duplicates the row
  - `edgar_client`: HTTP calls are fully mocked (no live network in tests); the rate-limit delay and the configurable `User-Agent` header are asserted on the outgoing request; a 404/malformed-JSON response is handled without crashing the sync
  - `ai_narrative`: with no `ANTHROPIC_API_KEY` set, zero network calls occur and the deterministic template is returned; with a mocked successful response, the AI text is used; with a mocked network failure, it falls back to the deterministic template without raising
  - HTML rendering: a ticker/company name containing `<script>` and `<img onerror>` payloads is confirmed to appear only as escaped/inert text in the generated `dashboard.html` (string-level assertion that no unescaped `<script>` tag other than the page's own is present)
  - CLI: `sync`/`list`/`show`/`flags`/`render` argument parsing and end-to-end flow against a fully mocked EDGAR client and an in-memory/temp SQLite file

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. `sync` against a mocked EDGAR response correctly resolves a ticker, extracts multi-year financials via the tag-resolution chain, and upserts without duplication on a second run
3. Every anomaly type (revenue decline, margin compression, leverage spike, negative equity, swing to loss) fires correctly on a hand-constructed fixture designed to trigger it, and does not fire on a fixture designed to avoid it
4. `render` produces a self-contained `dashboard.html` that opens directly in a browser with zero required build step, shows the comparison table and per-company trend chart, and safely escapes all company/ticker text against script injection
5. With no `ANTHROPIC_API_KEY` set, `render --ai` makes zero network calls and still produces complete, correctly-worded anomaly narratives from the deterministic template

---

## Scope Changes

None — full scope as specified above was delivered.
