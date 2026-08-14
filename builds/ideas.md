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
| 1 | 2026-06-06 | F | ambitious | The Canada List CSV Quality Inspector | Browser-based tool to inspect and validate CSV uploads for The Canada List pipeline — flags malformed rows, missing required columns, encoding issues, and duplicate entries before ingestion | — | 7 | Could be very useful if implemented properly — unclear what role Playwright plays here vs. a pure Python validator | built |
| 2 | 2026-06-06 | A | ambitious | Investment Research Dashboard | Comprehensive personal finance dashboard — portfolio tracking, watchlist, research notes, and performance over time; not just an investing-interest toy but a genuinely useful daily tool | — | 6 | Love the idea of a comprehensive investment dashboard, but not just for investing interest — that framing is less exciting | skipped |
| 3 | 2026-06-06 | A | ambitious | Lab Research Project Tracker | Dashboard for tracking neuroscience lab projects, milestones, team tasks, and publication status | — | 4 | No need — already use Teamwork.com for project tracking | pending |
| 4 | 2026-06-09 | B | ambitious | Cross-Agent Project Activity Workstreams | Automatically correlate Git, GitHub, and AI-agent activity into evidence-backed workstreams that can generate accurate standups, resumptions, handoffs, timelines, and decision histories across tools | [Brief](idea-briefs/cross-agent-project-activity-workstreams.md) | 9 | — | pending |
| 5 | 2026-06-10 | A | ambitious | GitHub Repository Health Scorecard | Python script using GITHUB_TOKEN to pull all user repos and generate an HTML health scorecard: last commit date, open issues/PRs, CI status, contributor count, and a health score per repo | — | — | Duplicate of the already-built 2026-06-21 GitHub Repository Health Scorecard (identical scope: GITHUB_TOKEN, per-repo health score, last-commit/issues/CI signals). Flagged as a verbatim duplicate when it was drawn on 2026-07-27 (overridden to fresh generation for SiliconWatch) but never corrected here until tonight (2026-08-14). | skipped |
| 6 | 2026-06-10 | A | ambitious | Open-Meteo Activity Planner | Vanilla HTML/JS dashboard pulling from Open-Meteo API for Toronto — 7-day forecast with activity suitability scores for running, golf, and boating; no auth required | — | — | — | pending |
| 7 | 2026-06-11 | B | focused | Morning Briefing | Unified daily digest that combines the Git Standup Reporter, Investment Portfolio Snapshot, and GitHub Repository Health Dashboard into a single morning report — commits from yesterday, portfolio overnight moves, and any repos that have gone quiet | — | 8 | — | pending |
| 8 | 2026-06-14 | A | ambitious | Investment Research Platform | Unified HTML report that merges live watchlist metrics (prices, sparklines, 52W range, P/E, analyst target) with thesis journal entries per ticker — showing the price when each thesis was written and the % move since, so you can evaluate your reasoning against outcomes at a glance. Builds on the Jun 10 Portfolio Snapshot as the base with the Jun 14 Thesis Journal's price-at-note logic integrated as a data layer. | — | 8 | Combines the two strongest investment builds into something with genuine daily utility — the accountability loop between thesis and outcome is the unique value | skipped |
| 9 | 2026-06-17 | H | ambitious | GitHub Actions Performance Analyzer | Uses GITHUB_TOKEN to fetch workflow run times across all repos and generate an HTML report identifying slow steps, frequent failures, and wasted CI minutes — with trend charts and per-job breakdown | — | — | Duplicate of the already-built 2026-06-28 ci-pulse build (identical scope: GITHUB_TOKEN workflow-run timing, failure-rate trend charts, per-job breakdown). Corrected 2026-08-12 after it lost the Category H lottery draw on 2026-08-03 (Landing Pattern) without being flagged. | skipped |
| 10 | 2026-06-17 | F | ambitious | SEC EDGAR Financial History Extractor | Uses SEC EDGAR public API (no auth) to pull 5 years of income statement and balance sheet data for any list of US tickers; outputs clean CSV and a comparison summary HTML; useful for investment research and financial modeling | — | — | — | pending |
| 11 | 2026-06-18 | G | ambitious | Market Cap Higher or Lower | Browser game using baked-in Yahoo Finance data: given two company names with sector/industry hints, guess which has the higher market cap. Tracks accuracy and streak per session. Teaches market intuition through play. | — | — | — | pending |
| 12 | 2026-06-18 | G | ambitious | Stock Chart Direction Quiz | Show a real historical stock chart (last 6 months) with sector and key metrics visible; guess whether the stock went up, down, or flat over the next quarter. Uses pre-generated yfinance data as static JSON. Trains pattern recognition and market intuition. | — | — | — | built |
| 13 | 2026-08-07 | C | ambitious | Concept Atlas | Cross-reference the user's own markdown notes against Wikipedia/Wikidata to auto-build a personal glossary with definitions. Too close to Connectome (2026-07-11), which already indexes the user's own note corpus into a local knowledge graph. | — | — | — | pending |
| 14 | 2026-08-07 | C | ambitious | Grant Boilerplate Miner | Index past grant/manuscript text into a searchable library of reusable aims/significance/methods paragraphs, tagged and searchable. Real friction point ("Grant writing") but requires the user to manually supply source documents with no live or automatically-captured data source — the same "requires manual entry" failure mode that sank AI Session Context Bridge (2026-06-06, 3/10). | — | — | — | pending |
| 15 | 2026-08-07 | C | ambitious | Course Concept Map | Cross-reference lecture notes/syllabi across the user's three taught courses to flag topic overlap and gaps. Same manual-entry dependency as the Grant Boilerplate Miner; also more naturally a Learning Aid (Category E) than a knowledge base. | — | — | — | pending |
| 16 | 2026-08-08 | D | ambitious | Public-Talk Hook & Title Generator | AI-assisted title/hook/abstract generator for the user's empathy-and-AI public talks and workshops, using audience-register templates (undergrad / public / industry). Passed over — structurally identical to AI Lecture Builder's (2026-06-24, 2/10) single-shot-prose-wrapper failure mode; would need the same deterministic-rubric-plus-fallback shape Panel Prep uses to be defensible, and Bridgework (2026-07-21) already covers making research accessible to public audiences via analogies. | — | — | — | pending |
| 17 | 2026-08-08 | D | ambitious | Manuscript Peer-Review Critique Simulator | Generates a mock peer-review critique for manuscript drafts (distinct from grant proposals) — simulated reviewer pushback on framing, methods, and contribution. Passed over — Manuscript Pipeline (2026-08-06) already owns "manuscript" as a keyword in the catalog for status tracking, and NIH's Significance/Innovation/Approach rubric is a cleaner, more concrete deterministic scaffold to build against than generic peer-review conventions, which vary widely by journal and field. | — | — | — | pending |
| 18 | 2026-08-08 | D | ambitious | Investment Thesis Red-Team / Bear-Case Simulator | Generates an adversarial bear-case critique against a saved investment thesis (ticker + written rationale), stress-testing assumptions the way a skeptical portfolio committee would. Passed over — investing already appeared once in the last 10 builds (SiliconWatch, 2026-07-27) and PROFILE.md's more specifically-named, completely untouched Category D friction points (grant writing, ethics applications) were prioritized instead. | — | — | — | pending |
| 19 | 2026-08-09 | E | ambitious | Git Internals Playground | Interactive clickable commit-DAG visualizer teaching branch/merge/rebase/detached-HEAD mechanics via a simulated repo the user manipulates step by step. Passed over for Portfolio Lab tonight — genuinely untouched Learning Aid topic tied to PROFILE.md's "Improve Git/GitHub proficiency" goal, but every input is necessarily synthetic (a teaching git repo has no real external data to connect to), making it a weaker fit than an idea with a live data source available. | — | — | — | pending |
| 20 | 2026-08-09 | E | ambitious | Agent Orchestration Sandbox | Visual explainer of multi-agent workflow execution patterns (pipeline vs. parallel, barriers, timing gains) as an interactive DAG the user builds and "runs" to see simulated wall-clock differences. Passed over — ties directly to PROFILE.md's "Master AI agent workflows and orchestration" goal and is genuinely novel, but is entirely synthetic/conceptual (no real data source) and risks reading as self-referential given the user's own Claude Code workflow usage. | — | — | — | pending |
| 21 | 2026-08-12 | H | ambitious | Node/npm Dependency Freshness & Advisory Checker | Extend dep-check's (2026-06-19) Python-only outdated/vulnerable-package scan to package.json/package-lock.json against the npm registry and GitHub Advisory Database. Passed over tonight — real gap (dep-check never covered Node) but structurally a near-rerun of an existing build with a swapped ecosystem, not a genuinely new tool shape. | — | — | — | pending |
| 22 | 2026-08-12 | H | ambitious | Git File Archaeology Narrator | Pick one file and walk its full git blame/log history, using Claude to narrate how a specific function evolved and why, based on commit messages and diffs. Passed over tonight — too close to Waymark's (2026-08-07) decision-mining shape (git log heuristic scoring + optional Claude narrative); a per-file narrative view is a smaller variation on already-covered ground rather than a new capability. | — | — | — | pending |
| 23 | 2026-08-13 | I | ambitious | Recurring Bills & Subscription Price Tracker | Track recurring bills/subscriptions from a bank CSV export, flag price increases, send renewal reminders. Passed over — Ledger Lens (2026-07-08) already does merchant+amount-clustering recurring-charge detection from bank CSVs; this would be a near-duplicate of an existing feature. | — | — | — | pending |
| 24 | 2026-08-13 | I | ambitious | Home/Cottage Maintenance Checklist (non-boat) | General home maintenance schedule (HVAC filters, gutters, etc.) with weather-based scheduling via Open-Meteo. Passed over — structurally identical to Dockside's (2026-08-04) seasonal-task-vs-weather-readiness engine, just swapping the task list. | — | — | — | pending |
| 25 | 2026-08-13 | I | ambitious | TFSA/RRSP Contribution Room Tracker | Track Canadian registered-account contribution room using hardcoded official annual limits plus an optional local IBKR TWS sync to auto-detect registered-account contributions; deadline reminders for RRSP (Mar 1) and TFSA (Dec 31). Genuinely untouched IBKR integration and a real Life Admin gap. Passed over tonight only — investing/finance had already appeared twice in the last 10 builds (Portfolio Lab, Quarter Call), and a third so soon risked topic oversaturation; strong candidate for a future Category I or A build. | — | — | — | pending |
| 26 | 2026-08-14 | A | ambitious | Canada List Coverage & Growth Dashboard | Ingest a locally-supplied Canada List business-directory export (CSV/JSON) and visualize provincial/category coverage, ownership-confidence distribution, and growth over time across repeated snapshots. Passed over tonight — real gap (no prior Category A build visualizes aggregate directory coverage; Ingest Gate is QC-only, CanFile is per-company) but requires the user to supply a real export file each run rather than the tool fetching live data itself, a weaker fit than an idea with a genuinely live data source. | — | — | — | pending |
| 27 | 2026-08-14 | A | ambitious | Sector Rotation Heatmap | Live yfinance-backed dashboard of relative sector-ETF momentum/rotation over trailing 1/3/6-month windows. Passed over tonight — investing/finance had already appeared twice in the last 10 builds (Portfolio Lab, Quarter Call); a third so soon risked topic oversaturation per CLAUDE.md's diversity check, and Category A's own history already includes two investing-flavored builds (Investment Research Platform, SiliconWatch). | — | — | — | pending |

---

## Status Key

| Value | Meaning |
|-------|----------|
| `pending` | Available for lottery draws |
| `built` | Already implemented — excluded from future draws |
| `skipped` | You've decided not to build this — excluded from future draws |
