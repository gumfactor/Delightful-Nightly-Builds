# Why This — Trading Book

## Category and rotation

Today is 2026-08-23, day 235 of the year. `(235 - 1) % 9 = 0` → Category A — Dashboard / Visualizer.

## Lottery

Filtered `builds/ideas.md` to pending Category A rows: idea #3 (Lab Research Project Tracker, rated 4) and idea #6 (Open-Meteo Activity Planner, unrated). Idea #5 (GitHub Repository Health Scorecard) was excluded before the draw — it is a verbatim duplicate of the already-built 2026-06-21 build of the same name (rated 6/10), a correction that had slipped through every prior Category A lottery undetected; it is now marked `skipped` in `builds/ideas.md`.

- Pool size after correction: 2 (idea #3 rated 4, idea #6 unrated/default 5)
- Rated count `R` = 1 → `lottery_chance = min(75, 25 + 1*2) = 27%`
- Roll: 66 (via a genuine random draw, not a model guess)
- 66 > 27 → lottery missed, proceeded to fresh idea generation (Step 2d)

## Topic diversity check (last 10 builds)

Macro Kitchen (I, nutrition/Garmin), Earshot (A, Kwyeter/noise), Provenance (B, Canada List ownership batch), Curriculum Atlas (C, teaching), Maple Press (D, Canada List editorial), Voxel Lab (E, neuroimaging), Effort Ledger (F, grant budgets), Fairway Physics (G, golf physics), Snipvault (H, dev snippets), Renewal Radar (I, deadlines). No domain repeats more than once — no saturation flag applies. Investment/finance last appeared at Quarter Call (2026-08-11), outside the last-10 window.

## Fresh ideas considered

1. **Trading Book** *(winner)* — a live IBKR portfolio dashboard: real net liquidation, cash, P&L, and position detail pulled from the user's own locally running TWS/IB Gateway session via `ib_insync`, persisted daily to local SQLite, rendered as a dashboard with trend and allocation charts.
2. **Research Pulse** — a publication-momentum trend dashboard over the same saved topics Paper Lens/PubMed Research Radar already read as an inbox. Passed over: it would be the fourth build touching that same literature feed (Paper Lens, PubMed Research Radar, Impact Ledger already cover discovery/reading/citation-impact), while IBKR has zero prior coverage. Logged as idea #26.
3. **Canada List Business Density Dashboard** — a StatsCan Web Data Service dashboard of business counts/industry composition by province. Passed over for the same reason idea #21 was passed over on 2026-08-19: the StatsCan table/vector-ID schema needs a real exploration pass this session didn't budget for, and the build container's egress proxy blocking the host makes that exploration hard to verify live. Logged as idea #27.

## Why Trading Book wins

- **Direct PROFILE.md hit, never built.** Interactive Brokers (IBKR) is explicitly named twice in PROFILE.md — under "Tools and environments you use daily" and "Services / APIs you already have credentials for" — and PROFILE.md's own Data Sources section names the IBKR TWS API as available "for tools the user runs locally." Across 71 prior builds, three have touched investing (Investment Research Platform, SiliconWatch, Portfolio Lab, Quarter Call), and none have ever connected to the user's actual brokerage account. Every prior investing build used either `yfinance` market data or fully synthetic teaching data — this is the first to show the user their own real numbers.
- **Answers the catalog's own strongest and weakest investing feedback at once.** The 2026-06-14 Investment Thesis Journal (4/10) was marked down for being "a bare CLI with no view layer... needs dashboard integration to be worth reaching for daily." The calibration pattern CLAUDE.md itself names — mock/localStorage data scoring low, live data scoring higher — points directly at a real-account dashboard rather than another synthetic or public-market tool.
- **Genuinely daily-use shaped.** PROFILE.md ranks "Tools I'll actually use daily or weekly" as the #2 most valuable build outcome. A one-command sync against an account the user already has open in TWS every trading day is about as low-friction as a real financial tool gets.
- **Distinct from every existing investing build.** SiliconWatch compares 12 curated semiconductor tickers via public market data; Portfolio Lab teaches Modern Portfolio Theory on a fixed synthetic 12-asset basket; Quarter Call is a historical-chart guessing game. None reads the user's actual positions or P&L.

## Design note on the build container's package restriction

This session's `.claude/settings.json` explicitly denies `Bash(pip install:*)`, so `ib_insync` cannot be installed or import-verified here — the same constraint this catalog has documented for live external APIs generally (CLAUDE.md: "design for the user's runtime, not the build container"). `src/ibkr_client.py` is written so the `ib_insync` import happens lazily inside the one function that needs it, never at module import time, so `import src.ibkr_client` succeeds in this container with or without the package installed, and every test runs against a fake `ib_insync` module injected into `sys.modules` rather than the real package. The user installs the pinned version from `requirements.txt` on their own machine, where TWS/IB Gateway is already running.
