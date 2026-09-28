# Manual — Outdoor Ops

> **Version:** 1.0 (built 2026-09-28)
> **Complexity:** Ambitious

---

## What This Is

Outdoor Ops turns live weather and air-quality forecasts into a daily "should I run today, should I golf today" decision, for the next 7 days. It's a small Python CLI plus a self-contained HTML dashboard: `sync` pulls a real 7-day forecast (temperature, wind, precipitation, UV) and air-quality (US AQI) from Open-Meteo's free public APIs and stores it locally; `render` turns the latest sync into a dashboard with hero scorecards, two trend charts, and a full data table. There's also `demo`, which does the same thing with bundled sample data and zero network calls, so you can see it work immediately.

---

## Quick Start

1. `cd builds/2026-09-28-outdoor-ops`
2. `python3 main.py demo` — renders `outdoor_ops.html` from bundled sample data (no network needed, good first look).
3. Open `outdoor_ops.html` in a browser.
4. For real data: `python3 main.py sync` (fetches live Toronto forecast + air quality), then `python3 main.py render`.
5. Re-run `sync` + `render` daily (or wire it into a cron job / Claude Code Routine) to keep the dashboard current — each day's sync is stored, so a real history accumulates.

---

## How to Use It

### `sync` — fetch and store live conditions

```
python3 main.py sync [--location "City, ST"] [--lat 43.65] [--lon -79.38] [--days 7] [--db outdoor_ops.db]
```

Fetches a `--days`-day forecast for the given coordinates from Open-Meteo (forecast + air quality), scores every day for running and golf, and upserts it into the local SQLite database. Running `sync` again the same day updates that day's numbers in place; running it on a later day adds a new snapshot and keeps the earlier one, so you build a real multi-day history the more you use it.

### `render` — build the dashboard

```
python3 main.py render [--location "City, ST"] [--db outdoor_ops.db] [--out outdoor_ops.html]
```

Reads the latest synced snapshot for each of the next several days and writes a single self-contained HTML file: hero cards for today's running/golf scores and this week's best day for each, a temperature/precipitation chart, a wind/AQI chart, a score-trend chart, and a full table with every underlying factor. If `ANTHROPIC_API_KEY` is set in your environment, an AI-generated "Coach's Note" is included; otherwise a deterministic note built from the same numbers is used instead — either way, the dashboard is complete.

### `demo` — see it work with zero setup

```
python3 main.py demo [--db outdoor_ops.db] [--out outdoor_ops.html]
```

Same as `sync` + `render`, but reads bundled sample data (`src/fixtures.py`) instead of calling any API. Good for a first look, for offline use, or for verifying the tool still works after a change.

### Reading the scores

Both scores are 0–100 (higher is better), computed from temperature, wind, rain probability, air quality (US AQI), and UV index — weighted differently per activity (golf is hit harder by wind and rain; running is hit harder by heat and poor air quality). The exact thresholds and weights are documented, named constants in `src/scoring.py` — nothing is a black box.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--location` | `Toronto, ON` | Display name stored alongside each snapshot; also used as the lookup key for `render`. |
| `--lat` / `--lon` | `43.6532` / `-79.3832` | Coordinates sent to Open-Meteo. Change these to your own location. |
| `--days` | `7` | How many days ahead to sync (Open-Meteo supports up to 16). |
| `--db` | `outdoor_ops.db` | SQLite file path, created on first `sync`/`demo`. |
| `--out` | `outdoor_ops.html` | Where the dashboard HTML is written. |
| `ANTHROPIC_API_KEY` (env var) | unset | If set, `render` asks Claude Haiku for the Coach's Note. Without it, a deterministic template note is used — the dashboard is fully functional either way. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `sync` prints "Sync failed: ..." and exits with an error | Network unreachable, or Open-Meteo is down/rate-limiting | Check your internet connection and retry; Open-Meteo has no auth so this is almost always transient. |
| Dashboard shows "No data yet" | `render` was run before any `sync`/`demo`, or `--location` doesn't match what was synced | Run `sync` (or `demo`) first, and make sure `--location` matches exactly between `sync` and `render`. |
| Charts show a "Chart.js could not load" message instead of graphs | No internet access when the dashboard HTML was opened (Chart.js loads from a CDN) | Open the dashboard with internet access, or use the score table, which has the same data. |
| Coach's Note reads the generic template even though I set `ANTHROPIC_API_KEY` | The key wasn't exported in the shell that ran `render`, or the API call failed silently | Confirm `echo $ANTHROPIC_API_KEY` shows your key in the same shell, then re-run `render`. |

---

## Known Limitations

- One location per sync — no built-in way to track multiple cities in the same database view (see `FutureFeatures.md`).
- Daily-resolution scoring only; doesn't distinguish "good in the morning, bad in the afternoon."
- Scoring weights (what counts as "too windy" for golf, etc.) are fixed defaults, not personalized to how the user actually feels about conditions.
- Chart.js is loaded from a CDN — the dashboard degrades gracefully to a text-only fallback (score table only) if that CDN is unreachable, rather than showing a broken page.
