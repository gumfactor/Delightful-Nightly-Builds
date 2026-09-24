# Manual — Corporate Ownership Chain Explorer

## What it is
A single-page browser tool: search a company, see who owns it (walking up the chain) and what it owns (its known subsidiaries), each link sourced live from Wikidata with a direct citation to the exact statement it came from.

## How to run it
No build step, no server, no install required to use it.

1. Open `index.html` directly in a browser (double-click it, or `file://` + the full path). It works from `file://` because it uses classic `<script>` tags, not ES modules.
2. Type a company name into the search box. Results appear after a short pause (debounced, ~300ms) as you stop typing.
3. Click a result to make it the focus company. Its ownership chain ("Owned by") and known subsidiaries load automatically.
4. Click any name in either chain to drill into that company — the explorer re-centers on it and the breadcrumb at the top grows.
5. Click an earlier name in the breadcrumb to jump back.
6. Click "source ↗" next to any ownership link to open the exact Wikidata statement it came from, where you can inspect the underlying reference Wikidata records for it.
7. "Recent searches" (bottom of the page) remembers your last 10 focus companies across visits, stored only in your browser (`localStorage`) — nothing is sent anywhere except to Wikidata's own public APIs.

## Requirements
- An internet connection (it calls `query.wikidata.org` and `www.wikidata.org` directly — both free, public, no API key or account needed).
- Any modern browser. No Node.js, Python, or install step needed to *use* it.

## Running the tests (for development)
```bash
cd builds/2026-09-24-corporate-ownership-explorer
npm install
npx playwright test
```
37 tests, all should pass. `npm install` only needs to run once (it pulls in `@playwright/test`; the app itself has zero runtime dependencies).

## Reading the results
- **"Owned by"** panel: the upward chain from the focus company to its ultimate known parent, one hop per Wikidata `owned by` (P127) or `parent organization` (P749) statement. Stops when Wikidata records no further parent, when it detects an ownership loop (rare bad data), or after 8 hops.
- **"Subsidiaries"** panel: companies that list the focus company as their owner/parent, plus anything the focus company lists as a `subsidiary` (P355). This is one hop only — click a subsidiary to see *its* subsidiaries.
- A blank panel with "No ownership data recorded on Wikidata for this company" means exactly that — Wikidata doesn't have the relationship recorded, not that the company has no owner in reality. Treat every result as a starting point for verification, not a final answer — that's exactly why every edge links back to its source.
- A qualifier like "(as of 2020)" or "(2015–2019)" means Wikidata recorded *when* that ownership relationship held; ownership can and does change over time.

## Known limitations
- Wikidata's ownership data is incomplete and crowd-sourced. A missing result is common and expected, especially for smaller or private companies.
- The upward chain shows one "primary" parent per company even when Wikidata records more than one (e.g. joint ventures) — it prefers `owned by` over `parent organization`, then picks deterministically. The full picture in edge cases like that is only visible by following the citation link.
- No ownership *percentages* are shown — Wikidata rarely records these reliably.
