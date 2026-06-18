# Nightly Builds — Catalog

> **Claude:** Append one row to the Full Catalog table each night. Update the Stats block and Last 7 Builds section.
> Never delete or rewrite existing rows — this is an append-only record.
> **You:** Add `Your Rating` (1–10) and `Rating Notes` after reviewing a build. Both feed future build decisions.

---

## Stats

- **Total builds:** 8
- **Completed:** 5
- **Partial:** 0
- **Aborted:** 0
- **Discarded:** 3
- **Last build date:** 2026-06-17
- **Categories used (all time):** A, B, C, F, H

---

## Last 7 Builds (Quick Reference for Decision-Making)

- 2026-06-07 — [H] — focused — Git Standup Reporter (complete)
- 2026-06-08 — [F] — focused — Quick Data Profiler (discarded)
- 2026-06-09 — [A] — focused — Investment Research Notes (discarded)
- 2026-06-10 — [A] — ambitious — Investment Research Platform (complete)
- 2026-06-12 — [A] — solid — Investment Watchlist Dashboard (discarded)
- 2026-06-14 — [C] — focused — Investment Thesis Journal (complete)
- 2026-06-17 — [F] — ambitious — Qualtrics Survey Data Inspector (complete)

---

## Full Catalog

| Date | Category | Complexity | Title | Short Description | Tech | Status | Your Rating | Rating Notes |
|------|----------|------------|-------|-------------------|------|--------|-------------|______________|
| 2026-06-06 | B | ambitious | AI Session Context Bridge (ctxlog) | Python CLI to capture AI coding session state and generate markdown handoff documents | Python 3, stdlib, pytest | complete | 3 | Requires manual entry to be useful — value depends entirely on what you write into it, making it no better than a markdown file. Architecture is sound but the wrong layer was automated. Would score higher with auto-capture of git state and Claude Code session transcript. |
| 2026-06-07 | H | focused | Git Standup Reporter | Python CLI to summarise recent git commits as a standup report; extended to pull GitHub pushed commits and local unpushed commits automatically | Python 3, stdlib, pytest | complete | — | — |
| 2026-06-08 | F | focused | Quick Data Profiler | Python CLI that profiles CSV and JSON/JSONL files — infers column types, shows null rates, computes numeric distributions, and lists top-value frequencies | Python 3, stdlib, pytest | discarded | 1 | Totally redundant with pandas df.describe() and R summary() — trivially handled by existing tools in the user's stack. No reason to build this. |
| 2026-06-09 | A | focused | Investment Research Notes | Browser app for capturing investment thesis notes per ticker with conviction rating, status lifecycle, and JSON export — localStorage only, no live data | HTML/CSS/JS, Playwright | discarded | 2 | Good field design (conviction rating, watchlist/owned/passed lifecycle) but localStorage only with no real data integration makes it hollow. The right ideas in the wrong shell. |
| 2026-06-10 | A | ambitious | Investment Research Platform | Python CLI combining live watchlist metrics (prices, sparklines, 52W range, P/E, market cap) with a persistent thesis journal — per-ticker notes with price-at-note capture, % move since, and full CLI for add/show/list/search/delete | Python 3, yfinance, pytest | complete | — | — |
| 2026-06-12 | A | solid | Investment Watchlist Dashboard | Python CLI that fetches yfinance data for a watchlist and renders an HTML dashboard with 52-week progress bars, dark/light mode, and terminal text output | Python 3, yfinance, pytest | discarded | 3 | Near-duplicate of the Jun 10 build — same data sources, similar output, marginal rendering differences. 52-week progress bar and --text mode are slightly better than Jun 10 equivalents but not enough to justify keeping both. |
| 2026-06-14 | C | focused | Investment Thesis Journal | Python CLI to record investment research notes per ticker with live price capture at time of writing for later accountability | Python 3, yfinance, pytest | complete | 4 | Good core concept — price-at-time-of-note creates genuine accountability over time. Delivered as a bare CLI with no view layer; value is real but half-realized. Needs dashboard integration to be worth reaching for daily. |
| 2026-06-17 | F | ambitious | Qualtrics Survey Data Inspector | Python CLI that parses Qualtrics CSV exports (3-row header format), computes research-quality data QC metrics (completion, timing, missing data, straight-lining, duplicate IPs, Cronbach's alpha), and produces a text + HTML report plus a cleaned CSV with QI_Flags column | Python 3, stdlib, pytest | complete | 9 | — |

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
