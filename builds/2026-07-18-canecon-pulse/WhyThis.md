# Why This? — CanEcon Pulse

> **Date:** 2026-07-18

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day of year 199, `(199-1) % 9 = 0`) is A — Dashboard / Visualizer. Three pending Category A backlog ideas existed (#3 Lab Research Project Tracker, #5 GitHub Repository Health Scorecard, #6 Open-Meteo Activity Planner). One had a numeric rating (#3, rated 4), so R = 1 and `lottery_chance = min(75, 25 + 1*2) = 27%`. A random roll of 78 (via `$RANDOM`) exceeded 27, so the fresh-idea path was taken instead of the lottery draw. Pool size at roll time: 3 pending ideas.

## The Decision

Before generating ideas, I ran the required topic-diversity check on the last 10 builds. Category A specifically has already produced three GitHub-repo-analytics dashboards (2026-06-21 GitHub Repository Health Scorecard, 6/10 — "overlaps with GitHub's own Insights views"; 2026-06-30 GitHub Developer Analytics Dashboard; 2026-07-09 Pipeline Pulse) and two investment/watchlist dashboards (2026-06-10, complete; 2026-06-12, discarded as "near-duplicate... marginal rendering differences"). Both of the pending backlog ideas for tonight (#5 GitHub Health Scorecard, #6 Open-Meteo Activity Planner) would have re-trodden already-covered ground — #5 is functionally identical to the already-built 2026-06-21 build, and #6 overlaps heavily with the already-built 2026-06-20 Run Planner's Open-Meteo activity-comfort scoring. Rather than draw from a backlog whose Category A entries are stale duplicates, I generated fresh ideas and chose CanEcon Pulse — a dashboard over live Bank of Canada + Statistics Canada public economic data, a domain never touched by any prior build in the catalog.

## Connection to User Context

PROFILE.md names "Canadian economic policy" directly under topics the user reads about and follows, and The Canada List — the user's consumer-advocacy platform for Canadian-owned and Canadian-made products — is listed as an active personal project with real (if not build-container-accessible) data needs. CanEcon Pulse gives a standing, always-current view of the exact macro indicators (CAD/USD exchange rate, the policy interest rate, CPI, unemployment) that shape the real economic argument for buying Canadian-made over imported goods — directly useful context for Canada List editorial work, not just an investing-interest toy.

## Why Tonight

Category A comes up once per 9-day rotation; today's roll landed there. The last Category A build (Pipeline Pulse, 2026-07-09) was a meta-dashboard about this repo's own build backlog, not a domain dashboard, so there was no immediate risk of back-to-back repetition. No prior build in the 37-entry catalog uses Bank of Canada or Statistics Canada data, making this the first build to act on the "Canadian government open data" data source PROFILE.md lists as available with no credentials.

## What I Hope the User Gets From This

1. A faster way to check "where do rates/CPI/the loonie stand right now" than opening the Bank of Canada or StatsCan websites directly.
2. Grounded economic context to draw on for Canada List editorial writing about the cost tradeoffs of buying Canadian.
3. A local history that gets more valuable every time it's run — the trend charts are only as rich as the accumulated `sync` history, which rewards making it a recurring habit (or, per FutureFeatures.md, a Routine).

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| SEC EDGAR Insider Trading Radar | A | Category A has already produced two investment/watchlist dashboards, one of which was explicitly discarded as a near-duplicate (2026-06-12, rated 3/10). Repeating that pattern a third time risks the same critique without a clearly differentiating angle. Added to `builds/ideas.md` as #28 in case a sharper angle emerges later. |
| Research Pipeline Health Dashboard (NIH RePORTER × PubMed cross-reference) | A | Would re-fetch data very close in spirit to two builds from the last 6 nights (GrantScope, 2026-07-14; PubMed Research Radar, 2026-07-02), risking the "another external feed" pattern the Connectome build's own rationale explicitly called out as a weakness to avoid repeating. Added to `builds/ideas.md` as #29 for later, with more distance from both builds. |
| Backlog #5 — GitHub Repository Health Scorecard | A | Present in the pending backlog, but functionally near-identical to the already-built and already-rated 2026-06-21 build of the same name (6/10). Not drawn because the fresh-idea path was rolled, and would not have been a good draw regardless. |
