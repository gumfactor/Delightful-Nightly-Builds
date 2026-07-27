# Manual — SiliconWatch

> **Version:** 1.0 (built 2026-07-27)
> **Complexity:** Ambitious Project

---

## What This Is

SiliconWatch is a local dashboard that compares the companies building the AI compute stack — GPUs/accelerators, foundry, chip equipment, memory, and analog/IP — on valuation, profitability, and price momentum, side by side. It fetches live data from Yahoo Finance (via `yfinance`, free and no API key required), stores it locally in SQLite so a real multi-week history accumulates the more you use it, and renders a self-contained dark-mode HTML dashboard you open directly in a browser. An optional Claude Haiku call can turn the numbers into a short plain-English sector narrative; without an API key, a deterministic template does the same job.

---

## Quick Start

1. `cd builds/2026-07-27-siliconwatch`
2. `pip install -r requirements.txt`
3. `python3 src/main.py sync` — fetches live data for the default 12-company universe and stores it in `./siliconwatch.db`
4. `python3 src/main.py report` — renders `./siliconwatch_report.html`
5. Open `siliconwatch_report.html` in any browser

---

## How to Use It

### `sync` — fetch and store live data

```
python3 src/main.py sync [--db PATH] [--tickers TICKER,TICKER,...] [--config PATH]
```

- Run this regularly (daily or weekly) — each run adds a new dated snapshot row per ticker to the local database, which is what powers the "sector P/E over time" trend chart. Running it twice on the same day updates that day's row rather than creating a duplicate.
- `--tickers NVDA,AMD` restricts the sync to just those tickers (still pulled from the default/config universe's metadata when available; any ticker not already in the universe gets a generic "Custom" subsector label).
- `--config path/to/tickers.json` replaces the default 12-company universe with your own list. Format:
  ```json
  [
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "subsector": "GPU / AI Accelerators"}
  ]
  ```

### `report` — render the dashboard

```
python3 src/main.py report [--db PATH] [--output PATH] [--ai]
```

- Reads everything from the local database — no network access needed to view a previously-synced report.
- `--ai` attempts a Claude Haiku sector-narrative call using your `ANTHROPIC_API_KEY` environment variable. Without `--ai`, or if the key is missing/the call fails, a deterministic template narrative is used instead and clearly labeled as such in the dashboard.

### `list` — see the configured universe

```
python3 src/main.py list [--config PATH]
```

Prints each ticker, its sub-sector, and company name.

### The Dashboard

- **KPI cards** — total market cap, average trailing P/E, average profit margin, and company count across the currently-synced universe.
- **Sector Comparison charts** — market cap and profit margin bar charts, colored by sub-sector.
- **Companies table** — sortable (click any column header) and searchable (type in the box), with 1-day and 1-year price change, P/E, PEG, and analyst-target upside.
- **Sub-sector filter chips** — click a chip to show only that sub-sector's rows; click it again to clear the filter.
- **Price History** — pick any ticker from the dropdown to see its trailing daily-close chart.
- **Sector P/E Over Time** — appears once you've run `sync` on at least two different days; shows the average trailing P/E trend across your sync history.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db` | `siliconwatch.db` (current directory) | SQLite database path used by both `sync` and `report` |
| `--output` | `siliconwatch_report.html` | Path the `report` command writes the dashboard to |
| `--tickers` | full default universe | Comma-separated ticker list to restrict a `sync` run to |
| `--config` | built-in 12-company list | Path to a JSON file of `{ticker, name, subsector}` objects to use instead of the default universe |
| `--ai` | off | When set on `report`, attempts a Claude Haiku narrative using `ANTHROPIC_API_KEY` from the environment |

`ANTHROPIC_API_KEY` — set this environment variable before running `report --ai` to get an AI-written sector narrative. Not required otherwise; the tool is fully functional without it.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `report` says "No data yet — run `sync` first." | You ran `report` before ever running `sync` against that `--db` path | Run `sync` first, or check you're pointing `--db` at the same file you synced into |
| Every metric in the dashboard shows "—" | `yfinance` couldn't reach Yahoo Finance (network issue, or a ticker was delisted/renamed) | Check your internet connection; `sync` prints a warning listing which tickers returned no price data |
| Charts don't render, but tables of the same data appear instead | The Chart.js CDN (`cdn.jsdelivr.net`) was unreachable from your browser/network | This is the intended graceful fallback — the data is all there, just in table form. Check your network/firewall if you expect the charts |
| `Config error: Config file not found: ...` | A typo in the `--config` path, or the file wasn't created yet | Double-check the path; see the `--config` JSON format above |
| The AI narrative panel shows a template-style paragraph even with `--ai` set | `ANTHROPIC_API_KEY` isn't set, or the Anthropic API call failed | Confirm the environment variable is exported in the shell you're running from; the fallback is intentional and the dashboard labels which one you're seeing |

---

## Known Limitations

- End-of-day data only — this is a research/tracking tool, not a real-time trading terminal.
- The valuation/margin trend chart needs multiple days of `sync` history to become meaningful; a single run only shows one data point (the price-history chart, by contrast, is populated from day one since `yfinance` returns a full year of history per fetch).
- The default 12-company universe is US-listed/ADR tickers only; use `--config` to track additional companies `yfinance` can resolve.
- No portfolio or personal-holdings tracking — this tool compares public companies at the sector level, not a personal position. For personal holdings, see the existing Investment Research Platform (2026-06-10).
