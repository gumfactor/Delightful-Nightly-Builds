# Future Features — SiliconWatch

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **CSV/JSON export** — a `python3 src/main.py export --db siliconwatch.db --format csv` command that dumps the latest snapshot table to a flat file for use in a spreadsheet or a separate analysis notebook.
2. **`--period` flag on `sync`** — let `sync` accept `2y`/`5y`/`max` instead of the hardcoded `1y`, so the price-history and eventual valuation-trend charts can span a longer window for tickers with a long history (e.g. TXN, INTC).
3. **Config validation command** — a `list --validate-config PATH` flag that checks a custom ticker JSON file for duplicate tickers or unknown subsector labels before a `sync` run wastes API calls on a typo'd ticker.

## Medium Effort (roughly one nightly build session)

4. **Historical earnings-date overlay** — pull each company's next/last earnings date from yfinance's calendar data and mark it on the price-history chart, so a sudden move is visibly explained rather than just appearing as a spike.
5. **Peer-relative valuation banding** — instead of just an absolute P/E number, compute each company's P/E percentile within its own sub-sector (not the whole list), so a viewer can see "NVDA trades at the 80th percentile of GPU/Accelerator valuations" rather than comparing a memory company's P/E to a foundry's.
6. **Routine wrapper** — package `sync` as a Claude Code Routine that runs on a weekday schedule (e.g. after market close), so the snapshot/price-trend history accumulates automatically without the user remembering to run it manually, the same pattern suggested for CanEcon Pulse.

## Ambitious Extensions (multi-session effort)

7. **SEC EDGAR cross-reference** — enrich the dashboard with quarterly revenue/R&D-spend deltas pulled directly from SEC EDGAR's XBRL API (free, no auth) instead of relying solely on yfinance's `.info` snapshot fields, giving a more auditable and historically complete margin/growth trend than a single scraped number per sync.
8. **Supply-chain relationship graph** — model the customer/supplier relationships between tracked companies (e.g. TSM manufactures for NVDA and AMD; ASML/AMAT/LRCX supply TSM) as a small graph, and visualize how a move in one company's numbers ripples through the others — genuinely differentiated from any generic stock dashboard and directly tied to the "AI infrastructure" framing rather than treating the 12 tickers as an unrelated list.

---

## Possible Integration Points

- **Investment Research Platform (2026-06-10)** and **Investment Thesis Journal (2026-06-14)** — SiliconWatch's sector-comparative lens could feed a "thesis" entry in that tool for a specific ticker, closing the loop between sector research and a tracked personal conviction.
- **Morning Briefing (2026-06-22)** — a natural inclusion in that multi-source daily digest, since SiliconWatch's aggregates (top mover, avg margin) are already compact enough for a one-line summary.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Valuation-trend accumulation (P/E over time) only grows one point per calendar day of manual `sync` runs — it will look sparse without weeks of consistent use | Package `sync` as a scheduled Routine (see Future Feature #6) so the trend fills in automatically |
| `.info` field availability varies by ticker and can silently return `None` for a metric yfinance does track under a different key in some data-provider outages | Add a secondary field-name fallback list per metric (e.g. try `trailingPE` then `trailingPe`) if a future sync run shows unexpected gaps |
| No intraday/real-time price — this is an end-of-day research tool, not a trading terminal | Out of scope by design; documented in the PRD and Manual |
| The 12-company default list is US/ADR-listed only; several important AI-infra suppliers (e.g. SK Hynix, Samsung foundry) don't trade as simple US tickers | A `--config` override already supports adding any yfinance-resolvable ticker; a future build could add a curated "extended" list as a second default |
