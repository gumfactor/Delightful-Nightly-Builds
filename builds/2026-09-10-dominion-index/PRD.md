# PRD — Dominion Index

## Goal

A single-page browser dashboard that queries Wikidata's live, public SPARQL endpoint for Canadian-owned companies and renders their industry and province composition, giving The Canada List's editorial work real market-context numbers instead of manual lookups.

## User Story

As the operator of The Canada List, I want to see how many Canadian-owned companies Wikidata knows about, broken down by industry and by province, so that I can spot under-covered industries/regions in the directory and cite real aggregate numbers in editorial content — without hand-querying Wikidata or writing SPARQL myself.

## Idea Brief Traceability

This build realizes backlog idea **#38** ("Canada List Market Landscape", added 2026-08-23, drawn via the Category A lottery on 2026-09-10 — 6-idea pool, 27% lottery gate rolled 10, weighted draw picked idea #38 out of 29 total tickets). There is no linked Idea Brief document for this row (the `Idea Brief` column was `—`), so this PRD is the full and only specification. The row's own rating notes flagged the exact correctness risk this PRD's Data Structure section addresses: naive `P17 (country) = Canada` filtering would mischaracterize a foreign company's Canadian subsidiary (e.g. a local sales office) as "Canadian-owned." See "Canadian-ownership definition" below for the fix.

## Scope

### In scope
- A single static HTML page (`index.html`, opens directly via `file://`, no build step, no server required)
- One live SPARQL query to `https://query.wikidata.org/sparql` (GET, `Accept: application/sparql-results+json`), fired on load and on a manual "Refresh" button
- Aggregate counts of Canadian-owned companies grouped by (industry, province) pairs — the query does the counting server-side; the client never pulls per-company rows
- Industry bar chart (top N industries by count, "Unclassified" bucket for companies with no `P452` industry)
- Province bar chart (13 provinces/territories plus an "Unknown" bucket for companies whose headquarters can't be resolved to a province)
- A sortable, filterable table of every (industry, province, count) triple returned
- CSV export of the raw triples
- `localStorage` snapshot of the last successful fetch (timestamp + totals), used to show a "since last visit" delta badge (up/down/new/gone) next to each industry and province on the next successful fetch — a genuine trend signal without needing a persisted backend
- Explicit, verbatim error states: query timeout, malformed response, network/CORS failure — each with actionable text, never a silent fallback to fake data
- Dark mode default with a light mode toggle; mobile-responsive
- Playwright tests: pure-logic tests (query builder, result parser, aggregation, delta computation, CSV escaping) run directly against the source modules; UI tests mock the Wikidata endpoint via Playwright's `page.route` — no test ever makes a live network call

### Out of scope
- Per-company drill-down or lookup (that's CanFile's and Provenance's shape — this build is deliberately the aggregate-count shape the backlog row asked for)
- Historical time-series storage beyond the single last-visit snapshot kept in `localStorage`
- Any write access to Wikidata (read-only SPARQL `SELECT` only)
- Server-side proxy or caching layer (none needed — the public endpoint is queried directly from the browser)

## Tech Stack

Vanilla HTML/CSS/JS (classic `<script>` tags, no ES modules, no bundler — opens directly via `file://`), Chart.js 4.4.4 pinned via CDN in `index.html`, `@playwright/test` for tests (dev-only dependency). The `chart.js` npm package is also a dev-only dependency, used solely so Playwright's test browser (which has no route to the public internet inside this build container) can be served the exact same pinned 4.4.4 UMD build in place of the CDN request — see "Network constraint" below. The shipped `index.html` is untouched by this and still loads Chart.js from the CDN for the user.

### Network constraint
This build container's sandbox has no route to the public internet (a live `curl` to an external host was denied outright at the sandbox layer, and the test browser's own request to `cdnjs.cloudflare.com` failed with `ERR_TUNNEL_CONNECTION_FAILED`), so `tests/app.spec.js` intercepts the Chart.js CDN request via `page.route` and fulfills it with the locally npm-installed `node_modules/chart.js/dist/chart.umd.js` (pinned to the identical 4.4.4 version) instead of skipping chart verification or vendoring a copy into the shipped app. This is a test-infrastructure workaround for the build container only, not a product decision — the user's browser reaches the real CDN normally.

## Canadian-ownership definition (the correctness fix backlog idea #38 called for)

A naive query (`?company wdt:P17 wd:Q16`, i.e. "country property is Canada") would count a foreign multinational's Canadian subsidiary as a Canadian-owned company, because a subsidiary can itself be legally registered ("country of registration") in Canada while its ultimate owner is not. This build instead uses:

1. **Headquarters-in-Canada, not registration-in-Canada**: `?company wdt:P159 ?hq` (headquarters location) and `?hq wdt:P17 wd:Q16` — the physical HQ's country, not the entity's own `P17`.
2. **No foreign parent**: `FILTER NOT EXISTS` excludes any company with a `P749` (parent organization) or `P127` (owned by) value whose own `P17` (country) is asserted and is *not* Canada. A company with no parent-organization statement at all, or whose parent's country is simply unrecorded on Wikidata, is treated as Canadian-owned by default (documented as a known false-positive risk in `Manual.md`, since Wikidata's ownership graph is incomplete — this is a limitation of the data source, not the query logic).

