# Why This? — Ingest Gate: CSV Quality Inspector for The Canada List

> **Date:** 2026-08-10

---

## How This Idea Was Selected

**Selection method:** Lottery draw from `builds/ideas.md`.

Tonight's category (day of year 222, `(222-1) % 9 = 5`) is **F — Data Explorer**. The category-F backlog held two pending rows: ID 1 (The Canada List CSV Quality Inspector, rated 7 → 7 tickets) and ID 10 (SEC EDGAR Financial History Extractor, unrated → 5 tickets). With one rated idea in the pool, `R = 1`, so `lottery_chance = min(75, 25 + 1*2) = 27%`. A roll of 9 (≤27) triggered a draw; a weighted roll of 5 out of 12 total tickets landed inside ID 1's 1–7 range, so ID 1 won.

## The Decision

This was a lottery draw, not a fresh idea, so the category-diversity and topic-saturation checks in CLAUDE.md Step 2d don't apply — but it's worth noting this build still lands on a genuinely untouched topic (The Canada List's data pipeline) rather than repeating the GitHub-metrics or markets/macro shapes that dominate the recent catalog. The idea's own rating note flagged uncertainty about "what role Playwright plays here vs. a pure Python validator" — resolved by building it as a real browser tool (drag-drop upload, live dashboard, downloadable cleaned CSV) rather than a CLI, which also satisfies Category F's hard ambition-floor requirement for a visual/interactive interface.

## Connection to User Context

PROFILE.md names **The Canada List** as an active personal project — "a large-scale Canadian business and product directory" involving "large-scale data collection and curation... automation pipelines" — and explicitly lists "The Canada List ingestion and quality control pipeline" under "Things you do manually that you suspect could be automated or aided by a tool." This build targets that exact friction point directly, and it is the **first build in the entire catalog to target The Canada List** (CanFile, 2026-07-20, touched Canadian ownership *lookups* for individual companies; this build is squarely about the operator's own bulk CSV ingestion workflow, a different part of the pipeline).

## Why Tonight

No direct dependency on a previous build — this is a fresh area of the catalog. It does deliberately avoid CanFile's shape (per-company Wikidata lookups) by focusing on the bulk-CSV QC step that happens before any per-company enrichment would even run.

## What I Hope the User Gets From This

1. A tool they can drop a real Canada List CSV export into tonight and get an honest read on how clean it actually is, with zero setup
2. A reusable schema they configure once (matching their actual pipeline's real column names) and reuse on every future export, saved locally in the browser
3. Confidence that bad data — malformed rows, duplicate listings, broken URLs — gets caught before it reaches the live directory, rather than surfacing as a support ticket or a bad search result later

## Alternatives Considered

Since this was a lottery draw (not fresh generation), the only real alternative was the other pool member:

| Idea | Category | Why Not Chosen |
|------|----------|-----------------|
| SEC EDGAR Financial History Extractor (backlog #10) | F | Lost the weighted draw (5/12 chance vs. 7/12) — also would have been the catalog's third build touching public-market financial data in the last 10 builds (Portfolio Lab, SiliconWatch), while The Canada List had zero prior builds despite being a named active project |
