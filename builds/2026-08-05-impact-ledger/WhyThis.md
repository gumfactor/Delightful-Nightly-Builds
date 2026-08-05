# Why This? — Impact Ledger

> **Date:** 2026-08-05

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day-of-year rotation (day 217 of 2026 → category_index = (217-1) % 9 = 0 → Category A, Dashboard/Visualizer). The Category A backlog held 3 pending rows after excluding the one marked `skipped`: ID 3 (Lab Research Project Tracker, rating 4), ID 5 (GitHub Repository Health Scorecard — a verbatim duplicate of the already-built 2026-06-21 build, previously encountered and overridden on 2026-07-27's SiliconWatch), and ID 6 (Open-Meteo Activity Planner, unrated). Only ID 3 has a numeric rating, so R = 1 and lottery_chance = min(75, 25 + 1×2) = 27%. Rolled 100 (1–100) — above the 27% threshold, so fresh ideas were generated instead of a draw.

## The Decision

Rather than build another GitHub-activity dashboard (already covered three times: GitHub Repository Health Scorecard, GitHub Developer Activity Explorer, GitHub Developer Analytics Dashboard) or risk re-building the stale duplicate sitting in the backlog, I generated three fresh Category A candidates and picked the one most directly tied to a named, unaddressed friction point in PROFILE.md: research impact tracking for grant and manuscript writing. It uses a genuinely new, free, no-auth public API (OpenAlex) that no prior build touches, and gives the dashboard category something it hasn't had yet — a tool that tracks *the user's own scholarly output* over time rather than GitHub repos, markets, or Canadian macro data.

## Connection to User Context

PROFILE.md explicitly names "Grant writing," "write grants and manuscripts," and "Literature reviews" as recurring friction points and as things done manually that could be automated. Citing up-to-date impact statements ("this paper has been cited N times, and citations are accelerating") is a concrete, recurring task in that workflow that currently requires manually re-checking Google Scholar or OpenAlex before every grant deadline — exactly the "reduce friction, preserve context" framing from PROFILE.md's opening paragraph.

## Why Tonight

Category A came up in tonight's 9-day rotation. The backlog lottery missed (roll 100 vs. 27% chance), which is what triggered fresh generation rather than a draw. This is also the first build in the catalog to use the OpenAlex API, and the first Category A build oriented around the user's own academic output rather than infrastructure, markets, or macro data — a genuine gap after 9 prior Category A builds, all either GitHub-metrics or investing/macro dashboards.

## What I Hope the User Gets From This

1. A quick, evidence-backed way to answer "what's my most-cited recent paper, and is anything picking up momentum right now?" without manually checking Google Scholar/OpenAlex.
2. A real accumulating history — each time the tool is run (say, monthly, or before a grant deadline), citation growth becomes genuinely visible, not just a single snapshot.
3. A concrete building block toward the "book on Stress and Coping" and public-education goals, since the same citation/impact data is useful supporting material for both grant narratives and public-facing writing about the research's reach.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| AI Model Release Radar (Hugging Face Hub API tracking new LLM/agentic-AI model releases and trending models) | A | Genuinely novel and ties to the named "Agentic AI systems and workflows" and "AI infrastructure" rabbit holes, but is a passive news-watching tool with no clear recurring action the user takes on it — weaker "things that save me real time" fit than a tool tied to a concrete recurring task (grant writing). Kept as a backlog idea for a future build. |
| Canadian Sector Ownership Dashboard (Bank of Canada + StatsCan + Wikidata, macro-level Canadian vs. foreign ownership by sector) | A | Directly relevant to The Canada List, but CanEcon Pulse (2026-07-18) already occupies the "Canadian macro dashboard" shape in Category A, and this would read as a close sibling rather than a clearly distinct build. Kept as a backlog idea to revisit once it can be scoped more distinctly from CanEcon Pulse. |
| IBKR live portfolio/P&L dashboard (via local TWS/IB Gateway, credentials confirmed in PROFILE.md) | A | Genuinely different from the existing watchlist-style investing builds (real holdings/P&L vs. public price data), but TWS's own interface already surfaces exactly this information, risking the same "duplicates functionality already in the user's tools" critique that has sunk prior builds (Morning Briefing, 5/10). Also cannot be exercised at all without a running local TWS instance, making it harder to verify end-to-end tonight. |
