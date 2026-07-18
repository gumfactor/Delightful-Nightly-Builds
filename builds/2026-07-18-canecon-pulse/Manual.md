# Manual — CanEcon Pulse

> **Version:** 1.0 (built 2026-07-18)
> **Complexity:** Ambitious Project

---

## What This Is

CanEcon Pulse is a small local tool that tracks five Canadian macroeconomic indicators — the USD/CAD and EUR/CAD exchange rates, the Bank of Canada's policy interest rate, national CPI, and the national unemployment rate — by pulling live data from the free, public Bank of Canada Valet API and Statistics Canada's Web Data Service (no API key or signup required for either). Each time you run it, it adds any new data points to a local history file, then renders a dark-mode HTML dashboard with trend charts, the latest value, and day/week/month change badges for each indicator, plus a short plain-English briefing on what the movements mean for the relative cost of imported versus Canadian-made goods.

---

## Quick Start

1. From this folder, run: `python3 canecon_pulse.py run`
2. This fetches the latest data (`sync`) and writes a dashboard to `output/dashboard.html` (`render`).
3. Open `output/dashboard.html` in any browser — no server needed.
4. Run `python3 canecon_pulse.py run` again on a later day to add more history; the trend charts fill in over repeated runs.
5. (Optional) `export ANTHROPIC_API_KEY=sk-...` before running `render`/`run` to get an AI-written briefing instead of the template one.

---

## How to Use It

### `sync` — fetch and store the latest data

```
python3 canecon_pulse.py sync [--db output/canecon.db] [--recent 30]
```

Fetches up to `--recent` most recent observations for each of the 5 tracked indicators and stores any new ones in the local SQLite database. Already-stored dates are skipped automatically — running `sync` repeatedly is always safe and never creates duplicates. If any single indicator's API call fails (network issue, changed endpoint, etc.), that indicator is skipped with a `[skip]` message and every other indicator still syncs normally.

### `show` — quick terminal check

```
python3 canecon_pulse.py show [--db output/canecon.db]
```

Prints the latest value and day/week/month deltas for every indicator with stored history, without opening a browser. Useful for a fast daily glance.

### `render` — build the HTML dashboard

```
python3 canecon_pulse.py render [--db output/canecon.db] [--out output/dashboard.html] [--no-ai]
```

Builds `output/dashboard.html` from whatever history is currently stored (does not fetch new data — run `sync` first). If `ANTHROPIC_API_KEY` is set in the environment, the briefing panel is AI-generated via Claude Haiku; pass `--no-ai` to always use the deterministic template instead, or leave the key unset to get the same effect.

### `run` — sync + render in one step

```
python3 canecon_pulse.py run [--db output/canecon.db] [--out output/dashboard.html] [--recent 30] [--no-ai]
```

The command you'll use most often — fetches fresh data and rebuilds the dashboard in one call.

### The Dashboard

Each indicator gets its own panel: the current value, three delta badges (day/week/month — a badge reads "n/a" when no comparison point exists yet in the stored history, e.g. before enough days have accumulated, or for monthly-frequency series like CPI where a day-over-day comparison doesn't meaningfully exist), a trend line chart, and a "last synced" timestamp. An indicator with no stored history yet shows a "No data yet — run sync" message instead of a broken chart.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db` | `output/canecon.db` | Path to the local SQLite history database |
| `--out` | `output/dashboard.html` | Path the HTML dashboard is written to |
| `--recent` | `30` | Number of most-recent observations to request per indicator on `sync` |
| `--no-ai` | off | Force the deterministic template briefing even if `ANTHROPIC_API_KEY` is set |
| `ANTHROPIC_API_KEY` (env var) | unset | When set, `render`/`run` use it to generate an AI briefing via Claude Haiku. Never required — the dashboard is fully functional without it. |

Tracked indicators (series IDs, labels, and units) are defined in `src/indicators.py` — add, remove, or correct one there if needed (see Known Limitations below).

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `[skip] ... no data returned` for every indicator on `sync` | No internet access, or the API host is blocked by a firewall/proxy | Check connectivity to `bankofcanada.ca` and `www150.statcan.gc.ca`; both are free, public, no-auth APIs and should be reachable from a normal home/office connection |
| One StatsCan panel (`Canada All-Items CPI` or `Canada Unemployment Rate`) always shows "No data yet" even after `sync` succeeds for other indicators | That indicator's StatsCan vector ID may be stale — this build's IDs were written from documentation, not verified against live traffic (see BUILD_LOG.md) | Look up the correct vector ID at statcan.gc.ca's table/vector browser and update it in `src/indicators.py` |
| Dashboard shows plain text tables instead of charts | The Chart.js CDN (`cdn.jsdelivr.net`) is unreachable from your network | This is a deliberate graceful-degradation fallback, not a bug — the data is still shown, just as text; check your network/firewall if you want charts |
| `render` says "No data yet" for every indicator | `sync` hasn't been run yet, or was run against a different `--db` path | Run `python3 canecon_pulse.py sync` first, and make sure `--db` matches between `sync` and `render` calls |

---

## Known Limitations

- The two Statistics Canada WDS vector IDs used (`v41690973` for CPI, `v2062815` for unemployment) could not be confirmed against live traffic during the build session — this container's egress policy denies outbound requests to both target APIs. They're written to match StatsCan's documented response schema, but the first real `sync` run is the first live verification. See the Troubleshooting table above if either panel stays empty.
- Trend richness depends entirely on how often you run `sync` over time — there is no historical backfill beyond what a single API call returns for the `--recent` window.
- The AI briefing is a single independent paragraph each time; it does not track how the assessment has changed run-to-run (see FutureFeatures.md).
- No alerting/notification — you have to open the dashboard or run `show` to notice a significant move.
