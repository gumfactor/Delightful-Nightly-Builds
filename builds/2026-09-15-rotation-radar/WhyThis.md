# Why This — Rotation Radar

## Category & selection path
Day of year 258 → `category_index = (258-1) % 9 = 5` → **Category F (Data Explorer)**.

Category F's backlog had 7 matching pending ideas (#10, #20, #21, #30, #31, #45, #46 in `builds/ideas.md`), all unrated (R=0), giving a `lottery_chance` of `min(75, 25+0) = 25%`. Rolled `98/100` (`python3 -c "import random; print(random.randint(1,100))"`) — missed the gate, so tonight went to fresh idea generation rather than a backlog draw.

## Topic diversity check
Scanned the last 10 builds (2026-09-05 through 2026-09-14): Mediation/Moderation Lab (E), Almanac (F, weather), True Course (G, boating), Secrets Sentinel (H, git security), Headroom (I, tax), Dominion Index (A, Wikidata), GradeLine (B, grading), Throughline (C, citations), Preprint Pulse (D, arXiv), ERP Lab (E, EEG). No investment/finance topic anywhere in that window — the last finance-adjacent build (EDGAR Lens, 2026-08-28) is now outside the 10-build lookback. Yahoo Finance/sector data was a clear, untouched angle for tonight.

## Fresh ideas generated
1. **Rotation Radar** (chosen) — a Yahoo Finance sector Relative Rotation Graph (RRG) explorer: cross-sectional RS-Ratio/RS-Momentum analysis across the 11 SPDR sector ETFs vs. SPY, classified into Leading/Weakening/Lagging/Improving quadrants with a trailing history plot.
2. Corporate Ownership Chain Explorer (Wikidata per-company drill-down for Canada List fact-checking) — logged as backlog idea #61.
3. Open-Meteo Air Quality & Pollen Explorer — logged as backlog idea #62.

Rotation Radar won on two grounds:
- **Topic novelty**: none of this catalog's 92 prior builds does cross-sectional relative-strength/rotation analysis. The four prior finance-adjacent builds are a per-ticker watchlist/thesis journal (June), a live IBKR account dashboard (Trading Book), and a single-filing statement analyzer (EDGAR Lens) — all per-ticker or per-account, never a market-structure view across sectors.
- **Topic diversity**: investment/finance had zero coverage in the last-10-builds window, while the two runner-up ideas' data sources (Wikidata, Open-Meteo) were each used within the last 5–9 nights for the exact same Category F slot (Dominion Index, Almanac).

## PROFILE.md tie
Directly serves "quantitative investing and market structure" (named explicitly under reading interests) and "Personal quantitative investing research and automation" (an active personal project). Unlike the June investment builds — which were mostly discarded for being near-duplicates of each other (per-ticker watchlists with marginal rendering differences) — this is a genuinely different analytical layer: sector-level rotation, not individual-position tracking, with local SQLite history so the tool gets more useful the more nights it's actually run.

## Deviations from a fully "textbook" RRG
The real Julius de Kempenaer RS-Ratio/RS-Momentum formula used by StockCharts/Bloomberg is proprietary and not publicly documented in exact form. Rotation Radar implements a standard, publicly documented cross-sectional-z-score approximation instead (full formula in PRD.md), chosen specifically because it is internally consistent and hand-verifiable — verification work is in BUILD_LOG.md. This is a documented approximation, not a claim of matching a commercial vendor's exact output, and is stated as such in Manual.md.

## Idea Brief
No linked Idea Brief — this was a freshly generated idea, not a backlog draw with a brief attached.
