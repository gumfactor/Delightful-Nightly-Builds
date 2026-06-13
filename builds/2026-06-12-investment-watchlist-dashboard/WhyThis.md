# Why This? — Investment Watchlist Dashboard

> **Date:** 2026-06-12

---

## How This Idea Was Selected

**Selection method:** Fresh generation

Tonight's category was A (Dashboard/Visualizer). The lottery pool for Category A was filtered to focused and solid complexity — backlog IDs 2 and 3 are both A/ambitious and ineligible on a Solid Feature night. Filtered pool was empty, so the lottery was skipped. A random roll of 73 exceeded the 25% lottery threshold, confirming fresh generation regardless.

Three candidate ideas were generated in Category A at Solid complexity. Non-winners were appended to builds/ideas.md.

## The Decision

Friday is a Solid Feature night. Category A (Dashboard/Visualizer) had not been used yet across all three previous builds (B, H, F). Among the three candidates, Investment Watchlist Dashboard scored highest on genuine daily utility and real-data connectivity — it fetches live prices from Yahoo Finance (a data source explicitly listed in PROFILE.md) without any credential setup, and delivers immediate value the first time it runs without requiring the user to populate or configure anything beyond a JSON file of tickers.

## Connection to User Context

The user explicitly lists "Personal quantitative investing research and automation" as an active project and uses Interactive Brokers daily. PROFILE.md names Yahoo Finance as a preferred data source with no credentials required. The user's stated top value for builds is "things that save real time" — a single command that pulls a current watchlist snapshot replaces the friction of opening a browser, navigating to a financial site, and checking each ticker manually.

## Why Tonight

Category A has not been used in the repo's history. Friday is a Solid Feature night, and a multi-component Python tool (data fetching → processing → HTML rendering) is squarely in solid complexity territory. The build is complete and immediately useful as delivered — no deferred prerequisites.

## What I Hope the User Gets From This

1. A morning habit: `python3 main.py` → open `dashboard.html` → scan the watchlist in under 30 seconds
2. A pattern they can extend: the watchlist.json and data model are clean enough to add new tickers or fields with minimal effort
3. Confidence that a nightly build can integrate real financial data cleanly without overengineering

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| GitHub Repository Activity Dashboard | A/H | Useful, but the user already has GitHub's built-in insights. Lower marginal value than investment data, which has no native dashboard in their current stack. |
| Open-Meteo Weather & Wellness Dashboard | A | Weather data is nice to look at but doesn't directly affect the user's work or decisions in a meaningful daily way. Lower on the "saves real time" axis. |
