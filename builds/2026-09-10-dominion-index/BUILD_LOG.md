# Build Log — Dominion Index

### [08:10 UTC] Step 0 — Incomplete build check
Local `builds/` was 68 builds behind (`main`/local branch last build 2026-06-18-regex-dojo). Fetched the most recent open PR branch (`claude/cool-sagan-hpwm1q`, PR #94, 2026-09-09 "Headroom") and checked its `BUILD_LOG.md` — ends with "Build complete. Success criteria reviewed. All tests passing." No resume needed.

### [08:15 UTC] Step 1 — Orient
Read `PROFILE.md`, `STANDARDS.md`, and the current `builds/index.md`/`builds/ideas.md` from `origin/claude/cool-sagan-hpwm1q` (87 builds total, last date 2026-09-09).

### [08:20 UTC] Step 2 — Decision
Day of year 253 → Category A (Dashboard/Visualizer). 6 pending Category A backlog ideas, R=1 rated, lottery_chance=27%. Rolled 10 → draw. Weighted draw (29 tickets) picked idea #38, "Canada List Market Landscape". Full reasoning in `WhyThis.md`. Marked `built` in `builds/ideas.md`.

### [08:35 UTC] Step 4 — PRD written
`PRD.md` complete before any code, including the exact SPARQL query and the Canadian-ownership correctness heuristic (headquarters-country + no-foreign-parent, replacing the naive `P17=Canada` filter the backlog row's own notes flagged as wrong).

### [08:40 UTC] Network check
Attempted a live `curl` to `query.wikidata.org/sparql` to verify the query shape before writing it — the sandbox denied the request outright (permission denied at the tool layer, matching the pattern idea #38's own passed-over note described for other hosts: "curl to pypi.org/registry.npmjs.org/api.github.com all denied outright"). Per `CLAUDE.md`, this is a build-environment constraint, not a redesign signal — the query and the 13 province/territory QIDs are written from training knowledge against Wikidata's stable, documented property model, and every test mocks the endpoint rather than calling it live.

### [09:00 UTC] Step 5 — Build
Wrote `src/sparql.js` (query builder + result parser), `src/aggregate.js` (industry/province totals, top-N + Other folding, delta-vs-snapshot), `src/snapshot.js` (storage-injected localStorage read/write), `src/render.js` (DOM rendering — CSV export, table, chart config, all external text via `textContent`/DOM APIs, never `innerHTML`), `src/app.js` (wiring: fetch → parse → aggregate → render, loading/error states, theme toggle, table filter/sort), `index.html`, `src/style.css`. `npm install` succeeded (registry.npmjs.org is reachable even though direct external hosts like `query.wikidata.org` and `cdnjs.cloudflare.com` are not).

### [09:15 UTC] Bug #1 — global name collision across classic scripts
First test run threw `PAGEERROR: Identifier 'api' has already been declared` in the browser. Cause: `sparql.js`, `aggregate.js`, `snapshot.js`, and `render.js` are loaded as classic (non-module) `<script>` tags sharing one global scope, and each file declared `const api = {...}` before attaching it to `window`. Fixed by renaming each module's export constant uniquely (`sparqlApi`, `aggregateApi`, `snapshotApi`, `renderApi`).

### [09:20 UTC] Bug #2 — Chart.js CDN unreachable inside the test browser
Even after fixing bug #1, `fetchAndRender` threw `Cannot read properties of undefined (reading 'aggregateIndustryTotals')` — a red herring from bug #1 still being live at that point, but a second real issue also showed up in the console: `net::ERR_TUNNEL_CONNECTION_FAILED` for the `cdnjs.cloudflare.com` Chart.js CDN request. Confirmed via `page.on('requestfailed')` in a throwaway debug spec that Playwright's browser process (not just this session's `curl`) has no outbound route to the public internet inside this container — the same constraint every prior nightly build has documented for its own CDN/API host. `npm install chart.js@4.4.4` succeeded (npm's registry is reachable even though arbitrary CDN hosts are not), so `tests/app.spec.js` now stubs the CDN request via `page.route` with the locally installed, identically-pinned `chart.umd.js`. The shipped `index.html` is unmodified and still points at the real CDN. Documented in `PRD.md`'s "Network constraint" note.

### [09:30 UTC] Step 6 — Test run
`npx playwright test`: 63 passed, 0 failed, on the first run after fixing both bugs above (two earlier runs surfaced and fixed the bugs above plus two test-authoring mistakes: a miscounted `filterRows` fixture-match count and a `decodeURIComponent`-vs-`+`-encoding mismatch in the `buildQueryUrl` test).

Tests: 63 passed, 0 failed.

### [09:40 UTC] Step 7 — Verify
Success criteria review against `PRD.md`:
1. ✓ `sparql.spec.js` asserts the query contains `?hq wdt:P17 wd:Q16` (headquarters-country) and explicitly asserts it does NOT contain a naive `?company wdt:P17 wd:Q16` filter, plus the `FILTER NOT EXISTS` parent-exclusion clause.
2. ✓ `app.spec.js` happy-path test verifies the rendered total (`219 companies`), the top industry (`Retail`, `65`), the top province (`Ontario`), a 14-row table, and non-null Chart.js instances — all against the hand-computed fixture totals also asserted directly in `aggregate.spec.js`.
3. ✓ Four distinct failure-state tests (empty result, HTTP 500 with verbatim body text, malformed JSON, aborted/network-failure request with file://-specific guidance) each assert their own distinct on-screen text.
4. ✓ The delta test mutates one fixture value between two fetches and asserts the exact `+50` badge with `delta-increased` styling on the second render.
5. ✓ All 63 tests pass; the dedicated XSS test injects an `<img onerror>`/`</script><script>` payload as a Wikidata label and asserts zero dialogs, zero side-effect flags set, zero `<img>` elements in the table, and the literal `<img` text rendered inertly.

Security checklist:
- No `.env` files, no hardcoded credentials/secrets/personal data.
- No `eval()`/`exec()` anywhere.
- No `innerHTML` anywhere in `src/` (grepped) — all DOM text uses `textContent` or is generated by Chart.js's own canvas renderer.
- No `os.system()`/`subprocess`/shell calls with user input (pure browser JS, no server component).
- No file-path handling of any kind (no filesystem access from the page).
- All code lives under this build's own folder.

### [09:50 UTC] Documentation
- `FutureFeatures.md`: 7 concrete suggestions.
- `Manual.md`: quick start, data source and ownership-heuristic explanation, troubleshooting (including the `file://` CORS caveat), known limitations.

Build complete. Success criteria reviewed. All tests passing.
