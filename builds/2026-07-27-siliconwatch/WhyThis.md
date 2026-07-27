# Why This? — SiliconWatch

> **Date:** 2026-07-27

---

## How This Idea Was Selected

**Selection method:** Fresh generation, after overriding a lottery draw.

Day of year 208 → `(208-1) % 9 = 0` → Category A (Dashboard/Visualizer). Three pending Category A backlog rows existed (#3 Lab Research Project Tracker, rating 4; #5 GitHub Repository Health Scorecard, blank; #6 Open-Meteo Activity Planner, blank), so `R = 1` (only one has a numeric rating) and `lottery_chance = min(75, 25 + 1*2) = 27%`. A roll of 26 (≤27) triggered a draw. Weighted by tickets (rating, blank = 5 → pool of 4+5+5=14), the draw rolled 7 of 14 and selected idea #5, "GitHub Repository Health Scorecard."

That idea is a verbatim duplicate of the already-built, already-rated 2026-06-21 build of the identical title and concept (GITHUB_TOKEN → per-repo health score → HTML dashboard), which scored 6/10 with a specific, already-recorded critique. Building it again would deliver zero new value and directly contradicts CLAUDE.md's calibration note about duplicate functionality being a proven failure pattern. Idea #6 has the same problem — it duplicates the 2026-06-20 Run Planner's Open-Meteo run/golf/boat scoring. I marked both `skipped` in `builds/ideas.md` with the rationale on record, and proceeded to fresh idea generation instead, per the spirit (if not the literal mechanics) of Step 2c/2d — the lottery mechanism exists to surface valuable backlog ideas, not to force a rebuild of something already shipped and rated.

## The Decision

With the draw pool disqualified, I generated three fresh Category A candidates and applied the topic-diversity check against the last 10 builds (2026-07-16 through 2026-07-26). Canada-related topics (CanEcon Pulse, CanFile) and academic-research topics (Protocol Forge, Bridgework, Bayes Lab) had each appeared multiple times in that window, so I ruled out a third Canada-data dashboard and a citation-tracker dashboard in favor of SiliconWatch, which touches a named profile interest with zero prior builds and fits Category A's ambition floor (a real visual dashboard, not a script that prints to stdout).

## Connection to User Context

PROFILE.md names "AI infrastructure and semiconductors" directly under "Topics you read about, follow, or find yourself going down rabbit holes on" — a rabbit-hole topic that, after 45 builds, had never been directly targeted. It also sits at the intersection of two other named interests: quantitative investing and the AI/research work that defines the user's day job. Every prior investment-flavored build (Investment Research Platform, Investment Thesis Journal, GitHub-based dashboards) was either generic-portfolio or developer-analytics in nature; none did sector-comparative analysis of the specific companies building the AI compute stack.

## Why Tonight

Category A comes up on a fixed 9-day rotation; today was its turn. No build in the 45-entry catalog has covered semiconductor/AI-infrastructure companies specifically, and the profile-interest gap made it a stronger fresh-generation candidate than either Canada-data or academic-citation alternatives once the topic-diversity check ruled those out for over-saturation.

## What I Hope the User Gets From This

1. A single dashboard to check on the specific companies (Nvidia, TSMC, ASML, etc.) behind a topic he already reads about, instead of clicking through six ticker pages
2. A sector-level lens — margin and valuation comparison across GPU/foundry/equipment/memory sub-segments — that no generic portfolio tracker gives him
3. A trend that compounds: re-running `sync` weekly builds a real multi-week valuation/margin history, not just a snapshot

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|-----------------|
| Canadian Manufacturing Sector Health Dashboard (StatsCan open data) | A | Canada-related topics already appeared twice in the last 10 builds (CanEcon Pulse, CanFile) — would push a third within the same window while a genuinely uncovered interest was available |
| Lab & Grad Student Citation Impact Tracker (Crossref/OpenAlex) | A | Academic-research domain already saturated in the last 10 builds (Protocol Forge, Bridgework, Bayes Lab) — appended to the backlog to revisit once that domain cools |
| GitHub Repository Health Scorecard (backlog #5, lottery winner) | A | Verbatim duplicate of the already-built and already-rated 2026-06-21 build; zero differentiation |
