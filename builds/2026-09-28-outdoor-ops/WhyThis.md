# Why This? — Outdoor Ops

> **Date:** 2026-09-28

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year for 2026-09-28 is 271 → `category_index = (271-1) % 9 = 0` → **Category A — Dashboard / Visualizer**.

Before running the lottery, I found idea #5 in `builds/ideas.md` ("GitHub Repository Health Scorecard") was marked `pending` for Category A but had already been built verbatim on 2026-06-21 under that exact title. Corrected it to `skipped` with a note before drawing, so it couldn't be drawn as if new (same precedent as the duplicate correction logged in the 2026-09-25 Agent Relay build).

With that correction, the Category A pending pool held 2 eligible ideas: #3 "Lab Research Project Tracker" (rating 4) and #6 "Open-Meteo Activity Planner" (rating blank → 5 tickets default). Entries with a numeric rating: R = 1 (#3). `lottery_chance = min(75, 25 + 1*2) = 27%`. Rolled a random integer 1–100 → **54**. 54 > 27, so the lottery missed its gate and the night went to fresh idea generation instead of a draw.

## The Decision

Scanned the last 10 builds in `builds/index.md` for topic saturation: Eligible Spend, Grant Horizon, Counterpoint, Star Atlas, Wake Log, Pooling Lab, Corporate Ownership Chain Explorer, Agent Relay, Shiplog, Parity. No domain repeats more than twice (grant/funding appears twice — Grant Horizon, Eligible Spend — not saturated per the >2 rule). Within Category A specifically, the historical catalog already has two GitHub-API dashboards, three Canada List/Wikidata builds' worth of adjacent territory, two finance builds (SiliconWatch, Trading Book), a macro-econ build (CanEcon Pulse), and a research-citation build (Impact Ledger) — so a third GitHub or finance dashboard would be repeating an already-covered pattern rather than filling a gap.

Generated 3 fresh Category A candidates (full list and reasoning also in `builds/ideas.md` #15–16 for the two not chosen):
1. **Outdoor Ops** (chosen) — multi-activity outdoor-conditions dashboard.
2. **Breadth Compass** — sector-rotation/market-breadth dashboard (yfinance). Passed over: third finance-domain Category A build.
3. **Filing Pulse** — SEC EDGAR Form 4 insider-transaction dashboard. Passed over: same finance-saturation reason, plus higher data-parsing risk for a first pass.

Outdoor Ops won because it opens a genuinely new data source in this catalog (Open-Meteo's Air Quality API has never been used, only the plain forecast API has, in Wake Log) and ties directly to two named hobbies — distance running and golf — that have zero prior dedicated builds, versus adding a third entry to an already-covered finance pattern.

## Connection to User Context

PROFILE.md lists "distance running, golf, ... boating" under Physical activities and Personal interests, and Wake Log (2026-09-22) already covers boating/cottage days well. Running and golf are named but unaddressed. PROFILE.md also flags Garmin Connect as a daily tool but explicitly without a live API (CSV export only) — so a Garmin-based build isn't viable tonight (also the reason backlog idea #13 "Habit Streak Mirror" was passed over on 2026-09-27). Open-Meteo's forecast and air-quality endpoints are both free, no-auth, and already named in PROFILE.md's Data Sources, giving a genuinely live alternative to "plan your training/tee time around real conditions" without needing wearable data.

## Why Tonight

Category A comes up on the fixed 9-day rotation for day-of-year 271. No idea brief was linked to any candidate.

## What I Hope the User Gets From This

1. A daily/weekly glance at which day this week is actually good for a run or a round of golf, instead of checking a generic weather app and mentally converting conditions into a go/no-go call.
2. Visibility into air quality (never previously surfaced in any build) alongside wind, precipitation, and UV — all four matter for outdoor training decisions but are scattered across different apps today.
3. A small, honest example of turning a public API into a decision-support tool rather than just a data mirror — the suitability scores are a real, documented, testable model, not just a re-displayed forecast.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Breadth Compass — sector-rotation/market-breadth dashboard | A | Would be the third finance-domain Category A build (after SiliconWatch, Trading Book); logged as backlog idea #15 for a future night when finance in Category A isn't repetitive. |
| Filing Pulse — SEC EDGAR Form 4 insider-transaction dashboard | A | Same finance-saturation reason as Breadth Compass, plus real Form 4 XML parsing carries more edge-case risk than a first-pass Category A idea should take on; logged as backlog idea #16. |
| Lab Research Project Tracker (backlog #3, rating 4) | A | User's own rating note says "No need — already use Teamwork.com for project tracking" — directly contradicted by real usage, so left in the backlog rather than drawn or reproposed. |
