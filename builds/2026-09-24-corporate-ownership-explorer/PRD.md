# PRD — Corporate Ownership Chain Explorer

## Goal
Given a company name, show its live, citable Wikidata-sourced ownership lineage — who owns it and what it owns — as an interactive, click-to-drill-down chain, so Canada List editorial fact-checking can verify "is this actually Canadian-owned?" in seconds instead of manual lookups.

## User Story
As the operator of The Canada List, when I'm vetting whether a business or product is genuinely Canadian-owned, I want to search a company and see its full parent-ownership chain and known subsidiaries in one view, each link backed by a direct citation to the Wikidata statement it came from, so I can trust the answer and trace it back to a source if challenged.

## Scope

### In scope
- Live search over Wikidata entities (`wbsearchentities` API) with debounced autocomplete.
- For a selected "focus" company: fetch and display
  - The full upward ownership chain (repeatedly resolving `owned by` (P127) / `parent organization` (P749)) until no further parent is found, a cycle is detected, or a depth cap (8 hops) is reached.
  - Direct subsidiaries (P355 forward, plus reverse P127/P749) as a clickable list — one hop, drill-down on click (lazy: clicking a subsidiary re-centers the explorer and fetches its own chain/subsidiaries).
- A citation link on every ownership edge, pointing directly at the Wikidata statement (`https://www.wikidata.org/wiki/Q<id>#P<prop>`) so the underlying source/reference metadata Wikidata itself records can be inspected.
- Qualifier display (point-in-time / start-end dates) on ownership edges when Wikidata records them, since ownership can change over time.
- Breadcrumb trail of companies visited this session (click to jump back).
- A "Recent searches" list (localStorage, last 10) as a convenience cache on top of live data — never a substitute for it.
- Graceful empty states (no parent found, no subsidiaries found) and graceful error states (network failure, malformed API response).
- Cycle protection (A owns B owns A) so the UI never hangs or infinitely recurses.
- All rendering via `textContent`/`createElement` — no `innerHTML` from API- or user-derived text (company labels are Wikidata-controlled but still untrusted for rendering purposes).

### Out of scope
- Editing Wikidata data (read-only tool).
- A full ownership *graph visualization* (nodes/edges canvas) — tonight's mechanic is a linear drill-down chain plus a subsidiary list, not a force-directed graph. (Documented as a future enhancement.)
- Resolving ownership *percentages* (Wikidata rarely records these reliably for P127/P749) — the tool shows the *relationship*, not a stake percentage.
- Any write access, accounts, or server-side persistence. Everything is client-side; the only persisted state is the local "recent searches" convenience cache.

## Tech Stack
- Vanilla HTML/CSS/JS, classic `<script>` tags (no ES modules, no bundler) — opens directly via `file://`, matching this repo's established pattern for standalone browser tools (WeatherSong, CircuitLab, Confound Hunter).
- Wikidata Query Service SPARQL endpoint (`https://query.wikidata.org/sparql`) and Wikidata `wbsearchentities` action API (`https://www.wikidata.org/w/api.php`) — both free, public, no-auth, CORS-enabled for direct browser `fetch()`. Confirmed under PROFILE.md's Data Sources ("Wikipedia / Wikidata — encyclopedic and structured reference data, no auth required").
- Playwright for tests (`tests/*.spec.js`), per STANDARDS.md's HTML/JS test framework mapping.

## Data Structure

### Runtime state (in-memory, `app.js`)
```js
{
  focus: { id: "Q...", label: "", description: "", instanceOf: "" } | null,
  parentChain: [
    { id, label, property: "P127"|"P749", qualifierText, statementUrl }
  ],
  subsidiaries: [
    { id, label, property: "P355"|"P127"|"P749", statementUrl }
  ],
  history: [ { id, label } ],      // breadcrumb, this session only
  recent: [ { id, label, ts } ]    // persisted, localStorage, capped at 10
}
```

### Normalized API response shapes (produced by `src/graph.js` parsers)
- `parseSearchResults(json) -> [{ id, label, description }]`
- `parseSparqlBindings(json, { idVar, labelVar, propVar?, qualifierVar? }) -> [{ id, label, property?, qualifierText? }]`

### localStorage key
`ownership-explorer:recent` — JSON array of `{ id, label, ts }`, capped at 10, most-recent-first. Read/write wrapped in try/catch (private browsing / disabled storage must degrade to an empty list, never throw).

