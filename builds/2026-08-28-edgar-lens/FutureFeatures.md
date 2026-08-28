# Future Features — EDGAR Lens

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`compare TICK1,TICK2,...` terminal command** — a side-by-side terminal table of the latest-FY metrics for a chosen subset of tracked tickers, without needing to open the HTML dashboard.
2. **`--min-anomalies N` filter on `flags`** — only print companies with at least N flagged anomalies, useful once the watchlist grows past a handful of tickers.
3. **CSV export of the comparison table** — a `render --csv out.csv` flag that writes the same latest-FY comparison data other tools (Excel, pandas) can consume directly.
4. **Anomaly severity ranking** — sort the Anomalies panel by how far past its threshold each flag is (e.g. a -40% revenue decline above a -12% one), not just by fiscal year.

## Medium Effort (roughly one nightly build session)

5. **10-K/A restatement flagging** — currently a restated fact silently replaces the original via latest-`filed`-wins; a dedicated `restated: true` marker and a visible "this year was later restated" badge would make that transparent instead of invisible.
6. **Peer-group percentile context** — instead of only flagging a company against its own history, compute the same metrics across the whole watchlist and note when a company's margin/leverage is an outlier versus its tracked peers, not just versus its own prior year.
7. **Quarterly (10-Q) trend layer** — extend the extraction and metrics engine to also track quarterly figures for the most recent 8 quarters, giving a finer-grained early-warning signal between annual 10-Ks.

## Ambitious Extensions (multi-session effort)

8. **Insider transaction overlay (SEC Form 4)** — cross-reference each flagged anomaly year with insider buying/selling activity from the same SEC EDGAR full-text search API, showing whether insiders were accumulating or distributing around a deteriorating year.
9. **A standing watchlist that grows into a screening tool** — once a user has synced dozens of tickers over months, add a `screen` command that ranks the entire tracked universe by a composite deterioration score, turning this from a lookup tool into a discovery tool.

---

## Possible Integration Points

- **Trading Book** (2026-08-23) reads live IBKR account positions — a shared "your actual holdings" ticker list could seed EDGAR Lens's `sync --from-portfolio` instead of a manually typed ticker string, so the fundamentals view always matches what's actually held.
- **SiliconWatch** (2026-07-27) already tracks a curated 12-company AI-infrastructure basket via `yfinance` — EDGAR Lens could sync that same basket to add a fundamentals-deterioration layer next to SiliconWatch's valuation/margin trend view, without duplicating either build's core engine.
- **Quarter Call** (2026-08-11) uses real historical Yahoo Finance closes for a chart-reading game — a shared "real financial data, honest about the build container's network constraint" pattern this build reuses directly (commit `data.js = null` until a live fetch, never fabricate).

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No quarterly data, only annual 10-K | See Medium Effort #7 above |
| IFRS/foreign-private-issuer filers unsupported | Add an `ifrs-full` taxonomy tag-resolution table alongside the existing `us-gaap` one |
| 10-K/A restatements are invisible (silently override, no badge) | See Medium Effort #5 above |
| Anomaly thresholds are fixed constants, not sector-aware (a 10% revenue swing means something different for a utility than a growth-stage tech company) | Add optional sector-specific threshold overrides, defaulting to today's fixed values |
