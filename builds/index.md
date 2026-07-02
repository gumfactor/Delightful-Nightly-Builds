# Nightly Builds — Catalog

> **Claude:** Append one row to the Full Catalog table each night. Update the Stats block and Last 7 Builds section.
> Never delete or rewrite existing rows — this is an append-only record.
> **You:** Add `Your Rating` (1–10) and `Rating Notes` after reviewing a build. Both feed future build decisions.

---

## Stats

- **Total builds:** 26
- **Completed:** 23
- **Partial:** 0
- **Aborted:** 0
- **Discarded:** 3
- **Last build date:** 2026-07-02
- **Categories used (all time):** A, B, C, D, E, F, G, H, I

---

## Last 7 Builds (Quick Reference for Decision-Making)

- 2026-06-27 — [G] — ambitious — Neurofact (complete)
- 2026-06-28 — [H] — ambitious — ci-pulse: GitHub Actions Performance Analyzer (complete)
- 2026-06-29 — [I] — ambitious — Project Pulse: Multi-Project Context Manager (complete)
- 2026-06-30 — [A] — ambitious — GitHub Developer Analytics Dashboard (complete)
- 2026-07-01 — [B] — ambitious — BIDS Dataset Organizer & Validator (complete)
- 2026-07-02 — [C] — ambitious — PubMed Research Radar (complete)

---

## Full Catalog

