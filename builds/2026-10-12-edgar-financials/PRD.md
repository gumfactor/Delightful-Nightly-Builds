# PRD — EDGAR Financials (SEC EDGAR Financial History Extractor)

> **Build date:** 2026-10-12
> **Category:** F — Data Explorer
> **Complexity:** Ambitious Project
> **Day of week:** Monday

---

## Goal

Pull multi-year income statement, balance sheet and cash flow history for a list of US tickers from the SEC EDGAR XBRL API, normalise it across inconsistent XBRL tags, and render a self-contained comparison report (HTML + CSV) with an optional AI commentary.

## User Story

As a solo investor-researcher who screens companies by hand, I want to type a list of tickers and get five years of clean, comparable fundamentals with growth and margin metrics, so that I can compare companies in one view instead of opening each 10-K.

## Idea Brief Traceability

No linked Idea Brief (backlog row #10 has `—`). Backlog description followed: 5 years of income statement and balance sheet data, clean CSV, comparison summary HTML. Extended with cash flow, derived metrics, and optional Claude commentary.

## Scope

### In Scope
- Ticker to CIK lookup via `company_tickers.json`; fact download via `data.sec.gov/api/xbrl/companyfacts`.
- On-disk cache of SEC responses (offline re-runs, polite to SEC), SEC-compliant `User-Agent` from `EDGAR_USER_AGENT`, request throttling and retry on 429/5xx.
- Normalisation: tag-alias fallback per metric and per year (handles ASC 606 revenue tag change), annual-duration filtering, restatement dedupe (latest filing wins), fiscal-year labelling.
- Derived metrics: gross/operating/net margin, free cash flow, ROE, ROA, debt-to-equity, YoY growth, revenue/net-income CAGR.
- Outputs: long-format CSV (`financials_long.csv`), wide per-company CSVs, a one-row-per-company summary CSV, and a self-contained HTML report (Chart.js comparison chart with metric selector, sortable summary table, per-company statements, dark/light mode, mobile-friendly).
- Optional `--ai` commentary using the Anthropic API (`ANTHROPIC_API_KEY` at runtime). Only public SEC figures are sent.
- `--demo` mode that renders the report from clearly-labelled synthetic data so the UI can be inspected without network.

### Out of Scope
- Non-USD reporting, quarterly data, segment data, non-annual filers (see FutureFeatures).
- Price data / valuation multiples.
- Any hosting or persistence beyond local files.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only at runtime (urllib, json, csv, html). Chart.js 4.4.4 via pinned CDN in the report. Tests use stdlib `unittest` (also collectable by pytest).
- **Runtime requirement:** `PYTHONPATH=src python -m edgar_fin AAPL MSFT`

## Data Structure

SEC companyfacts: `{"cik", "entityName", "facts": {"us-gaap": {TAG: {"units": {"USD": [{"start","end","val","form","filed","fp","fy"}]}}}}}`.

Normalised company record:
`{"ticker","cik","name","years":[2020..2024],"metrics":{metric: {year: value}}, "derived":{metric:{year: value}}, "end_dates":{year:"YYYY-MM-DD"}}`

## Folder Structure

```
builds/2026-10-12-edgar-financials/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/edgar_fin/
│   ├── __init__.py
│   ├── __main__.py
│   ├── concepts.py     (tag aliases)
│   ├── sec.py          (client, cache, throttling)
│   ├── extract.py      (companyfacts -> annual series)
│   ├── metrics.py      (derived metrics)
│   ├── exports.py      (CSV)
│   ├── report.py       (HTML)
│   ├── ai.py           (Anthropic commentary)
│   ├── demo.py         (synthetic data)
│   └── cli.py
└── tests/
    ├── helpers.py
    ├── test_extract.py
    ├── test_metrics.py
    ├── test_sec.py
    ├── test_exports.py
    ├── test_report.py
    ├── test_ai.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** `unittest` (pytest compatible; pytest could not be installed in the build container, see BUILD_LOG)
- **Test file location:** `tests/test_*.py`
- **Run command:** `PYTHONPATH=src python -m unittest discover -s tests -v`
- **What will be tested:**
  - Annual-duration filtering (quarterly and YTD facts ignored), restatement dedupe, 10-K only.
  - Alias fallback per year (revenue tag switch), gross-profit fallback, capex sign handling.
  - Fiscal-year labelling for January year-ends.
  - Derived metrics incl. zero/negative denominators and missing data.
  - SEC client: ticker lookup, unknown ticker error, cache hit avoids network, retry on 429, User-Agent required.
  - CSV shape; HTML escaping of hostile company names, no raw `</script>` breakout, all tickers present.
  - AI: prompt contains figures, missing key handled, mocked response rendered escaped.
  - CLI end-to-end with mocked transport; demo mode.
- All network and Anthropic calls are mocked.

## Success Criteria

1. All tests pass (zero failures).
2. A multi-ticker run (mocked transport) writes the long CSV, per-company CSVs, summary CSV and one HTML report.
3. Normalisation correctly merges differing revenue tags across years and ignores non-annual facts.
4. HTML is self-contained, escapes untrusted strings, and renders in dark and light mode.
5. Missing network, missing key, bad tickers degrade gracefully with clear messages.

---

## Scope Changes

Pytest unavailable in build container (pip install denied); tests written with stdlib unittest instead.
