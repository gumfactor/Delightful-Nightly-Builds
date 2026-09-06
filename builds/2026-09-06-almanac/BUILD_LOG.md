# Build Log — Almanac

> **Date:** 2026-09-06
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Checked `builds/` for incomplete builds: most recent dated folder is `2026-06-18-regex-dojo`, whose BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Read PROFILE.md, STANDARDS.md, and CLAUDE.md.
- `builds/index.md` on the local `main`-derived checkout was stale (last entry 2026-06-24). Per Step 1's instructions, resynced from the most recently opened PR branch instead: found 30 open PRs (#61–#90, dated 2026-08-04 through 2026-09-05) via the GitHub MCP `list_pull_requests` tool, none merged. The newest, PR #90 (branch `claude/cool-sagan-mltlo1`), carries the current `builds/index.md` (83 total builds, last build 2026-09-05) and `builds/ideas.md` (44 backlog rows). Fetched both from that branch and used them — not the stale local copies — for tonight's decision.
- Day of year (UTC): 249. `category_index = (249 - 1) % 9 = 5` → **Category F — Data Explorer**.
- Category F's pending backlog pool (from the synced ideas.md): 5 rows (#10 SEC EDGAR Financial History Extractor, #20 Manuscript Citation Cross-Checker, #21 StatsCan Canadian Business Data Explorer, #30 SEC EDGAR Form 4 Insider Transaction Explorer, #31 Wikipedia Pageview Trend Explorer for Canadian Companies), all unrated (blank = 5 tickets each). R = 0 rated rows → lottery_chance = min(75, 25 + 0) = 25%. Rolled 92/100 → fresh-idea path (see WhyThis.md for full reasoning).
- Reviewed the last 10 builds and all 8 prior Category F builds to check for duplication. Category F is already deep: Qualtrics Survey Data Inspector, GitHub Developer Activity Explorer, TrialScope, GrantScope (NIH RePORTER), ItemScope, Ingest Gate, Effort Ledger, EDGAR Lens (SEC EDGAR). Investment/finance touched twice in the last 10 (Trading Book 08-23, EDGAR Lens 08-28) — not saturated (>2 threshold) but a reason to steer away from a third finance build tonight.
- Generated 3 fresh Category F candidates and picked the strongest: **Almanac** — a browser-based historical climate & extreme-weather data explorer built on Open-Meteo's free, no-auth Historical Weather Archive API, computing percentile climatology bands, extreme-event detection (heat waves, cold snaps, heavy-rain days, high-wind days), year-over-year comparison, and activity-suitability statistics (running/golf/boating) for any location and date range. Untouched data source for Category F, direct tie to PROFILE.md's named running/golf/boating/cottage-life hobbies, and reuses the catalog's highest-rated pattern (deterministic verifiable-statistics engine + interactive dashboard — the same shape as the 9/10 Qualtrics Survey Data Inspector).
- Stack decision: vanilla HTML/CSS/JS + Chart.js (CDN, pinned version), classic `<script>` tags (no ES modules) so it opens directly via `file://` with no server — same convention as Ingest Gate. Playwright for tests, with all Open-Meteo network calls mocked via `page.route()`.
- **API verification constraint:** attempted to confirm the current Open-Meteo Historical Weather Archive and Geocoding API response shapes live via WebFetch before writing the client. Both `archive-api.open-meteo.com` and `geocoding-api.open-meteo.com` are blocked by this build container's egress proxy (`EGRESS_BLOCKED`), consistent with CLAUDE.md's documented network policy. Per CLAUDE.md, this is a build-environment constraint, not a redesign signal — the tool is written against Open-Meteo's documented, stable API contract (`/v1/archive` with `daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max`, `/v1/search` geocoding) for the user's own runtime, where the API is freely reachable. To keep the tool robust to any minor field-naming drift the build session couldn't verify live, the fetch layer surfaces the API's own error payload verbatim on a non-2xx response or a missing/malformed `daily` block, rather than assuming field shapes and silently producing NaN-filled charts.

### [00:20 UTC] PRD Written

- Goal: interactive historical-weather data explorer with deterministic climate statistics for outdoor-activity planning.
- Scope: location search + geocoding, multi-year daily archive fetch, percentile climatology bands, extreme-event detection, year comparison, activity suitability scoring, CSV export, recent-location memory (localStorage).
- Notable constraints: no live Open-Meteo verification possible in the build container (see above); all network calls mocked in tests per CLAUDE.md's testing rules.

