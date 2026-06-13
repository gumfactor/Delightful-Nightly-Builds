# Future Features — Investment Watchlist Dashboard

> Ideas for extending this build. All of these are enhancements to a working tool, not prerequisites for usefulness.

---

## Quick Wins (under 2 hours each)

### 1. Auto-open in Browser
Add a `--open` flag that calls `webbrowser.open(output_path)` after writing the HTML file. Zero user friction — one command to check the dashboard.

### 2. Watchlist Groups / Sectors
Add an optional `"group"` field to each `watchlist.json` entry (e.g., `"group": "AI Infrastructure"`). The renderer inserts a section header row when the group changes, turning a flat list into a grouped table.

### 3. Pre-market / After-hours Indicator
yfinance provides `preMarketPrice`, `postMarketPrice`, and their change fields. Display these in a secondary badge on each row so the user can see extended-hours moves before the main session opens.

### 4. Watchlist from CLI Flag
Accept ticker symbols directly on the command line (`python3 main.py AAPL MSFT NVDA`) as an alternative to `watchlist.json`, making one-off lookups instant.

### 5. Analyst Rating Consensus
yfinance exposes `recommendationMean` (1=Strong Buy → 5=Strong Sell) and `recommendationKey` (e.g., "buy"). Add a column showing the consensus rating badge alongside the analyst target price.

---

## Medium Scope (half a day each)

### 6. Historical Sparklines
For each ticker, fetch the last 30 days of daily close prices with `yf.Ticker(symbol).history(period="1mo")` and render a tiny inline SVG sparkline in the table row. No external chart library needed — pure SVG path elements.

### 7. Portfolio Mode
Add an optional `"shares"` and `"cost_basis"` field to watchlist entries. The dashboard then shows: current position value, total return $, total return %, and unrealized gain/loss per holding, plus a portfolio-level summary at the top.

### 8. Daily Snapshot Archive
Save a timestamped JSON snapshot of fetched prices to `output/snapshots/YYYY-MM-DD.json` each time the script runs. A separate `python3 history.py` command reads the archive and renders a weekly or monthly performance chart — day-over-day changes without relying on yfinance historical data.

---

## Ambitious Extensions

### 9. Claude Code Routine (Scheduled Morning Briefing)
Package the dashboard generation as a Claude Code Routine that runs automatically at 08:00 local time each weekday. The Routine fetches data, generates the HTML, and optionally posts a summary to a Slack channel or writes a `BRIEFING.md` note in the user's journal folder.

### 10. SEC EDGAR Earnings Calendar Integration
Cross-reference each watchlist ticker with the SEC EDGAR earnings calendar API to flag upcoming earnings dates. Add an "Earnings" column showing days-until-next-report, and highlight rows where earnings are within 7 days — so the user knows when to watch for elevated volatility.
