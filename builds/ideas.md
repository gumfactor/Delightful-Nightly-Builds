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
| 4 | 2026-06-09 | B | ambitious | Cross-Agent Project Activity Workstreams | Automatically correlate Git, GitHub, and AI-agent activity into evidence-backed workstreams that can generate accurate standups, resumptions, handoffs, timelines, and decision histories across tools | [Brief](idea-briefs/cross-agent-project-activity-workstreams.md) | 9 | Built as Worklog (2026-07-10), which explicitly implements this brief as its first release. Backlog bookkeeping was never updated at the time; correcting the status now so it stops surfacing in future Category B draws. | built |
| 5 | 2026-06-10 | A | ambitious | GitHub Repository Health Scorecard | Python script using GITHUB_TOKEN to pull all user repos and generate an HTML health scorecard: last commit date, open issues/PRs, CI status, contributor count, and a health score per repo | — | — | Won the 2026-07-27 Category A lottery draw (roll 7 of 14) but is a verbatim duplicate of the already-built, already-rated 2026-06-21 build of the identical title/concept (scored 6/10, with a specific critique already on file). Marking skipped rather than rebuilding a zero-differentiation duplicate. | skipped |
| 6 | 2026-06-10 | A | ambitious | Open-Meteo Activity Planner | Vanilla HTML/JS dashboard pulling from Open-Meteo API for Toronto — 7-day forecast with activity suitability scores for running, golf, and boating; no auth required | — | — | Superseded by the 2026-06-20 Run Planner build, which already delivers Open-Meteo-based run/golf/boat comfort-window scoring plus a Chart.js dashboard. Marking skipped as a stale duplicate. | skipped |
| 7 | 2026-06-11 | B | focused | Morning Briefing | Unified daily digest that combines the Git Standup Reporter, Investment Portfolio Snapshot, and GitHub Repository Health Dashboard into a single morning report — commits from yesterday, portfolio overnight moves, and any repos that have gone quiet | — | 8 | Built verbatim as Morning Briefing (2026-06-22) — same title, same combination of GitHub activity + portfolio pulse + digest format. Backlog bookkeeping was never updated at the time; correcting the status now so it stops surfacing in future Category B draws. | built |
| 8 | 2026-06-14 | A | ambitious | Investment Research Platform | Unified HTML report that merges live watchlist metrics (prices, sparklines, 52W range, P/E, analyst target) with thesis journal entries per ticker — showing the price when each thesis was written and the % move since, so you can evaluate your reasoning against outcomes at a glance. Builds on the Jun 10 Portfolio Snapshot as the base with the Jun 14 Thesis Journal's price-at-note logic integrated as a data layer. | — | 8 | Combines the two strongest investment builds into something with genuine daily utility — the accountability loop between thesis and outcome is the unique value | skipped |
| 9 | 2026-06-17 | H | ambitious | GitHub Actions Performance Analyzer | Uses GITHUB_TOKEN to fetch workflow run times across all repos and generate an HTML report identifying slow steps, frequent failures, and wasted CI minutes — with trend charts and per-job breakdown | — | — | — | pending |
| 10 | 2026-06-17 | F | ambitious | SEC EDGAR Financial History Extractor | Uses SEC EDGAR public API (no auth) to pull 5 years of income statement and balance sheet data for any list of US tickers; outputs clean CSV and a comparison summary HTML; useful for investment research and financial modeling | — | — | — | pending |
| 11 | 2026-06-18 | G | ambitious | Market Cap Higher or Lower | Browser game using baked-in Yahoo Finance data: given two company names with sector/industry hints, guess which has the higher market cap. Tracks accuracy and streak per session. Teaches market intuition through play. | — | — | — | pending |
| 12 | 2026-06-18 | G | ambitious | Stock Chart Direction Quiz | Show a real historical stock chart (last 6 months) with sector and key metrics visible; guess whether the stock went up, down, or flat over the next quarter. Uses pre-generated yfinance data as static JSON. Trains pattern recognition and market intuition. | — | — | — | pending |
| 13 | 2026-07-25 | H | ambitious | Deadweight: Dead Code / Unused Symbol Finder | Python CLI using `ast` to statically find unused functions/classes/module-level variables across a codebase, ranked by confidence (excludes dunders, pytest test_ functions, __all__ exports, decorated/dynamically-registered symbols), with an optional Claude second opinion on medium-confidence candidates to catch likely dynamic-usage false positives; terminal + HTML report, `--exit-on-high-confidence` for CI gating | — | — | Considered and passed over for the 2026-07-25 build (BugTrace) — the established PyPI package `vulture` already does the mechanical core of this well; would need a genuinely strong AI-driven differentiator (e.g. dynamic-usage false-positive triage) to be worth building instead of just recommending vulture | pending |
| 14 | 2026-07-25 | H | ambitious | Flaky Test Detector | Python CLI that reruns a pytest (or Playwright) suite N times, tracks per-test pass/fail variance, and ranks tests by flakiness score with a summary report; useful for catching intermittent failures before they erode trust in CI | — | — | Genuinely useful but narrow — only valuable for repos that already have an intermittently-failing suite, which most of the user's current nightly-build repos don't yet exhibit. Revisit if a future build's test suite turns out flaky. | pending |
| 15 | 2026-07-26 | I | ambitious | Household & Cottage Maintenance Scheduler | Tracks recurring cottage/boat maintenance tasks (winterizing, engine service, dock removal) and uses Open-Meteo to flag the next dry/calm weather window for weather-dependent tasks | — | — | Considered and passed over for the 2026-07-26 build (TripKit) — narrower audience-fit than trip prep, and the weather-window logic is largely a subset of what TripKit's forecast/climate-normal engine already does; would ship thinner for similar effort | pending |
| 16 | 2026-07-26 | I | ambitious | Momentum: Cross-Domain Habit Tracker | Daily habit/streak log for writing and exercise, using GitHub commit activity as a proxy signal plus manual logging, with AI coaching on streaks and lapses | — | — | Considered and passed over for the 2026-07-26 build (TripKit) — GitHub is already the backbone of five prior builds this month (Worklog, Pipeline Pulse, and others); no live data source in a genuinely new domain, and the manual-log-plus-streak pattern overlaps procedurally with Deadline Guardian and Ledger Lens | pending |
| 17 | 2026-07-27 | A | ambitious | Canadian Manufacturing Sector Health Dashboard | Statistics Canada open-data dashboard tracking manufacturing sector indicators (output, employment, trade balance) by industry, surfaced against The Canada List's Canadian-made product categories | — | — | Considered and passed over for the 2026-07-27 build (SiliconWatch) — Canada-topic domain already appeared twice in the last 10 builds (CanEcon Pulse, CanFile); would push a third within the same 10-build window while a genuinely uncovered profile interest (AI infrastructure/semiconductors) was still available | pending |
| 18 | 2026-07-27 | A | ambitious | Lab & Grad Student Citation Impact Tracker | Dashboard using the free Crossref/OpenAlex APIs (no auth) to track citation counts and publication trends over time for the user's own lab's DOIs/ORCID, visualized with per-paper and per-year trend charts | — | — | Considered and passed over for the 2026-07-27 build (SiliconWatch) — the academic-research topic domain was already saturated in the last 10 builds (Protocol Forge, Bridgework, Bayes Lab all research/academia-adjacent); worth revisiting once that domain cools down | pending |
| 19 | 2026-07-28 | B | ambitious | Student Evaluation Feedback Assistant | Batch-compiles rubric scores and short grader notes into polished individual student feedback paragraphs via Claude | — | — | Considered and passed over for the 2026-07-28 build (Voiceprint) — the only useful input path is real student names and submission text sent to a third-party API, which sits too close to the STANDARDS.md line on personal data for an unsupervised nightly build. Revisit only with a privacy-first redesign (anonymized rubric codes only, never names or verbatim submissions). | pending |
| 20 | 2026-07-28 | B | ambitious | Citation/Reference Batch Formatter | CLI that resolves a folder of citation strings or DOIs via the free Crossref API (no auth), reformats to a consistent style, dedupes, and emits BibTeX | — | — | Considered and passed over for the 2026-07-28 build (Voiceprint) — genuinely useful for literature reviews/research admin, but it's a formatting/lookup pipeline with no real judgment layer, mechanically thinner than the AI-tell auditor. Superseded by the 2026-07-29 Citation Vault build, whose `export bibtex` command folds this exact feature into a full reading tracker. Marking skipped as a stale near-duplicate. | skipped |
| 21 | 2026-07-29 | C | ambitious | Teaching Material Archive | Index and search lecture/discussion/quiz materials across courses, tagged by concept, growing each term into a persistent teaching knowledge base | — | — | Considered and passed over for the 2026-07-29 build (Citation Vault) — architecturally near-identical to the already-built Connectome (generic folder-of-notes indexer with concept extraction and a note graph); a user could already point Connectome at a folder of teaching notes. Worth revisiting only with a genuinely distinct mechanic (e.g. syllabus/term structure, not just file indexing). | pending |
| 22 | 2026-07-29 | C | ambitious | Grant Boilerplate & Progress Report Library | Reusable grant-writing sections (specific aims, significance, broader impacts) indexed by funding mechanism/topic, with approved-boilerplate reuse for future tag-similar applications | — | — | Considered and passed over for the 2026-07-29 build (Citation Vault) — nearly identical architecture to the already-built Protocol Forge (compliance rule engine + approved-boilerplate reuse + 3-tier AI/template fallback), just swapping IRB protocol sections for grant sections. Same redundancy risk that cost points on the GitHub-scorecard duplicate. Revisit with a more differentiated angle. | pending |

---

## Status Key

| Value | Meaning |
|-------|----------|
| `pending` | Available for lottery draws |
| `built` | Already implemented — excluded from future draws |
| `skipped` | You've decided not to build this — excluded from future draws |
