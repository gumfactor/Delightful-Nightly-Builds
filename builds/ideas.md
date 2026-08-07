# Build Idea Backlog

> **Claude:** Append the ideas you considered but didn't build after every fresh-idea session.
> Mark a drawn idea's Status as `built` when it gets selected for a build.
> **You:** Add a rating (1–10) and Rating Notes to any idea to influence its lottery weight and guide future builds.
> Leave the rating blank (—) to keep the default weight (5 tickets).
> Set Status to `skipped` on any idea you never want built.
> Add an Idea Brief when an idea needs richer requirements than fit in one table row.
> Linked briefs live in `builds/idea-briefs/` and must be read before the build PRD is written.

---

## How the Lottery Works

Claude selects tonight's **category** and **complexity target** first (from the rotation),
then filters this backlog to matching ideas before running the draw. Ideas that don't
match tonight's category or are too complex for tonight's target are skipped — if the
filtered pool is empty, Claude generates fresh ideas instead.

When a draw does happen, each matching idea's probability is proportional to its ticket count:

| Your Rating | Tickets in Draw |
|-------------|------------------|
| 1 | 1 — much less likely |
| 2–3 | 2–3 |
| — (blank) or 5 | 5 — default |
| 7–8 | 7–8 |
| 10 | 10 — most likely |

Tickets = Your Rating directly. Blank = 5 tickets.

If no pending ideas exist in the backlog, the lottery is skipped and Claude
always generates fresh ideas.

---

## Backlog

| ID | Date Added | Category | Complexity | Title | Description | Idea Brief | Your Rating | Rating Notes | Status |
|----|------------|----------|------------|-------|-------------|------------|-------------|--------------|--------|
| 1 | 2026-06-06 | F | ambitious | The Canada List CSV Quality Inspector | Browser-based tool to inspect and validate CSV uploads for The Canada List pipeline — flags malformed rows, missing required columns, encoding issues, and duplicate entries before ingestion | — | 7 | Could be very useful if implemented properly — unclear what role Playwright plays here vs. a pure Python validator | pending |
| 2 | 2026-06-06 | A | ambitious | Investment Research Dashboard | Comprehensive personal finance dashboard — portfolio tracking, watchlist, research notes, and performance over time; not just an investing-interest toy but a genuinely useful daily tool | — | 6 | Love the idea of a comprehensive investment dashboard, but not just for investing interest — that framing is less exciting | skipped |
| 3 | 2026-06-06 | A | ambitious | Lab Research Project Tracker | Dashboard for tracking neuroscience lab projects, milestones, team tasks, and publication status | — | 4 | No need — already use Teamwork.com for project tracking | pending |
| 4 | 2026-06-09 | B | ambitious | Cross-Agent Project Activity Workstreams | Automatically correlate Git, GitHub, and AI-agent activity into evidence-backed workstreams that can generate accurate standups, resumptions, handoffs, timelines, and decision histories across tools | [Brief](idea-briefs/cross-agent-project-activity-workstreams.md) | 9 | — | pending |
| 5 | 2026-06-10 | A | ambitious | GitHub Repository Health Scorecard | Python script using GITHUB_TOKEN to pull all user repos and generate an HTML health scorecard: last commit date, open issues/PRs, CI status, contributor count, and a health score per repo | — | — | — | pending |
| 6 | 2026-06-10 | A | ambitious | Open-Meteo Activity Planner | Vanilla HTML/JS dashboard pulling from Open-Meteo API for Toronto — 7-day forecast with activity suitability scores for running, golf, and boating; no auth required | — | — | — | pending |
| 7 | 2026-06-11 | B | focused | Morning Briefing | Unified daily digest that combines the Git Standup Reporter, Investment Portfolio Snapshot, and GitHub Repository Health Dashboard into a single morning report — commits from yesterday, portfolio overnight moves, and any repos that have gone quiet | — | 8 | — | pending |
| 8 | 2026-06-14 | A | ambitious | Investment Research Platform | Unified HTML report that merges live watchlist metrics (prices, sparklines, 52W range, P/E, analyst target) with thesis journal entries per ticker — showing the price when each thesis was written and the % move since, so you can evaluate your reasoning against outcomes at a glance. Builds on the Jun 10 Portfolio Snapshot as the base with the Jun 14 Thesis Journal's price-at-note logic integrated as a data layer. | — | 8 | Combines the two strongest investment builds into something with genuine daily utility — the accountability loop between thesis and outcome is the unique value | skipped |
| 9 | 2026-06-17 | H | ambitious | GitHub Actions Performance Analyzer | Uses GITHUB_TOKEN to fetch workflow run times across all repos and generate an HTML report identifying slow steps, frequent failures, and wasted CI minutes — with trend charts and per-job breakdown | — | — | — | pending |
| 10 | 2026-06-17 | F | ambitious | SEC EDGAR Financial History Extractor | Uses SEC EDGAR public API (no auth) to pull 5 years of income statement and balance sheet data for any list of US tickers; outputs clean CSV and a comparison summary HTML; useful for investment research and financial modeling | — | — | — | pending |
| 11 | 2026-06-18 | G | ambitious | Market Cap Higher or Lower | Browser game using baked-in Yahoo Finance data: given two company names with sector/industry hints, guess which has the higher market cap. Tracks accuracy and streak per session. Teaches market intuition through play. | — | — | — | pending |
| 12 | 2026-06-18 | G | ambitious | Stock Chart Direction Quiz | Show a real historical stock chart (last 6 months) with sector and key metrics visible; guess whether the stock went up, down, or flat over the next quarter. Uses pre-generated yfinance data as static JSON. Trains pattern recognition and market intuition. | — | — | — | pending |
| 13 | 2026-08-07 | C | ambitious | Concept Atlas | Cross-reference the user's own markdown notes against Wikipedia/Wikidata to auto-build a personal glossary with definitions. Too close to Connectome (2026-07-11), which already indexes the user's own note corpus into a local knowledge graph. | — | — | — | pending |
| 14 | 2026-08-07 | C | ambitious | Grant Boilerplate Miner | Index past grant/manuscript text into a searchable library of reusable aims/significance/methods paragraphs, tagged and searchable. Real friction point ("Grant writing") but requires the user to manually supply source documents with no live or automatically-captured data source — the same "requires manual entry" failure mode that sank AI Session Context Bridge (2026-06-06, 3/10). | — | — | — | pending |
| 15 | 2026-08-07 | C | ambitious | Course Concept Map | Cross-reference lecture notes/syllabi across the user's three taught courses to flag topic overlap and gaps. Same manual-entry dependency as the Grant Boilerplate Miner; also more naturally a Learning Aid (Category E) than a knowledge base. | — | — | — | pending |

---

## Status Key

| Value | Meaning |
|-------|----------|
| `pending` | Available for lottery draws |
| `built` | Already implemented — excluded from future draws |
| `skipped` | You've decided not to build this — excluded from future draws |
