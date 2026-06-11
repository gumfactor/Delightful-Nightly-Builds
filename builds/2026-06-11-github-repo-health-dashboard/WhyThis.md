# Why This? — GitHub Repository Health Dashboard

> **Date:** 2026-06-11

---

## How This Idea Was Selected

**Selection method:** Fresh generation

Tonight's lottery was skipped: the backlog contains no ideas matching tonight's category (A — Dashboard/Visualizer) at the compatible complexity level (focused). All four backlog entries are tagged `ambitious`, which is ineligible on a Focused Utility night. A random roll of 90 was generated but was moot — the filtered pool was empty, so the process went directly to fresh idea generation.

## The Decision

Thursday = Focused Utility. Category A (Dashboard/Visualizer) was chosen because B, H, and F have all been covered in the last three builds. Three fresh ideas were evaluated; this one scored highest on "real data" and "novelty" — it uses `GITHUB_TOKEN` (always available in this environment) to connect to the user's actual repositories, and it does something GitHub.com does not: shows all repos on a single dashboard sorted by staleness with health labels, so the user can triage project health in one glance rather than navigating repo by repo.

## Connection to User Context

The user manages multiple simultaneous GitHub repositories across several active projects — The Canada List, Kwyeter, nightly build scripts, neuroscience lab tools, and personal experiments. One of their listed recurring friction points is "managing many simultaneous projects." This tool attacks that friction directly: one command shows which repos are active, which have accumulated issues, and which have gone quiet, without requiring the user to visit each one.

## Why Tonight

Category A (Dashboard/Visualizer) fills a gap in the rotation. The previous focused utilities (Git Standup Reporter and Quick Data Profiler) were category H and F; this is the first A build. Focused utility is the right complexity level for a clean, well-scoped CLI that does exactly one thing well.

## What I Hope the User Gets From This

1. A reliable "morning check" they can run alongside `git standup` to see which repos need their attention today.
2. A concrete answer to "which projects have I been ignoring?" — stale/quiet repos surface automatically.
3. A JSON output mode that can feed downstream scripts or a future dashboard build.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Stock Watchlist Morning Snapshot | A | The user already uses IBKR with real-time data; a 15-minute delayed yfinance watchlist adds less marginal value. The watchlist would also be a hardcoded list rather than connected to their actual portfolio positions. |
| Outdoor Activity Weather Planner | I | Genuinely useful (user runs, golfs, boats), but Open-Meteo weather data requires less personal connection — any weather app shows a 7-day forecast. The activity-scoring layer is novel but a weaker match to the user's ranked priorities (time savings, daily utility) than a tool connected to their actual GitHub work. |
