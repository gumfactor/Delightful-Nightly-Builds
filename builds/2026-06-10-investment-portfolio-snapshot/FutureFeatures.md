# Future Features — Investment Research Platform

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Configurable output path via watchlist.json** — Add an optional `"output"` key to `watchlist.json` so users can specify the output path without a CLI flag, making it easier to use as a cron job.

2. **Multi-note thesis view** — The report currently shows only the latest thesis note per ticker. An expandable UI (click to reveal) or secondary section could show all historical notes, making it easy to track how your thesis evolved over time.

---

## Medium Effort (roughly one nightly build session)

3. **Historical snapshot archive** — When generating a report, save a timestamped copy to `snapshots/YYYY-MM-DD.html` in addition to overwriting `report.html`. Add a simple index HTML listing all past snapshots, so price changes can be reviewed over time even without a database.

4. **Thesis export** — `python3 main.py export` writes a Markdown or CSV summary of all thesis notes, suitable for pasting into a research journal or sharing with a collaborator.

---

## Ambitious Extensions (multi-session effort)

5. **Week-over-week delta view** — Compare today's snapshot to a saved previous snapshot and add a "vs. last week" column showing price change since the last archived snapshot. Requires the snapshot archive (feature 6) and a diff function between two report datasets.

6. **Analyst target price and news integration** — Pull analyst consensus target price and the 3 most recent news headlines for each ticker via the Yahoo Finance API (both available via yfinance). Add a collapsible "news" row under each ticker in the report, giving the snapshot a morning briefing character rather than just price data.

---

## Possible Integration Points

- **2026-06-06 — AI Session Context Bridge (ctxlog):** A daily portfolio snapshot could be automatically included in ctxlog's session context document — so every AI coding session starts with awareness of that day's market state. Link the two tools via a daily hook that regenerates the snapshot and updates the context bridge.
- **The `TickerData` dataclass and `fetch_ticker()` in `src/fetcher.py`** are clean enough to import as a data layer in future investment-related builds — screeners, performance trackers, or earnings calendars could all reuse this fetching layer without duplicating the yfinance wrapper.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Yahoo Finance API is blocked in the nightly build environment (HTTP 403) | The tool works correctly when run from the user's machine; no code fix needed, but a note in the Manual explains this |
| No rate limiting between ticker fetches | Add a short `time.sleep(0.5)` between requests to avoid being throttled on large watchlists |
| Canadian tickers (`.TO`) may return CAD prices, but the 52W range doesn't label currency | Add currency suffix to the 52W range string for non-USD tickers |
| Thesis column in report shows only the latest note | See Future Feature #5 for multi-note expansion |