This is a heuristic, not a legal determination — it is documented as such in `Manual.md`'s Known Limitations section.

## Data Structure

**SPARQL query** (built by `src/sparql.js#buildQuery()`, one round trip):

```sparql
SELECT ?industryLabel ?provinceLabel (COUNT(DISTINCT ?company) AS ?count) WHERE {
  ?company wdt:P31/wdt:P279* wd:Q4830453 .
  ?company wdt:P159 ?hq .
  ?hq wdt:P17 wd:Q16 .
  FILTER NOT EXISTS {
    { ?company wdt:P749 ?parent } UNION { ?company wdt:P127 ?parent }
    ?parent wdt:P17 ?parentCountry .
    FILTER(?parentCountry != wd:Q16)
  }
  OPTIONAL {
    ?company wdt:P452 ?industry .
    ?industry rdfs:label ?industryLabelRaw . FILTER(LANG(?industryLabelRaw) = "en")
  }
  BIND(COALESCE(?industryLabelRaw, "Unclassified") AS ?industryLabel)
  OPTIONAL {
    VALUES ?province { wd:Q1904 wd:Q176 wd:Q1974 wd:Q1951 wd:Q1948 wd:Q1989 wd:Q13603 wd:Q1952 wd:Q1926 wd:Q1965 wd:Q13575 wd:Q2003 wd:Q2023 }
    ?hq wdt:P131* ?province .
    ?province rdfs:label ?provinceLabelRaw . FILTER(LANG(?provinceLabelRaw) = "en")
  }
  BIND(COALESCE(?provinceLabelRaw, "Unknown") AS ?provinceLabel)
}
GROUP BY ?industryLabel ?provinceLabel
ORDER BY DESC(?count)
```

Wikidata IDs used: `Q16` Canada, `Q4830453` business, `P31` instance of, `P279` subclass of, `P159` headquarters location, `P17` country, `P749` parent organization, `P127` owned by, `P452` industry, `P131` located in the administrative territorial entity. The 13 province/territory QIDs (`Q1904` Ontario, `Q176` Quebec, `Q1974` British Columbia, `Q1951` Alberta, `Q1948` Manitoba, `Q1989` Saskatchewan, `Q13603` Nova Scotia, `Q1952` New Brunswick, `Q1926` Newfoundland and Labrador, `Q1965` Prince Edward Island, `Q13575` Northwest Territories, `Q2003` Yukon, `Q2023` Nunavut) were selected from training knowledge, not live-verified — a live `curl` to `query.wikidata.org` was denied outright at this session's sandbox layer before ever reaching the network, consistent with every prior nightly build's documented egress constraint. This is a build-environment limitation per `CLAUDE.md`, not a redesign signal; the query is written against Wikidata's stable, documented property/entity model and the fetch layer surfaces the endpoint's own error text verbatim on any non-2xx or malformed response rather than assuming the query is correct.