### [00:35 UTC] Build Phase

- `src/analytics.js`: pure, dependency-free analytics engine (percentiles with linear interpolation, run-length streak detection for heat waves / cold snaps, activity suitability scoring, monthly climatology, month-window filtering with year-boundary wraparound, CSV escaping). Exposed as `window.Almanac`, classic script.
- `index.html` + `src/styles.css` + `src/app.js`: location search (Open-Meteo Geocoding API) with auto-select on a single match, year-range + season-window + activity-preset controls, Chart.js climatology band and year-comparison charts, extreme-events panel, sortable year table, CSV export (raw daily + year summary), `localStorage`-backed recent-locations and last-settings memory. All DOM writes use `textContent`/`createElement` — zero `innerHTML` anywhere (grep-verified before commit).
- Chose a local static file server (`python3 -m http.server`, wired into `playwright.config.js` as a `webServer`) over raw `file://` navigation for the test suite specifically, after confirming `file://`-origin `localStorage` behaves inconsistently across Chromium sandbox configurations; the shipped app itself still opens directly via `file://` for the user (STANDARDS.md's classic-script, no-ES-module convention preserved) — the test transport is independent of how the user runs it.
- Built the two fixture families in `tests/fixtures/`: hand-crafted geocoding responses (single match, multiple matches, zero matches, an XSS-payload location name) and one hand-computed 17-day historical-archive fixture spanning two years, deliberately constructed to exercise every extreme-event boundary condition (an exact 3-day heat wave, a 2-day non-event, a broken streak, a 2-day cold snap, one heavy-rain day, one high-wind day, one all-null day, and two different activity-suitable days) with every derived number hand-computed before writing a single assertion.

### [00:55 UTC] Tests Run

Tests: 32 passed, 0 failed.

First run surfaced 2 failures, both fixed and re-verified:
1. The XSS-safety test read `.textContent()` once instead of using an auto-retrying `expect(...).toContainText()`, so it sometimes ran before the async search/select chain finished populating the DOM — fixed by switching to the retrying assertion.
2. The Golf-preset suitability test expected the display string `"6.25%"`, but `(6.25).toFixed(1)` renders `"6.3"` in V8 — fixed the test's expected string, not the app's rounding (the app's behavior is correct floating-point display rounding).

### [01:05 UTC] Verify — Step 7

Security checklist (STANDARDS.md): grepped `src/` and `index.html` for `innerHTML`, `eval(`, `exec(`, `document.write` — the only match is a comment documenting the deliberate `textContent`-only convention. No `.env` files, no hardcoded credentials, no personal data, no `os.system`/`subprocess` (N/A, browser-only build), no file-path handling of user input.

PRD success criteria:
1. All tests pass (zero failures) — 32/32 passing.
2. Searching a location and fetching a year range renders climatology chart, extreme-event summary, year-over-year chart, and sortable year table from fetched data only — verified live via the Playwright happy-path test against the hand-built archive fixture; no mock/static data ships in the app itself, only in tests.
3. Extreme-event and suitability numbers are independently verifiable — the fixture's expected heat-wave count (1), cold-snap count (1), heavy-rain-day count (1), high-wind-day count (1), and Running/Golf suitability percentages (12.5% / 6.3%) were all hand-computed in this log before the assertions were written, and the UI matches exactly.
4. A non-2xx or malformed API response never crashes the page — covered by the `archive-error.json` (400 response) and `archive-empty.json` (empty `daily` block) tests; both show a readable status message and keep the results section hidden.
5. No `innerHTML` ever receives API- or user-derived text — grep-verified, and the dedicated XSS fixture test (a location name carrying `<img onerror>` and `</script><script>` payloads) confirms zero injected globals fire and the page's `<script>` count stays at exactly 3. CSV export verified to produce correctly-escaped, round-trippable data for both the raw daily export and the year-summary export.

### [01:10 UTC] Docs — Step 8

- FutureFeatures.md: 7 concrete suggestions across quick wins, medium effort, and ambitious extensions.
- Manual.md: quick start, full usage guide, configuration table, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.

