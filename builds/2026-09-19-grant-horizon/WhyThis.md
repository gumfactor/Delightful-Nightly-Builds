# Why This? — Grant Horizon

> **Date:** 2026-09-19

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 262 → `category_index = (262-1) % 9 = 0` → Category A — Dashboard/Visualizer. Four pending Category A backlog rows existed (#3 Lab Research Project Tracker, rated 4; #6 Open-Meteo Activity Planner, unrated; #26 Research Pulse, unrated; #27 Canada List Business Density Dashboard, unrated). `R` = 1 (only #3 has a numeric rating), so `lottery_chance = min(75, 25 + 1*2) = 27%`. Rolled 90 (`python3 -c "import random; print(random.randint(1,100))"`) → 90 > 27, routing to fresh generation per Step 2d.

## The Decision

Scanned the last 10 builds' topic domains before generating ideas: investment/finance appeared once (Rotation Radar, F, 09-15), GitHub/dev-tooling once (Secrets Sentinel, H, 09-08), Canada List once (Dominion Index, A, 09-10) — none saturated. Scanned all 13 prior Category A builds specifically for domain overlap: GitHub/repo analytics (4 builds), investment/finance (2), Canada List (2), academic-citation-impact (1), ambient-sound/Kwyeter (1), Canadian macroeconomics (1). Generated three fresh Category A candidates and picked the strongest — see Alternatives Considered.

## Connection to User Context

PROFILE.md names "Grant writing" verbatim under "Things you do manually that you suspect could be automated or aided by a tool," ranks "Academic research" among the domains where a personal tool adds the most value, and states the user runs a "forensic and affective neuroscience lab" studying "empathy, psychopathy, and stress research." No prior build (across all 9 categories, 95 builds) touches federal grant-funding intelligence — the closest is 2026-09-18's Eligible Spend, which checks an already-awarded Tri-Agency budget for compliance, not the pre-award competitive landscape a grant writer needs to justify novelty and identify comparable funded work.

## Why Tonight

Pure category rotation — tonight is Category A's slot in the 9-day cycle, and the topic-diversity check ruled out re-treading GitHub/dev-tooling, investment/finance, or Canada List ground that recent Category A nights already covered.

## What I Hope the User Gets From This

1. A concrete before-a-grant-submission step: search the live NIH-funded project landscape for the specific subfields this lab works in, see who else is funded and how much, and cite the real gap instead of an assumed one.
2. A reusable local dataset (SQLite) that grows more valuable each time `sync` is re-run before a new submission cycle, rather than a one-off report.
3. A concrete demonstration of the "AI as differentiating layer, strictly grounded in fetched data, PI names never in the prompt" pattern this catalog has been refining — useful as a reference for future grant/research-admin builds.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Marine/Cottage Conditions Dashboard — live water-level and marine-buoy data (Environment and Climate Change Canada Hydrometric API / NOAA) scored for boating readiness, tied to PROFILE.md's named "boating, cottage life" hobby | A | Real live-data angle and genuinely novel domain for the catalog, but the underlying value (a boating-conditions check) is a nice-to-have hobby tool, not a named friction point — PROFILE.md ranks "things that save me real time" and "tools I'll use daily/weekly" above "fun/delightful," and grant writing scores higher on both. Worth building on a future Category A or I night, especially once boating season framing matters again. |
| Canada List Trending-Interest Tracker — Wikimedia's free, no-auth pageviews REST API tracking week-over-week public interest in Canadian-owned brands already in The Canada List's dataset, distinct from Dominion Index's static ownership-composition count | A | A genuinely different data source and shape (time-series interest trend vs. aggregate count) from Dominion Index, but The Canada List already has 5 prior builds across the catalog (CanFile, Ingest Gate, Provenance, Maple Press, Dominion Index) — closer to the saturation line than a domain with zero prior Category A coverage. Logged to the backlog for a future night if the domain isn't further saturated by then. |
| PubMed Research Landscape Pulse — publication-volume trend for the user's specific subfields via PubMed E-utilities | A | Already effectively logged and passed over as backlog idea #26 (Research Pulse) for overlapping too closely with three existing literature-feed builds (Paper Lens, PubMed Research Radar, Impact Ledger); regenerating a near-identical idea wouldn't add anything the backlog note didn't already conclude. |
