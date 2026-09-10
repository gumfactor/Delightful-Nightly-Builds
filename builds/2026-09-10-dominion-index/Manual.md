# Manual — Dominion Index

## Quick start

1. Open `index.html` directly in a browser (double-click it, or `open index.html` / drag it into a browser window). No server, no build step, no installation required.
2. The page immediately queries Wikidata's public SPARQL endpoint and renders the dashboard. This takes a few seconds — Wikidata aggregate queries over hundreds of thousands of entities are not instant.
3. Click **Refresh** any time to re-query. Click the 🌙/☀️ button to switch theme. Use the filter box or click a table column header to search/sort the results table. Click **Export CSV** to download the raw (industry, province, count) rows.

## What it shows

Two bar charts and a table: how many Wikidata-recorded, Canadian-owned companies fall into each industry (`P452`) and each province/territory (based on headquarters location). A second visit shows **+N / -N / new / gone** badges next to each industry and province, comparing against the last successful fetch (saved in your browser's `localStorage` — nothing is sent anywhere except the one Wikidata query itself).

## What "Canadian-owned" means here

This is a heuristic, not a legal or corporate-registry determination:

- A company counts if its **headquarters location** (`P159`) is itself located in Canada (`P17` = Canada) — not the company's own `P17`, which can just mean "incorporated in Canada" even for a foreign company's local subsidiary.
- A company is **excluded** if Wikidata records a parent organization (`P749`) or owner (`P127`) whose own country is asserted and is *not* Canada.
- A company with **no recorded parent/owner at all** is counted as Canadian-owned by default. Wikidata's ownership data is incomplete, so this can occasionally overcount a foreign subsidiary whose ownership link just isn't recorded on Wikidata. There is no way to distinguish "genuinely independent" from "ownership simply not documented" from public data alone.
- Companies with no `P452` industry statement are bucketed as **"Unclassified"**; companies whose headquarters can't be resolved to one of the 13 provinces/territories are bucketed as **"Unknown"**.

## Data source

[Wikidata Query Service](https://query.wikidata.org/sparql) — free, public, no authentication, no API key. The exact query is in `src/sparql.js` (`buildQuery()`) and documented in `PRD.md`. This is a community-editable database: coverage is uneven (large/notable companies are far better represented than small ones), and the totals shown reflect *what's on Wikidata*, not the true total number of Canadian-owned companies.

## Troubleshooting

- **"Could not reach the Wikidata SPARQL endpoint"** — some browsers restrict cross-origin `fetch()` requests from a page opened via `file://` (the page's origin is treated as `null`). If this happens, run a local static server from this folder and open the page through it instead, e.g.:
  ```
  python3 -m http.server 8000
  ```
  then open `http://localhost:8000`.
- **A Wikidata HTTP error or timeout message appears** — Wikidata's public query service occasionally times out on heavier aggregate queries, especially at peak hours. The on-screen message is Wikidata's own response text; just click Refresh to retry, ideally a little later.
- **The numbers look low compared to what you'd expect** — see "What Canadian-owned means here" above; this reflects Wikidata's own coverage, not an undercount bug.

## Known limitations

- Ownership determination is a heuristic (see above) and will occasionally misclassify a company either way.
- Province resolution depends on the company's headquarters being linked (directly or transitively via `P131`) to one of the 13 Wikidata province/territory entities; a headquarters recorded only at a city with no linked province falls into "Unknown".
- No historical trend beyond the single most-recent snapshot kept in `localStorage` — clearing browser storage resets the delta comparison to "everything is new."
- This build's Wikidata property IDs and the 13 province/territory QIDs were written from training knowledge, not live-verified against Wikidata during the build session (this build container has no route to the public internet — see `BUILD_LOG.md`). If Wikidata's schema for any of these properties has since changed, the on-screen error text from a failed/empty query will say so rather than showing wrong numbers silently.
