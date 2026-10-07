# PRD — CanPulse: Canadian Economy Dashboard

> **Build date:** 2026-10-07
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday (day 280, index 0)

## Goal
A Python tool that pulls live Canadian macro data (Statistics Canada + Bank of Canada, both public/no-auth), computes derived signals, and renders one interactive, mobile-readable HTML dashboard with an optional AI briefing.

## User Story
As an academic and founder who follows Canadian economic policy and runs The Canada List (a consumer platform sensitive to trade/tariff/price conditions), I want one phone-readable page showing where inflation, rates, jobs, housing, GDP and the CAD stand, so that I can understand the macro backdrop in two minutes without opening five government sites.

## Scope
### In Scope
- Fetchers: Bank of Canada Valet API (policy rate, USD/CAD, 2y/10y GoC yields) and StatCan WDS (CPI, unemployment, real GDP, new housing price index, retail sales, participation rate), each independent so one failure degrades only that card.
- Disk cache (`data/cache.json`) of last good fetch; `--offline` re-renders from cache; first-run `data/sample_data.json` (clearly labelled illustrative) so the page opens before any fetch.
- Analysis: YoY / MoM change, 5-yr percentile, z-score, trend direction, signal tag per indicator; derived series: real policy rate (policy − CPI YoY), 10y–2y yield spread (curve inversion), CAD change.
- Dashboard: summary cards with sparklines and signal badges; click for detail chart with range buttons (1Y/5Y/10Y/Max); compare mode (two indicators rebased to 100); event markers (COVID, 2022 tightening cycle); dark/light mode; mobile layout; "data as of" and staleness flags.
- Optional AI briefing via Anthropic API (`ANTHROPIC_API_KEY` at runtime; only aggregate public statistics are sent); deterministic rule-based briefing when no key.
- `--verify` mode checking StatCan vector metadata titles against expectations.
### Out of Scope
- Persisting hosted infrastructure, provincial breakdowns, forecasting.

## Tech Stack
- **Language:** Python 3.11 (stdlib only at runtime: urllib, json, statistics), HTML/CSS/JS
- **Framework:** None; Chart.js 4.4.4 via CDN
- **Dependencies:** pytest (tests), Playwright (UI tests, node)
- **Runtime requirement:** `python3 src/main.py` → writes `dashboard.html`

## Data Structure
Series: `{id, label, unit, source, freq, higher_is, title, points: [[YYYY-MM-DD, value], ...]}`. Cache: `{fetched_at, series: {id: Series}, errors: {id: msg}}`. Analysis output per series: `{latest, latest_date, mom, yoy, pct5y, z, trend, signal, stale}`. Dashboard embeds one JSON blob (`window.CANPULSE`).

## Folder Structure
```
builds/2026-10-07-canpulse-economy-dashboard/
├── PRD.md, WhyThis.md, BUILD_LOG.md, FutureFeatures.md, Manual.md
├── requirements.txt, package.json, playwright.config.js
├── src/main.py
├── src/canpulse/{__init__,config,sources,analysis,briefing,render,store}.py
├── src/canpulse/template.html
├── data/sample_data.json
└── tests/{test_sources,test_analysis,test_briefing,test_render,test_store}.py, tests/dashboard.spec.js
```

## Testing Strategy
- **Framework:** pytest (logic, mocked HTTP) + Playwright (rendered page)
- **Run:** `python -m pytest tests/ -v` and `npx playwright test`
- Tested: Valet/WDS parsing from fixtures, partial failure isolation, YoY/percentile/z-score math, derived series alignment, signal rules, briefing fallback and mocked Anthropic call (no network), cache round trip, HTML embedding safety (`</script>` escaping), UI: cards render, click opens detail, range buttons, compare mode, theme toggle, error card.

## Success Criteria
1. All tests pass (zero failures)
2. Rendering from sample data yields a working dashboard with all cards, detail chart, compare mode
3. A failed source degrades to an error card without breaking others
4. No live network calls in tests; no secrets in source
