# PRD — Almanac

> **Build date:** 2026-09-06
> **Category:** F — Data Explorer
> **Complexity:** Ambitious Project
> **Day of week:** Sunday

---

## Goal

A browser tool that turns decades of real historical daily weather data for any location into an explorable climate picture — percentile "normal" bands, extreme-event counts, year-over-year comparison, and how often conditions actually suit running, golf, or boating.

## User Story

As a distance runner, golfer, and cottage-life boater who also thinks in evidence and base rates, I want to explore a location's real multi-year weather history — not just a 7-day forecast — so that I can see how often a given month is actually heat-wave-prone, rain-soaked, or calm enough for the water, and plan around real patterns instead of anecdote.

## Scope

### In Scope
- Location search via Open-Meteo's free Geocoding API (name → lat/lon/timezone candidates), with a picker when multiple matches are returned
- Historical daily fetch via Open-Meteo's free Historical Weather Archive API (`temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `wind_speed_10m_max`) for a user-chosen year range (up to the last ~40 years, bounded to what the API can serve, i.e. not before 1940 and not past yesterday)
- Optional month/season window (e.g. "Jun–Aug only") applied client-side after fetch, so the same fetched dataset supports multiple seasonal views without refetching
- Deterministic analytics computed entirely client-side from the fetched daily arrays:
  - Day-of-year percentile climatology (P10/P25/P50/P75/P90) for temperature, with a shaded-band chart
  - Extreme-event detection: heat-wave streaks (≥3 consecutive days at/above a configurable max-temp threshold), cold-snap streaks (≥2 consecutive days at/below a configurable min-temp threshold), heavy-rain days (precip ≥ configurable threshold), high-wind days (max wind ≥ configurable threshold) — counted per year and totaled
  - Year-over-year overlay chart for a chosen variable across all fetched years
  - Activity suitability scoring for three built-in presets (Running, Golf, Boating) plus a fully custom preset — each preset defines a temp range, a max wind, and a max precipitation; the tool reports the % of days in the selected window meeting all three conditions, per year and averaged
  - Sortable year-by-year summary table (avg high/low, total precip, extreme-event counts, % suitable days)
- CSV export of both the raw fetched daily rows and the computed year-by-year summary
- Recent-location memory in `localStorage` (last 5 searched locations, for one-click reuse — no personal data, just place name + coordinates)
- Error handling for: no geocoding matches, archive API error response, a request the API rejects (e.g. date range outside available history), and empty/all-null data for a variable

### Out of Scope
- Forecasts (this is historical/retrospective only — Run Planner already covers 7-day forward comfort scoring)
- Sub-daily (hourly) data — daily aggregates only, to keep fetch size and analysis scope bounded
- Server-side persistence or multi-device sync — `localStorage` only, per STANDARDS.md guidance for this class of tool
- Air quality / UV / marine-specific variables (wave height, tide) — a real gap for the boating use case, but a distinct data source; noted in FutureFeatures.md

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, ES5-compatible classic scripts — no ES modules, no build step)
- **Framework:** None. Chart.js 4.4.4 via CDN for charts.
- **Dependencies:** Chart.js 4.4.4 (CDN, pinned)
- **Runtime requirement:** Opens directly via `file://` (or any static server) — no install, no build step. Requires internet access at runtime to reach `archive-api.open-meteo.com` and `geocoding-api.open-meteo.com` (both free, no API key).

## Data Structure

All state lives in browser memory plus two `localStorage` keys:

- `almanac.recentLocations` — JSON array (max 5) of `{ name, admin1, country, latitude, longitude, timezone }`, most-recent-first, de-duplicated by coordinates.
- `almanac.lastSettings` — JSON object of the last-used year range, activity preset, and custom thresholds, restored on load for convenience.

In-memory session data (never persisted): the fetched daily arrays `{ time: string[], temperature_2m_max: (number|null)[], temperature_2m_min: (number|null)[], precipitation_sum: (number|null)[], wind_speed_10m_max: (number|null)[] }` and every derived analytics object (percentile bands, extreme events, year summaries).

## Folder Structure

```
builds/2026-09-06-almanac/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── playwright.config.js
├── src/
│   ├── styles.css
│   ├── analytics.js      (pure, testable: percentiles, extreme events, suitability, CSV formatting)
│   └── app.js             (DOM wiring, fetch calls, Chart.js rendering, localStorage)
├── tests/
│   ├── fixtures/
│   │   ├── geocode-toronto.json
│   │   └── archive-toronto.json
│   ├── analytics.spec.js  (pure-function tests via page.evaluate)
│   └── app.spec.js        (UI/integration tests with page.route() network mocks)
```

## Testing Strategy

- **Framework:** Playwright
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Percentile calculation against hand-computed values (odd/even length, single value)
  - Extreme-event streak detection (exact 3-day heat wave boundary, a streak broken by one cool day, no false positive below threshold, streak spanning a year boundary)
  - Activity suitability scoring against a hand-built fixture with known suitable/unsuitable day counts
  - Year-by-year summary aggregation (averages, totals) against a hand-computed fixture
  - CSV formatting (header row, correct escaping of a location name containing a comma)
  - Null/missing-day handling (a day with `null` temperature must be excluded from averages, not treated as 0)
  - Location search: happy path (single match auto-selects), multiple matches (picker shown), zero matches (error message, no crash)
  - Historical fetch: happy path renders charts and table; a mocked non-2xx API response shows the API's own error text; a mocked response with an empty `daily` block shows a "no data" state instead of crashing
  - Activity preset switching updates the suitability numbers
  - CSV export button produces a download with the expected filename pattern
  - XSS safety: a location name fixture containing `<script>`/`</script><script>` and `<img onerror>` payloads renders as inert text everywhere it's displayed (search results, recent-locations list, summary header) — zero `window` globals fire, zero extra `<script>` nodes appended
  - Recent-locations persistence: a searched-and-selected location appears in `localStorage` and is reusable across a reload (simulated via `page.reload()`)
  - Mobile viewport (375px) does not overflow horizontally

## Success Criteria

1. All tests pass (zero failures)
2. Searching a real location name and fetching a real year range renders a percentile-band chart, an extreme-event summary, a year-over-year chart, and a sortable year table — all computed from the fetched daily data, no mock/static data in the shipped app
3. Extreme-event and suitability numbers are independently verifiable: the same hand-computed fixture used in tests produces the exact expected counts when run through the UI
4. A non-2xx or malformed API response never crashes the page — it always shows a readable error state
5. No `innerHTML` assignment ever receives API-derived or user-derived text (verified by the XSS fixture test); CSV export works and round-trips real data

---

## Scope Changes

<!-- Filled in only if scope changes during the build. -->
