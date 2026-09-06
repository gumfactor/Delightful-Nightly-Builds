# Why This? — Almanac

> **Date:** 2026-09-06

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day-of-year 249 → index 5) is F — Data Explorer. The synced `builds/ideas.md` (pulled from the most recent open PR branch, `claude/cool-sagan-mltlo1`, since the local `main` checkout was weeks stale) had 5 pending Category F rows, all unrated (blank = 5 tickets each, R = 0 rated rows). Per the lottery formula, `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 92/100 — above the gate, so fresh ideas were generated instead of drawing from the backlog. Pool size at the gate: 5 (SEC EDGAR Financial History Extractor, Manuscript Citation Cross-Checker, StatsCan Canadian Business Data Explorer, SEC EDGAR Form 4 Insider Transaction Explorer, Wikipedia Pageview Trend Explorer for Canadian Companies).

## The Decision

Category F already has 8 prior builds, including two SEC EDGAR-flavored ones in the last two weeks (Trading Book 2026-08-23, EDGAR Lens 2026-08-28) — not saturated by the >2-in-last-10 rule, but close enough that a third finance build tonight risked feeling repetitive. Two of the five pending backlog rows are themselves SEC EDGAR variants, which reinforced steering away from that data source. Almanac instead targets an Open-Meteo data source that Category F has never used (Run Planner, Category I, only used Open-Meteo's 7-day *forecast* API for a comfort score — never the historical archive), and reuses the catalog's single highest-rated pattern to date: a deterministic, independently-verifiable statistics engine feeding an interactive dashboard (the 2026-06-17 Qualtrics Survey Data Inspector, 9/10, is the only rated build in the entire 83-build catalog scoring above 6).

## Connection to User Context

PROFILE.md names distance running, golf, boating, and "cottage life" directly under Personal interests and hobbies — a genuinely untouched cluster across 83 builds (Run Planner touches running/golf/boating only as a 7-day forward planner, not a historical explorer). Almanac answers a different, evidence-driven question PROFILE.md's own "highly analytical and evidence-driven" self-description points at: not "what's the forecast this week" but "how often does this actually happen here" — e.g. what fraction of July days at the cottage are actually boating-calm, or how heat-wave-prone golf season has become over the fetched years.

## Why Tonight

Category F, chosen by the fixed 9-day rotation for day-of-year 249. No direct follow-up to a specific prior build, but it deliberately avoids repeating EDGAR Lens's and Trading Book's finance-data mechanic from the immediately preceding two-plus weeks, and fills a data-source gap (Open-Meteo's historical archive) that's been sitting unused since Run Planner only touched the forecast endpoint.

## What I Hope the User Gets From This

1. A real answer to "is [location] actually good for golf/running/boating in [month]?" backed by real multi-year data, not a single week's forecast or gut feel
2. A concrete, checkable extreme-event count (heat waves, cold snaps, heavy-rain days, high-wind days) for planning around risk, not just averages
3. A reusable tool for any location — Toronto for daily life, a cottage-country town for boating season planning, a destination for travel timing — not a single hardcoded place

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Wikipedia Pageview Trend Explorer for Canadian companies (interest-signal over time for The Canada List) | F | The Canada List domain already has 4 prior builds across the catalog (CanFile, Ingest Gate, Provenance, Maple Press); pageview-as-proxy-signal is also a weaker, less verifiable core than Almanac's directly-measured climate statistics. Left as-is in the backlog (idea #31) for a future night. |
| SEC EDGAR Full-Text Search risk-factor keyword explorer | F | Would have been the third SEC EDGAR-shaped Category F build in three weeks (after EDGAR Lens, plus two pending EDGAR backlog rows) — too close a mechanic repeat on the same data source. |
| NIH RePORTER institution/investigator collaboration explorer | F | Near-duplicate data source to the already-built GrantScope (2026-07-14), which already queries NIH RePORTER for funded-project landscapes; not enough differentiation to justify a second build on the same API. |
