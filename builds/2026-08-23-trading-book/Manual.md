# Manual — Trading Book

A live dashboard of your real Interactive Brokers account: net liquidation, cash, P&L, and every open position, pulled straight from your own locally running TWS or IB Gateway session. Read-only — this tool never places, modifies, or cancels an order.

## 1. One-time setup

1. **Enable the API in TWS or IB Gateway.**
   In TWS: *File → Global Configuration → API → Settings* — check "Enable ActiveX and Socket Clients", and add `127.0.0.1` to "Trusted IPs" if it isn't already there. Leave "Read-Only API" checked if you want an extra guarantee this tool can never place an order.
   Note the **Socket port**: TWS defaults to `7497` for paper trading accounts and `7496` for live accounts; IB Gateway defaults to `4002` (paper) and `4001` (live).
2. **Install the Python dependency** (on your own machine, not in this build container):
   ```bash
   cd builds/2026-08-23-trading-book
   pip install -r requirements.txt
   ```
3. Leave TWS or IB Gateway running and logged in whenever you want to sync.

## 2. Daily use

```bash
# Pull today's account snapshot (defaults to TWS paper port 7497)
python main.py sync

# ...or point at a different host/port/client ID:
python main.py sync --port 7496 --client-id 2

# Print the latest snapshot to the terminal
python main.py show

# Print the day-over-day net-liquidation trend
python main.py history --days 14

# Build dashboard.html
python main.py render

# ...with an optional one-paragraph AI portfolio note (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-...
python main.py render --ai-briefing
```

Open `dashboard.html` directly in any browser (double-click it, or `open dashboard.html` / `xdg-open dashboard.html`) — no server required.

Running `sync` more than once on the same day updates that day's snapshot in place rather than creating a duplicate, so `history`/`render` always show one clean point per day, however many times you sync.

## 3. What the dashboard shows

- **Hero stats** — net liquidation, total cash, unrealized P&L, realized P&L, and today's day-over-day % change (red/green).
- **Net Liquidation Trend** — a line chart of your account value across every day you've synced. Falls back to a plain table automatically if the Chart.js CDN is unreachable (confirmed live in this build's own container, where it genuinely is).
- **Allocation by Asset Class** — a donut chart of market value by security type (stocks, options, futures, cash, etc.), with the same table fallback.
- **Positions** — every open position, sortable by clicking a column header and filterable with the search box.
- **Portfolio Note** *(optional, `--ai-briefing`)* — a one-paragraph plain-English note from Claude Haiku, built only from percentages (day-over-day change, allocation shares, top movers) — your account ID and dollar figures are never sent. Without `ANTHROPIC_API_KEY` set, this is a short deterministic sentence instead, and no network call is made at all.

## 4. Data & privacy

Everything lives in `trading_book.db` (SQLite) inside this folder — nothing leaves your machine except the optional Anthropic API call described above, which only ever receives aggregate percentages.

## 5. Running the tests

```bash
cd builds/2026-08-23-trading-book
pip install pytest   # if you don't already have it
python -m pytest tests/ -v
```

All 41 tests run against fakes and fixtures — no real TWS/IB Gateway connection or `ANTHROPIC_API_KEY` is required.

## 6. Troubleshooting

- **"Sync failed: Could not connect to TWS/IB Gateway..."** — make sure TWS or IB Gateway is open, logged in, and the API is enabled (Step 1 above), and that `--port` matches what you configured there.
- **Dashboard shows "No snapshot yet"** — run `python main.py sync` at least once before `render`.
- **Chart.js charts don't appear** — check your internet connection; the dashboard falls back to plain tables automatically, so this never blocks you from reading your numbers.
