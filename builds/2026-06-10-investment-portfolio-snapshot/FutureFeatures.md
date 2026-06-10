# Future Features — Investment Portfolio Snapshot

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Open report automatically** — Add `--open` flag to `main.py` that calls `webbrowser.open(output_path)` after writing the file, so the report opens in the default browser immediately without a manual step.

2. **Currency column** — Add a "Currency" column to the table (USD/CAD) so mixed watchlists (US + TSX tickers) are visually clear without inferring from the ticker suffix.

3. **Sortable table** — Add a small inline JavaScript snippet (no CDN) to make table columns sortable on click by 1D Change or Market Cap — one `<script>` block of ~30 lines; useful for quickly scanning biggest movers.

4. **Configurable output path via watchlist.json** — Add an optional `"output"` key to `watchlist.json` so users can specify the output path without a CLI flag, making it easier to use as a cron job.

5. **Ticker grouping** — Add optional `"group"` field to each watchlist entry so rows can be visually separated into sections (e.g. "Core Positions", "Watchlist", "ETFs") with a group header row in the table.

---

## Medium Effort (roughly one nightly build session)

6. **Historical snapshot archive** — When generating a report, save a timestamped copy to `snapshots/YYYY-MM-DD.html` in addition to overwriting `report.html`. Add a simple index HTML listing all past snapshots, so price changes can be reviewed over time even without a database.

7. **Claude Code Skill: `/portfolio-check`** — Package this tool as a Claude Code Skill so the user can type `/portfolio-check` in any coding session to instantly generate and open a fresh portfolio snapshot. Involves creating a skill definition in `~/.claude/skills/portfolio-check.md` that runs `python3 main.py --open` in the build folder.

---

## Ambitious Extensions (multi-session effort)

8. **Week-over-week delta view** — Compare today's snapshot to a saved previous snapshot and add a "vs. last week" column showing price change since the last archived snapshot. Requires the snapshot archive (feature 6) and a diff function between two report datasets.

9. **Analyst target price and news integration** — Pull analyst consensus target price and the 3 most recent news headlines for each ticker via the Yahoo Finance API (both available via yfinance). Add a collapsible "news" row under each ticker in the report, giving the snapshot a morning briefing character rather than just price data.

---

## Possible Integration Points

- **2026-06-06 — AI Session Context Bridge (ctxlog):** A daily portfolio snapshot could be automatically included in ctxlog's session context document — so every AI coding session starts with awareness of that day's market state. Link the two tools via a daily hook that regenerates the snapshot and updates the context bridge.
- **Future investment research builds:** The `TickerData` dataclass and `fetch_ticker()` function in `src/fetcher.py` are clean enough to import as a data layer in future investment-related builds — screeners, performance trackers, or earnings calendars could all reuse this fetching layer.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Yahoo Finance API is blocked in the nightly build environment (HTTP 403) | The tool works correctly when run from the user's machine; no code fix needed, but a note in the Manual explains this |
| Fetch errors produce a low-information "argument of type 'NoneType' is not iterable" message | Add more specific exception handling in `fetch_ticker()` to surface yfinance-specific errors more clearly |
| No rate limiting between ticker fetches | Add a short `time.sleep(0.5)` between requests to avoid being throttled on large watchlists |
| Canadian tickers (`.TO`) may return CAD prices, which the formatter correctly handles, but the 52W range doesn't label currency | Add currency suffix to the 52W range string for non-USD tickers |
