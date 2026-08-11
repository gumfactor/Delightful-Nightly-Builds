# Future Features — Quarter Call

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Difficulty tiers by volatility** — Bucket rounds into Low/Medium/High volatility (using the already-computed `annualizedVolatilityPct`) and let Practice mode filter to one tier, so the user can specifically train on the hardest (highest-volatility, least-obvious) charts.
2. **"Skip the flat band" toggle** — A settings toggle that removes `outcome === "flat"` rounds from the pool for users who find the ±5% band ambiguous and want a cleaner up/down-only mode.
3. **Streak-based visual flourish** — A small on-screen callout at streak milestones (5, 10, 15) using only the data already tracked in `stats.streak` — no new data needed, purely a UI polish pass on the existing stats panel.

## Medium Effort (roughly one nightly build session)

4. **Expand the round bank with a `fetch_data.py --extend` flag** — Let the user append their own curated (ticker, decision_date) pairs to `CURATED_ROUNDS` via a small JSON sidecar file, re-run the fetch, and grow the bank past 48 rounds with their own watchlist tickers.
5. **Per-sector leaderboard / weakest-sector callout** — The `sectorStats` data already tracked in localStorage is enough to compute this; surface "Your weakest sector: Energy (2/8)" prominently instead of just listing all sectors flatly, turning the existing stats into an actionable practice suggestion.

## Ambitious Extensions (multi-session effort)

6. **Head-to-head mode against a naive baseline** — Alongside the player's guess, show what a simple momentum rule ("if trailing 6-month return is positive, guess up") would have called, and track the player's accuracy against that baseline over time — a genuinely interesting extension of the "markets are close to a random walk" framing already in the footer, turning intuition-training into a real behavioral-finance comparison.
7. **Cross-build integration with SiliconWatch/Impact Ledger's SQLite pattern** — Move from the current flat `rounds-data.js` file to a local SQLite round history (following the pattern several other builds in this catalog already use), so `fetch_data.py` can be re-run periodically to add newly-settled quarters for tickers already in the bank without hand-editing `CURATED_ROUNDS`, and old rounds are never lost.

---

## Possible Integration Points

- **Portfolio Lab (2026-08-09)** already implements a from-scratch financial-math JS module (`src/math.js`) and the same "ships honest, `fetch_data.py` run locally" pattern this build follows — a shared, extracted `fetch-yfinance-history.py` helper could serve both builds and any future one needing real historical price data.
- **SiliconWatch (2026-07-27)** already persists multi-week yfinance snapshots in local SQLite — the same infrastructure could back Future Feature #7 above.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Daily Challenge progress is not saved mid-run — reloading the page during a 5-round Daily Challenge restarts that day's set from round 1 (though it's the same deterministic 5 rounds, so nothing is skipped or duplicated, and completion is only recorded once all 5 are answered). | Persist `dailyIndex`/`dailyResults` to `localStorage` on every guess, not just at completion, and resume from the saved index on reload. |
| The 48-round bank is fixed at fetch time; sector/industry labels are hand-curated rather than pulled live from Yahoo Finance, since `yfinance`'s `.info` dict is notoriously inconsistent across versions. | If `yfinance`'s info API proves stable enough in practice, add it as an optional live override with the current hand-curated list as the fallback, rather than replacing it outright. |
| No way to review past Daily Challenge results beyond the current day's `localStorage.dailyHistory` object (which does accumulate every day played, but has no UI to browse it). | Add a small history view that reads `stats.dailyHistory` and renders a calendar-style streak view, similar to Confound Hunter's/Heuristic Hunt's per-flaw mastery dashboards. |
