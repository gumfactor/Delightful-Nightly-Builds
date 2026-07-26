# Manual — TripKit

TripKit is a command-line tool that turns a trip's destination, dates, and activity type into a weather-aware packing checklist, plus a self-contained HTML dashboard you can open on your phone.

## Setup

```bash
cd builds/2026-07-26-tripkit-trip-prep-planner
python3 -m pip install -r requirements.txt   # only installs pytest; the CLI itself is stdlib-only
```

Optional: to get an AI-written trip briefing instead of the deterministic template, set your own key before running:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

No key is required — TripKit works fully offline/without a key, using a deterministic briefing template instead.

## Commands

All commands are run from the build folder as `python3 src/main.py <command> ...`.

### Add a trip

```bash
python3 src/main.py add \
  --name "ICON Conference" \
  --destination "Boston" \
  --start 2026-08-15 \
  --end 2026-08-17 \
  --tags conference,business
```

- `--destination` is free text; it's resolved via live geocoding to a city/region/country and coordinates.
- `--start`/`--end` are `YYYY-MM-DD`. If the start date is within 16 days, TripKit fetches a real forecast; further out, it fetches and averages the same calendar dates from the last 5 years as a "historical average" estimate — clearly labeled as such, not a forecast.
- `--tags` is a comma-separated list from: `conference, cottage, boating, golf, outdoor, business, leisure`. At least one is required.

### List trips

```bash
python3 src/main.py list
```

### Show a trip's briefing and packing list

```bash
python3 src/main.py show 1
```

### Refresh weather for an existing trip

Useful once a far-future trip enters the 16-day forecast window and you want the real forecast instead of the historical estimate:

```bash
python3 src/main.py refresh 1
```

### Delete a trip

```bash
python3 src/main.py delete 1
```

### Generate the dashboard

```bash
python3 src/main.py dashboard
```

Writes `output/dashboard.html` — a single self-contained file (only external dependency is the pinned Chart.js CDN script tag). Open it directly:

```bash
open output/dashboard.html      # macOS
xdg-open output/dashboard.html  # Linux
```

or just double-click it / drag it into a browser tab. It's mobile-readable and works over `file://` with no local server needed.

Checking off packing items in the dashboard saves state in your browser's `localStorage`, so it survives a reload — but it's per-browser/per-device, not synced. Re-running `dashboard` regenerates the HTML without losing your checked-off state (the checkboxes are keyed by trip id + item, not by anything that changes on regeneration).

## Data

Everything is stored locally in `output/tripkit.db` (SQLite) — nothing leaves your machine except the destination name (sent to Open-Meteo's free geocoding API), the coordinates (sent to Open-Meteo's forecast/archive APIs), and — only if you've set `ANTHROPIC_API_KEY` — the trip name, destination, dates, and weather summary (sent to the Anthropic API for the briefing paragraph).

## Running the tests

```bash
python3 -m pytest tests/ -v
```

43 tests, all network calls mocked — no live API access required to test.