**Parsed row shape** (`src/sparql.js#parseResults()` output): `{ industry: string, province: string, count: number }[]`

**localStorage snapshot** (`dominion-index:last-snapshot`): `{ fetchedAt: ISO string, industryTotals: {[name]: count}, provinceTotals: {[name]: count} }`

## Folder Structure

```
builds/2026-09-10-dominion-index/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── package-lock.json
├── playwright.config.js
├── index.html
├── src/
│   ├── style.css
│   ├── sparql.js       — query builder + SPARQL JSON result parser (pure functions)
│   ├── aggregate.js     — industry/province totals, top-N, delta-vs-snapshot computation (pure functions)
│   ├── snapshot.js      — localStorage read/write for the last-visit snapshot (pure functions, storage injected)
│   ├── render.js        — DOM rendering (charts, table, CSV export) — all text via textContent, never innerHTML on external data
│   └── app.js           — wires fetch → parse → aggregate → render, loading/error states
├── fixtures/
│   └── sparql-response.json  — a realistic sample Wikidata SPARQL JSON response used by both tests and local manual testing
└── tests/
    ├── sparql.spec.js
    ├── aggregate.spec.js
    ├── snapshot.spec.js
    ├── render.spec.js
    └── app.spec.js
```

## Testing Strategy

- **Unit-style tests** (`sparql.spec.js`, `aggregate.spec.js`, `snapshot.spec.js`) run in a Playwright browser context but call the plain `<script>`-loaded functions directly — no DOM interaction, no network. Cover: query string contains every required triple pattern/entity ID; parser handles a normal multi-row response, an empty `bindings` array, a response missing the optional label bindings, and a malformed/non-SPARQL JSON body (throws a typed error rather than crashing); aggregation produces correct top-N ordering, tie-breaking, percentage math, and "Unclassified"/"Unknown" bucketing against hand-computed fixture numbers; delta computation correctly classifies increase/decrease/unchanged/new/removed against a fixture snapshot; snapshot read/write round-trips through a fake storage object and degrades gracefully when storage throws (private-browsing mode).
- **Integration tests** (`render.spec.js`, `app.spec.js`) load `index.html` from a local static file server (required for reliable `localStorage` behavior under Playwright, per the pattern used by prior builds in this catalog — the shipped app still opens via `file://` for the user) and mock `query.wikidata.org` with `page.route`, supplying `fixtures/sparql-response.json` or deliberately broken responses. Cover: happy-path render (charts drawn, table populated, delta badges shown on a second fetch), empty-result state, HTTP-error state (endpoint returns 500 with plain-text timeout body — verbatim text shown), malformed-JSON state, network-failure state (route aborts — CORS/network guidance text shown), CSV export content and escaping, a dedicated XSS-payload fixture (industry/province label containing `<img onerror>` / `</script><script>`) confirming zero injected DOM nodes and zero `innerHTML` usage in the source, theme toggle, mobile viewport, and table sort/filter interactions.
- Minimum 15 tests; target is higher given the aggregation and delta logic each have several edge cases worth a dedicated test.
- Run with `npx playwright test` from the build folder.

## Success Criteria

1. The SPARQL query builder produces a query containing the headquarters-country check and the parent-organization exclusion (not a naive `P17 = Canada` filter) — verified by a test asserting on the query string.
2. Given a realistic mocked Wikidata response, the dashboard renders an industry chart, a province chart, and a full triple table with correct totals — verified against hand-computed fixture numbers, not just "a chart appeared."
3. Every failure mode (HTTP error, malformed JSON, network/CORS failure, empty result set) shows distinct, specific on-screen text — never a silent blank screen and never fabricated data standing in for a failed fetch.
4. A second successful fetch (simulating a return visit) shows correct up/down/new/gone delta badges against the first fetch's `localStorage` snapshot.
5. All tests pass (`npx playwright test`), and a dedicated XSS-payload test confirms external Wikidata label text is never inserted via `innerHTML`.

## Scope Changes

None — this PRD was written before any code and the build was completed to the scope above without reduction.