| Date | Category | Complexity | Title | Short Description | Tech | Status | Your Rating | Rating Notes |
|------|----------|------------|-------|-------------------|------|--------|-------------|--------------|
| 2026-06-06 | B | ambitious | AI Session Context Bridge (ctxlog) | Python CLI to capture AI coding session state and generate markdown handoff documents | Python 3, stdlib, pytest | complete | 3 | Requires manual entry to be useful — value depends entirely on what you write into it, making it no better than a markdown file. Architecture is sound but the wrong layer was automated. Would score higher with auto-capture of git state and Claude Code session transcript. |
| 2026-06-07 | H | focused | Git Standup Reporter | Python CLI to summarise recent git commits as a standup report; extended to pull GitHub pushed commits and local unpushed commits automatically | Python 3, stdlib, pytest | complete | — | — |
| 2026-06-08 | F | focused | Quick Data Profiler | Python CLI that profiles CSV and JSON/JSONL files — infers column types, shows null rates, computes numeric distributions, and lists top-value frequencies | Python 3, stdlib, pytest | discarded | 1 | Totally redundant with pandas df.describe() and R summary() — trivially handled by existing tools in the user's stack. No reason to build this. |
| 2026-06-09 | A | focused | Investment Research Notes | Browser app for capturing investment thesis notes per ticker with conviction rating, status lifecycle, and JSON export — localStorage only, no live data | HTML/CSS/JS, Playwright | discarded | 2 | Good field design (conviction rating, watchlist/owned/passed lifecycle) but localStorage only with no real data integration makes it hollow. The right ideas in the wrong shell. |
| 2026-06-10 | A | ambitious | Investment Research Platform | Python CLI combining live watchlist metrics (prices, sparklines, 52W range, P/E, market cap) with a persistent thesis journal — per-ticker notes with price-at-note capture, % move since, and full CLI for add/show/list/search/delete | Python 3, yfinance, pytest | complete | — | — |
| 2026-06-12 | A | solid | Investment Watchlist Dashboard | Python CLI that fetches yfinance data for a watchlist and renders an HTML dashboard with 52-week progress bars, dark/light mode, and terminal text output | Python 3, yfinance, pytest | discarded | 3 | Near-duplicate of the Jun 10 build — same data sources, similar output, marginal rendering differences. 52-week progress bar and --text mode are slightly better than Jun 10 equivalents but not enough to justify keeping both. |
| 2026-06-14 | C | focused | Investment Thesis Journal | Python CLI to record investment research notes per ticker with live price capture at time of writing for later accountability | Python 3, yfinance, pytest | complete | 4 | Good core concept — price-at-time-of-note creates genuine accountability over time. Delivered as a bare CLI with no view layer; value is real but half-realized. Needs dashboard integration to be worth reaching for daily. |
| 2026-06-17 | F | ambitious | Qualtrics Survey Data Inspector | Python CLI that parses Qualtrics CSV exports (3-row header format), computes research-quality data QC metrics (completion, timing, missing data, straight-lining, duplicate IPs, Cronbach's alpha), and produces a text + HTML report plus a cleaned CSV with QI_Flags column | Python 3, stdlib, pytest | complete | 9 | — |
| 2026-06-18 | G | ambitious | Regex Dojo | Browser puzzle game with 20 progressive levels — write a regex to match the green strings and reject the red ones; teaches literals through lookaheads with real-time feedback and localStorage progress | Vanilla HTML/CSS/JS, Playwright | complete | — | — |
| 2026-06-19 | H | ambitious | dep-check: Python Dependency Auditor | Python CLI that audits requirements.txt/setup.cfg/Pipfile against PyPI — classifies each pinned package as up-to-date/patch/minor/major, flags yanked releases, outputs coloured terminal report or self-contained HTML dashboard; --exit-on-outdated enables CI gating | Python 3, stdlib, pytest | complete | — | — |
| 2026-06-20 | I | solid | Run Planner | Python CLI to log runs and track weekly mileage, with Open-Meteo 7-day weather scoring for running/golf/boating comfort windows and a Chart.js HTML dashboard | Python 3, Open-Meteo, Chart.js, pytest | complete | — | — |
| 2026-06-21 | A | ambitious | GitHub Repository Health Scorecard | Python CLI that fetches all GitHub repos via GITHUB_TOKEN, computes a composite health score from recency/CI/issues, and generates a dark-mode HTML dashboard with Chart.js doughnut chart, sortable/filterable repo table, and optional AI-generated briefing | Python 3, GITHUB_TOKEN, Chart.js, Anthropic API, pytest | complete | 6 | Good idea and the right output format — consolidates repo health info that would otherwise require clicking through GitHub. Loses points for overlapping with GitHub's own Insights views and being very similar to the Jun 11 terminal build. Would score significantly higher if it incorporated AI agent conversation history per repo, giving a view GitHub can't provide. |
| 2026-06-22 | B | ambitious | Morning Briefing | Python CLI combining GitHub activity, yfinance portfolio pulse, Open-Meteo weather windows scored for run/golf/boat, and Claude Haiku AI synthesis into a single daily HTML dashboard and markdown file | Python 3, yfinance, Open-Meteo, GITHUB_TOKEN, Anthropic API, Chart.js, pytest | complete | 5 | Right concept — multi-source daily digest with AI synthesis is genuinely useful. But ChatGPT's scheduling feature achieves the same result with a 2-minute setup, which undercuts the "this build solves something I couldn't otherwise do" argument. The value is real but the build is over-engineered for a use case existing tools cover adequately. |
| 2026-06-23 | C | ambitious | Paper Lens | Python CLI that queries arXiv across 4 topic areas, batches abstracts to Claude Haiku for relevance scoring (1–10) and plain-English summaries, stores results in SQLite with deduplication, and renders a dark-mode HTML inbox with filter tabs, search, and read-state tracking | Python 3, arXiv API, Anthropic API, SQLite, pytest | complete | 6 | Solid concept — AI relevance scoring is the right differentiating layer that turns a raw paper feed into a prioritized inbox. Limited by arXiv-only sourcing; a neuroscience researcher needs PubMed and Google Scholar at minimum. Worth extending rather than discarding — the core pipeline is sound. |
| 2026-06-24 | D | ambitious | AI Lecture Builder | Python CLI using Anthropic API to generate a complete 7-section lecture package (objectives, outline, hook, discussion questions, quiz, key concepts, homework) and render it as a tabbed dark-mode HTML viewer with copy and export functions | Python 3, Anthropic API, pytest | complete | 2 | The AI-generated content is the right core value, but a tabbed HTML viewer adds overhead without adding capability the user can't get from a single Claude prompt. Needs a genuinely differentiating layer: integration with existing course materials, Canvas/LMS export, or a persistent lecture library. As built, a power user replicates this with one prompt in the Claude interface. |
| 2026-06-26 | F | ambitious | GitHub Developer Activity Explorer | Python CLI that fetches all GitHub repos via GITHUB_TOKEN, analyzes commit patterns across 12 months, and renders a dark-mode HTML dashboard with hourly heatmap, day-of-week distribution, 52-week volume trend, repo focus map, streak analytics, and an AI developer profile via Claude Haiku | Python 3, GITHUB_TOKEN, Chart.js 4.4.4, Anthropic API, pytest | complete | — | — |
| 2026-06-27 | G | ambitious | Neurofact | Self-contained browser quiz game: 30 neuroscience claims (15 real research findings, 15 AI-generated plausible fakes) presented one at a time — players press Real Finding or AI Generated, then see the correct answer and explanation; final screen shows grade (A–F), accuracy, streak, and a real-vs-fake breakdown | Vanilla HTML/CSS/JS, Playwright, Python 3, pytest | complete | — | — |
| 2026-06-28 | H | ambitious | ci-pulse: GitHub Actions Performance Analyzer | Python CLI that fetches all completed GitHub Actions runs across every repo via GITHUB_TOKEN, computes per-workflow avg/p95 duration and failure rates, ranks by improvement potential, and generates a dark-mode HTML dashboard with 3 Chart.js charts (slowest workflows, failure rates, 30-day trend) and a sortable per-workflow table; AI insights panel via Claude Haiku when ANTHROPIC_API_KEY is set | Python 3, GITHUB_TOKEN, Chart.js 4.4.4, Anthropic API, pytest | complete | — | — |
| 2026-06-29 | I | ambitious | Project Pulse: Multi-Project Context Manager | Python CLI to register and track multiple simultaneous projects — syncs GitHub commits via GITHUB_TOKEN, records manual activity notes (idempotent), generates AI context briefs via Claude Haiku with text fallback, and renders a dark-mode HTML dashboard with a 30-day stacked bar Chart.js timeline, staleness badges (green/yellow/orange/red), project cards with type/repo tags, and a type filter | Python 3, GITHUB_TOKEN, Chart.js 4.4.4, Anthropic API, SQLite, pytest | complete | — | — |
| 2026-06-30 | A | ambitious | GitHub Developer Analytics Dashboard | Python CLI that fetches all owned repos via GITHUB_TOKEN, collects 12 months of commit history, and renders a dark-mode HTML dashboard with four tabs: Overview (hero stats + top repos bar), Timeline (CSS grid heatmap: repo × month), Rhythm (hour-of-day + weekday bar charts), and Languages (stacked horizontal bar by repo) | Python 3, GITHUB_TOKEN, Chart.js 4.4.4, requests, pytest | complete | — | — |
| 2026-07-01 | B | ambitious | BIDS Dataset Organizer & Validator | Python CLI that scans a neuroimaging dataset directory against core BIDS naming rules (entity order, required JSON sidecars, events.tsv for task runs, dataset_description.json, zero-padding consistency, duplicate detection, session consistency), produces text/JSON/dark-mode HTML reports, safely auto-fixes zero-padding mismatches with a dry-run-by-default `--apply` flag, and generates an optional Claude Haiku plain-English action list from the structural findings | Python 3, stdlib, Anthropic API (optional), pytest | complete | — | — |
| 2026-07-02 | C | ambitious | PubMed Research Radar | Python CLI that queries PubMed E-utilities (free, no auth) across 5 saved topics seeded from forensic/affective neuroscience research interests, dedupes articles by PMID in SQLite, scores relevance 1-10 with a plain-English summary and methodology tag via Claude Haiku (with a deterministic keyword-overlap fallback when no API key is set), and renders a dark-mode HTML radar report with topic tabs, relevance sorting, client-side search, and localStorage star/read state | Python 3, PubMed E-utilities, Anthropic API (optional), SQLite, pytest | complete | — | — |

---

## Category Key

| ID | Category |
|----|----------|
| A  | Dashboard / Visualizer |
| B  | Productivity Utility |
| C  | Personal Knowledge Tool |
| D  | Creative / Generative |
| E  | Learning Aid |
| F  | Data Explorer |
| G  | Game / Puzzle |
| H  | Developer Tool |
| I  | Life Admin Helper |

## Status Key

| Value | Meaning |
|-------|-------|
| `complete` | All hard standards met, committed and pushed |
| `partial` | Build works but scope was reduced; documented in BUILD_LOG |
| `aborted` | Could not complete safely; see ABORTED.md in the dated folder |
| `discarded` | Build completed but judged not worth keeping; folder renamed with -DISCARDED suffix |
