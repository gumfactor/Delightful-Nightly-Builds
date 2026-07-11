# Why This? — Ledger Lens

> **Date:** 2026-07-08

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 189 → `category_index = (189-1) % 9 = 8` → Category I — Life Admin Helper. The `builds/ideas.md` backlog (resynced from the most recent open PR branch, `claude/cool-sagan-lonk43`, which carries the catalog through 2026-07-07) has zero pending rows tagged Category I — every I-category slot in the backlog is either absent or already built (Run Planner 06-20, Project Pulse 06-29). With an empty filtered pool, the lottery step is skipped entirely and generation goes straight to fresh ideas (Step 2d), so no random roll was made tonight.

## The Decision

Three fresh Life Admin Helper candidates were generated: (1) Ledger Lens — a bank-CSV-import spending categorizer and budget dashboard, (2) a manual-entry grant/conference deadline cockpit with AI task breakdown, (3) a weather-driven trip-packing checklist generator built on Open-Meteo. Ledger Lens won because it most closely follows the architecture of this catalog's highest-rated build to date (Qualtrics Survey Data Inspector, 9/10): ingest a real user-owned file, run substantive computation on it, and produce a genuinely new report — rather than requiring the user to type data in by hand (the failure mode that sank AI Session Context Bridge, 3/10, and the deadline-cockpit alternative). "Budget tracker" is also one of the category's own canonical examples in CLAUDE.md, so this isn't a stretch interpretation of Life Admin Helper.

## Connection to User Context

PROFILE.md lists Interactive Brokers as the only financial tool in the daily stack — investing, not spending. Nothing in "Tools and environments you use daily" covers budgeting or expense tracking, and "Domains where a personal tool would add the most value" explicitly names "Personal productivity and project coordination." Running a lab, a consumer platform (The Canada List), and personal investing simultaneously (per "Active work projects") means expense visibility across those overlapping financial lives is exactly the kind of administrative overhead the profile calls out as a recurring friction point.

## Why Tonight

Tonight is purely a category-rotation night (index 8 → I), not a follow-up to a specific prior build. It is the third Life Admin Helper build in the catalog (after Run Planner and Project Pulse), and deliberately picks a topic domain — personal finance/spending — that hasn't appeared in the last 10 builds, keeping topic diversity within the category rotation as instructed.

## What I Hope the User Gets From This

1. A five-minute answer to "where did my money actually go last month," without opening a spreadsheet
2. Automatic surfacing of forgotten recurring subscriptions — the specific failure mode budgeting apps are best at catching and manual review is worst at
3. A tool that works completely offline (rule-based categorization, deterministic insights) but gets measurably smarter the moment an `ANTHROPIC_API_KEY` is added — no rebuild required

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Grant/Conference Deadline Cockpit with AI task breakdown | I | Core data (deadlines) has no live source and must be typed in by hand each time — the same manual-entry pattern that scored AI Session Context Bridge 3/10 and Investment Research Notes 2/10 in this catalog. |
| Weather-Driven Trip Packing Checklist (Open-Meteo + Claude) | I | Real data and a genuine AI layer, but overlaps functionally with the existing Run Planner build's weather-scoring logic, and "what to pack" is a lower-stakes problem than "where is my money going" for a user managing multiple concurrent ventures. |
| Habit/Streak Tracker | I | No live data source available (no Garmin/MyFitnessPal credentials in PROFILE.md's Data Sources), would end up as a bare manual-entry checklist with no real differentiation from any generic habit app. |