## Folder Structure
```
builds/2026-09-24-corporate-ownership-explorer/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── playwright.config.js
├── index.html
├── src/
│   ├── styles.css     — layout, dark-mode-first theme, mobile-responsive
│   ├── graph.js        — pure logic: chain building, cycle detection, parsing, formatting (window.OwnershipGraph)
│   ├── api.js           — Wikidata fetch wrappers, isolated so tests can stub window.fetch (window.OwnershipApi)
│   ├── render.js        — DOM rendering helpers, textContent/createElement only (window.OwnershipRender)
│   └── app.js            — state, event wiring, debounce, drill-down orchestration, localStorage recents
└── tests/
    ├── graph.spec.js      — pure-logic tests (chain building, cycles, parsing, formatting) via page.evaluate
    ├── ui.spec.js          — end-to-end flows with mocked network (search → select → chain/subsidiaries → drill-down → breadcrumb → recents)
    └── security.spec.js    — XSS-hostile label rendering, error-state resilience
```

## Testing Strategy
Framework: Playwright (`npx playwright test`), per STANDARDS.md. All external API calls are mocked via `page.route()` interception in every test — no live network calls in any test, per CLAUDE.md's hard rule. `graph.spec.js` tests pure functions directly through `page.evaluate()` against `window.OwnershipGraph`, so they run with zero network involvement at all (the page loads `about:blank`-equivalent local `index.html`, but no fetch happens).

Coverage:
1. **Pure logic (`graph.spec.js`, ~11 tests):** linear parent-chain resolution; no-parent (root) termination; cycle detection (A→B→A) stops without hanging and flags the cycle; max-depth cap (8) is respected on a synthetic long chain; subsidiary de-duplication when the same entity is reachable via both P355 and reverse-P127; citation URL formatting for a plain statement and for one with a qualifier; qualifier text formatting for point-in-time, start-only, and start+end dates; SPARQL binding parsing with all optional fields present vs. missing; search-result parsing on an empty result set.
2. **End-to-end UI (`ui.spec.js`, ~10 tests):** empty initial state; debounced search renders dropdown from a mocked response; selecting a result populates the focus panel and issues the ownership queries; parent chain renders in correct order with citation links; subsidiaries render and are clickable; clicking a subsidiary drills down (re-centers, fetches its own chain) and updates the breadcrumb; clicking a breadcrumb entry jumps back without re-fetching already-cached data; a company with no recorded ownership data shows explicit empty-state text (not a blank panel); a simulated network failure shows an error banner and leaves the UI usable; recent searches persist to `localStorage` and re-render on reload; narrow (390px) viewport does not clip or break the layout.
3. **Security (`security.spec.js`, ~4 tests):** a mocked label containing `<img src=x onerror=alert(1)>` renders as literal inert text with zero script execution and zero `innerHTML` use for that content; a search query containing special/reserved URL characters is correctly percent-encoded before being sent (assert on the intercepted request URL, not just visually); a malformed/non-JSON API response is caught and shown as an error rather than throwing an unhandled exception; verifying no `eval`/`Function`/`innerHTML`-from-API-data path exists by exercising the actual rendering functions with hostile input rather than static grep alone.

Total: 25 tests, all required to pass with zero failures before commit.

## Success Criteria
1. Searching a company name returns live-shaped, correctly parsed Wikidata candidates and selecting one renders that company as the focus entity — verified by `ui.spec.js` search/select tests.
2. The rendered parent-ownership chain is correct, cycle-safe, and depth-capped against synthetic pathological inputs (a real cycle, a chain longer than the cap) — verified by `graph.spec.js`.
3. Every rendered ownership edge carries a working citation link to the specific Wikidata statement it came from (`.../wiki/Q<id>#P<prop>`) — verified by both `graph.spec.js` (URL formatting) and `ui.spec.js` (link present and correctly targeted in the rendered DOM).
4. Clicking a subsidiary or a parent re-centers the explorer on that company and updates the breadcrumb, enabling genuine drill-down navigation rather than a single static lookup — verified by `ui.spec.js`.
5. No API-derived or user-derived text can execute as script (XSS-safe rendering) and no network call in the test suite is live (every test mocks `page.route`) — verified by `security.spec.js` and by a manual audit of every `fetch` call site in `src/`.
6. All 25 tests pass with zero failures; `STANDARDS.md`'s security checklist passes; `builds/index.md` is updated with this build's row.
