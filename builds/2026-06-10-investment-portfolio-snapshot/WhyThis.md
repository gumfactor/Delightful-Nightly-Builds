# Why This? — Investment Portfolio Snapshot

> **Date:** 2026-06-10

---

## How This Idea Was Selected

**Selection method:** Fresh generation

Roll: 80. Lottery chance was 29% (2 rated ideas in the filtered Category A pool). 80 > 29 → fresh path.

Filtered pool for the lottery had 2 ideas (both Category A / ambitious): "Investment Research Dashboard" (ID 2, rating 6) and "Lab Research Project Tracker" (ID 3, rating 4). The lottery did not fire, so fresh ideas were generated independently.

## The Decision

Wednesday → Ambitious Project. Category A (Dashboard/Visualizer) was chosen as the rotation pick — the last three builds covered B (Productivity Utility), H (Developer Tool), and F (Data Explorer); A was the strongest unused category for an ambitious scope. Three fresh ideas were evaluated: Investment Portfolio Snapshot (winner), GitHub Repository Health Scorecard, and Open-Meteo Activity Planner. The investment snapshot scored highest on genuine daily usefulness and data availability.

## Connection to User Context

Investing is listed in PROFILE.md as a core personal interest and active project. The user has Interactive Brokers credentials and is building quantitative investing research workflows. Yahoo Finance (`yfinance`) is explicitly listed in PROFILE.md's Data Sources section as available with no credentials — a clear green light to connect real market data. The friction this addresses is named directly in PROFILE.md: the user currently does investment research aggregation manually. A one-command snapshot that surfaces price, trend, P/E, and 52-week range for a watchlist is something a quantitative researcher would reach for every morning.

## Why Tonight

Wednesday's ambitious target is well-matched to this build: it requires data fetching, normalization, chart generation (SVG sparklines), and HTML templating — multiple real components with real integration. The preference prior had insufficient signal (< 3 rated builds), so category and usefulness drove the decision. Category A had not been used in the build history at all; this is the first dashboard build.

## What I Hope the User Gets From This

1. A daily morning ritual: run one command, open one HTML file, get oriented on the market in 30 seconds.
2. A concrete foundation to extend — the watchlist is editable, the code is clean Python, and FutureFeatures.md maps the obvious next steps.
3. Confirmation that connecting to real data (Yahoo Finance) in nightly builds is worth doing — this is what the 2026-06-06 context bridge build was missing.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| GitHub Repository Health Scorecard | A | Real value, but the Git Standup Reporter (2026-06-07) already covers developer-activity ground; a repo health dashboard would feel like a sequel rather than something new |
| Open-Meteo Activity Planner | A | Weather apps already exist and do this well; the novelty bar isn't cleared — the user wouldn't choose this over a phone weather widget |
| Lab Research Project Tracker (backlog ID 3) | A | Explicitly rated 4 with note: "No need — already use Teamwork.com for project tracking"; drawing this from the backlog would ignore the user's own feedback |
