# BUILD_LOG.md — Corporate Ownership Chain Explorer

### [Step 0] Incomplete-build check
Most recent dated local folder: `builds/2026-06-18-regex-dojo` (complete). Local `main`/session branch is far behind the actual catalog — the most recent open PR branch (`claude/cool-sagan-l3gjln`, PR #107, 2026-09-23 "Pooling Lab") is the real head of the build history (100 builds, `Build complete. Success criteria reviewed.` confirmed in its `BUILD_LOG.md`). No interrupted build found. Proceeding to tonight's build.

### [Step 1] Orient
Read `PROFILE.md`, `STANDARDS.md`, and `builds/index.md` resynced from `origin/claude/cool-sagan-l3gjln` (100 rows, last build 2026-09-23). Noted: every build since 2026-06-26 is unrated (`Your Rating` = `—`) — the user has not yet reviewed the ~74-build backlog of open, unmerged PRs. This is a pattern worth surfacing to the user outside this build's own scope.

### [Step 2] Decide
- Category: day-of-year 267 → index 5 → **F — Data Explorer**.
- Lottery: 9 pending Category F ideas, all unrated (R=0) → 25% chance. Roll 11 → draw. Weighted pick (45 tickets, 5 each) → idea #61, "Corporate Ownership Chain Explorer". Marked `built` in `builds/ideas.md`. Full reasoning in `WhyThis.md`.
- No linked Idea Brief for idea #61.
- Stack: browser tool (Category F requires a visual/interactive interface) — vanilla HTML/CSS/JS, classic scripts (no ES modules, no bundler) so it opens directly via `file://`, matching the established pattern for this repo's vanilla builds (WeatherSong, CircuitLab, Confound Hunter). Playwright for tests.
- Data source: Wikidata Query Service SPARQL endpoint (`query.wikidata.org/sparql`) and the `wbsearchentities` action of the Wikidata API (`www.wikidata.org/w/api.php`) — both free, no-auth, CORS-enabled for direct browser `fetch()`. Confirmed in PROFILE.md's Data Sources (Wikipedia/Wikidata, no credentials).
- Deployment model: on-demand browser tool the user opens when doing Canada List editorial fact-checking — not a schedule/hook/skill fit, matches the pattern of prior Category F/data-explorer builds shipped as standalone HTML tools.

### [Step 3] Build folder created
`builds/2026-09-24-corporate-ownership-explorer/`

### [Step 4] PRD written
`PRD.md` complete — Goal, User Story, Scope (in/out), Tech Stack, Data Structure, Folder Structure, Testing Strategy, Success Criteria. Key scope decision made while writing it: `focusEntity` was originally sketched with an `instanceOf` field, but since `wbsearchentities` already returns `{id, label, description}` for the entity the user picks, a separate entity-details fetch (and the SPARQL complexity of resolving `instanceOf`'s own label) was dropped — the search selection itself supplies everything the focus header needs. Documented here per STANDARDS.md's "Scope Changes" guidance rather than editing the already-written PRD.

### [Step 5] Build
Implemented in dependency order: `src/graph.js` (pure logic — chain building, cycle/depth-cap handling, SPARQL/search-result parsing, citation URL + qualifier formatting, primary-parent selection), `src/api.js` (Wikidata `wbsearchentities` + `query.wikidata.org/sparql` fetch wrappers, one query for parents with qualifiers via `p:`/`ps:`/`pq:`, one UNION query for subsidiaries covering both `P355` forward and reverse `P127`/`P749`), `src/render.js` (DOM rendering, `createElement`/`textContent` only, zero `innerHTML`), `src/app.js` (state, debounced search, drill-down/breadcrumb orchestration, localStorage recents), `index.html` + `src/styles.css` (dark-mode-first with a `prefers-color-scheme: light` override, mobile-responsive two-column-to-one-column layout).

`npm install` for `@playwright/test` completed cleanly in the build folder (no external-API dependency, so the container's egress restriction doesn't affect it).

### [Tests] Step 6 — Test run
First run: 35/37 passed, 2 failures.
- `ui.spec.js` "parent ownership chain renders... citation link": `getByTestId('chain-node')` matched 3 elements (2 in the parent chain + 1 in the subsidiaries panel, since both panels reuse the same `chain-node` test id) instead of the expected 2. Fixed by scoping the locator to `page.getByTestId('parent-chain').getByTestId('chain-node')`.
- `ui.spec.js` "recent searches persist... after reload": a `beforeEach` hook used `page.addInitScript()` to clear `localStorage` for test isolation, but an init script re-fires on every navigation in that page — including the test's own `page.reload()` — so it was wiping the just-saved recent-search entry before the app re-read it. Each Playwright test already runs in its own fresh, isolated browser context by default (empty storage per test), so the manual clear was both redundant and actively wrong; removed it entirely.

Second run: **37/37 passed, 0 failed.**

[08:25 UTC] Tests: 37 passed, 0 failed.

### [Verify] Step 7 — Success criteria check
1. ✓ Live-shaped search → selection populates the focus entity — `ui.spec.js` "typing a query renders a debounced dropdown" + "selecting a search result populates the focus panel".
2. ✓ Parent chain correct, cycle-safe, depth-capped against synthetic pathological inputs — `graph.spec.js` linear/root/cycle/default-depth-cap/custom-depth tests (5 tests).
3. ✓ Every ownership edge carries a working Wikidata statement citation link — `graph.spec.js` `formatCitationUrl` tests + `ui.spec.js` chain-render test asserting the actual rendered `href`.
4. ✓ Clicking a subsidiary or parent re-centers the explorer and updates the breadcrumb — `ui.spec.js` "clicking a subsidiary drills down" + "clicking an earlier breadcrumb entry jumps back".
5. ✓ XSS-safe rendering and zero live network calls in tests — `security.spec.js` (hostile label in search results, hostile label in the ownership chain, malformed-response handling with a `pageerror` listener asserting zero unhandled errors) + every network-touching test in `ui.spec.js`/`security.spec.js` routes through `page.route()` interception; `graph.spec.js` never calls `fetch` at all.
6. ✓ 37/37 tests pass. Security checklist run below. `builds/index.md` updated in Step 9.

Manual visual verification: rendered the live app (mocked Wikidata responses matching the real API's documented JSON shape) in headless Chromium at 900×900 (dark and light `prefers-color-scheme`) and at a 390×844 mobile viewport. Confirmed: two-level parent chain renders in the correct order with the qualifier ("as of 2020") and a working citation link; the subsidiary renders and its citation link is correct; dark/light both readable with sufficient contrast; mobile layout collapses the two-column chain/subsidiary grid to one column with no overflow, matching the `ui.spec.js` mobile-viewport assertion. A live end-to-end run against the real `query.wikidata.org`/`www.wikidata.org` endpoints was not possible from the build container (egress proxy blocks most external hosts per PROFILE.md's documented build-container network policy) — this is a build-environment constraint, not a design compromise; the user runs this locally where those endpoints are freely reachable, and every request shape in `src/api.js` matches Wikidata's documented, versioned REST/SPARQL response formats.

Security checklist (STANDARDS.md):
- No `.env` files anywhere in the build folder.
- No `password`/`api_key`/`secret`/`token`/`private_key` with a real value assigned anywhere in `src/`, `index.html`, or `package.json` — confirmed by grep.
- No `eval()`, `exec()`, or `new Function()` anywhere in this build — confirmed by grep.
- No `innerHTML` assignment anywhere in this build (the only match for the string "innerHTML" is a comment in `render.js` explaining that it's deliberately avoided) — confirmed by grep and by the two hostile-payload rendering tests in `security.spec.js`.
- No `os.system()`/`subprocess` calls (pure client-side JS, no Python in this build).
- No file paths constructed from user input anywhere in this build.
- All files live under this build folder; only `builds/index.md` and `builds/ideas.md` are touched outside it.
- `node_modules/`, `test-results/`, and `playwright-report/` are excluded via a build-folder `.gitignore` and were not staged for commit.

### [Docs] Step 8 — Documentation
- `Manual.md` written (this build has a UI — the explorer itself).
- `FutureFeatures.md` written with 8 concrete suggestions.

Build complete. Success criteria reviewed. All tests passing.
