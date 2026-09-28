# PRD — Outdoor Ops

> **Build date:** 2026-09-28
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious

---

## Goal

A local dashboard that turns live Open-Meteo weather and air-quality forecasts into daily running and golf suitability scores for the coming week, so the user can pick the best day for each activity at a glance instead of mentally converting raw forecast numbers.

## User Story

As a distance runner and golfer who also tracks air quality and weather-sensitive outdoor plans, I want a single dashboard that scores each of the next 7 days for running and for golf using real forecast and air-quality data, so that I can decide at a glance which day to run hard, which day to play, and which day to stay in — without opening a weather app and doing the mental math myself.

## Scope

### In Scope
- `sync` command: fetches a 7-day daily forecast (temp, precipitation probability/amount, wind, wind gusts, UV index) from the Open-Meteo Forecast API, and hourly US AQI + PM2.5 from the Open-Meteo Air Quality API (aggregated to daily max/mean), for a configurable lat/lon (default: Toronto, matching the user's home timezone).
- Deterministic, documented suitability scoring engine (0–100) for **running** and **golf**, each a weighted combination of temperature comfort, wind, precipitation probability, air quality (US AQI), and UV index — with activity-specific ideal ranges and weights (golf penalizes wind and rain harder; running penalizes heat and AQI harder).
- SQLite persistence in the build folder: each `sync` upserts one row per (location, forecast date, sync day) — re-running `sync` the same UTC day updates that day's snapshot in place; running it again the next day adds a new snapshot, so a genuine multi-day forecast history accumulates over repeated real use.
- `render` command: generates a single self-contained dark-mode HTML dashboard from the latest synced data — hero cards (today's running/golf score, this week's best day for each), a 7-day temperature/precipitation chart, a 7-day wind/AQI chart, and a per-day score table with the underlying factors.
- `demo` command: renders the dashboard from a bundled fixture snapshot with zero network calls, for verification and as a way to see the tool work without waiting on a real API call.
- Optional AI "Coach's Note": if `ANTHROPIC_API_KEY` is set at `render` time, sends only the computed aggregate summary (best/worst day per activity, the limiting factor, no personal data) to Claude Haiku for a 2–3 sentence note. With no key, a deterministic template generates the same kind of note from the same aggregate summary — zero network calls.
- Mobile-responsive, dark-mode dashboard; light-mode variables included per STANDARDS.

### Out of Scope
- Boating/cottage suitability — already covered by Wake Log (2026-09-22); Outdoor Ops covers running and golf only.
- Garmin Connect integration — PROFILE.md notes no live Garmin API (CSV-export only); out of reach for a live-data build.
- Multiple saved locations / location search UI — one configurable location per sync, set via CLI flag or config, no in-browser location picker.
- Historical-forecast-accuracy analysis (comparing what was predicted for a date vs. what actually happened) — the schema supports it (multiple snapshots per forecast date), but the dashboard UI for it is a future feature, not tonight's scope.
- Hourly-resolution scoring — daily aggregates only.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None (stdlib `urllib`, `sqlite3`, `argparse`, `html`, `json`, `datetime`)
- **Dependencies:** stdlib only for the core engine. Chart.js 4.4.4 via pinned CDN URL inside the generated HTML (no bundler, no npm).
- **Runtime requirement:** `python3 main.py sync` then `python3 main.py render` (or `python3 main.py demo` for a zero-network preview), then open the generated `outdoor_ops.html` in a browser. No install step beyond Python 3.

## Data Structure

**SQLite** (`outdoor_ops.db`, created in the build folder on first `sync`):

```sql
CREATE TABLE forecast_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    forecast_date TEXT NOT NULL,      -- YYYY-MM-DD, the day this row describes
    sync_day TEXT NOT NULL,           -- YYYY-MM-DD, the UTC day the sync ran
    fetched_at TEXT NOT NULL,         -- full ISO 8601 timestamp of the sync
    temp_max REAL, temp_min REAL,
    precip_prob_max REAL, precip_sum REAL,
    wind_max REAL, windgust_max REAL,
    uv_index_max REAL,
    weathercode INTEGER,
    aqi_max REAL, aqi_mean REAL, pm25_mean REAL,
    running_score REAL NOT NULL,
    golf_score REAL NOT NULL,
    UNIQUE(location_name, forecast_date, sync_day)
);
```

`sync` performs `INSERT ... ON CONFLICT(location_name, forecast_date, sync_day) DO UPDATE` (upsert), so a second sync the same day refreshes that day's numbers in place, while a sync on a later day adds new rows and preserves the earlier ones — the same per-day dedup pattern used elsewhere in this catalog (CanEcon Pulse, SiliconWatch).

`render` reads, for each `forecast_date`, the row with the most recent `sync_day`/`fetched_at` (the latest snapshot), builds a 7-day list, computes the aggregate summary, and writes it into the HTML template.

## Folder Structure

```
builds/2026-09-28-outdoor-ops/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── weather_client.py
│   ├── air_quality_client.py
│   ├── scoring.py
│   ├── storage.py
│   ├── ai_note.py
│   ├── dashboard.py
│   ├── summary.py
│   ├── fixtures.py
│   └── cli.py
└── tests/
    ├── __init__.py
    ├── test_weather_client.py
    ├── test_air_quality_client.py
    ├── test_scoring.py
    ├── test_storage.py
    ├── test_ai_note.py
    ├── test_summary.py
    ├── test_dashboard.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Scoring engine: boundary values for each factor (temp inside/outside ideal range, wind at/over threshold, precip at/over threshold, each AQI tier, UV at/over threshold), composite weighting for both running and golf, and that scores are always clamped to [0, 100].
  - Weather client: request URL/params construction, successful response parsing into the expected daily records, and error handling for a non-200 response and malformed JSON — all via an injected fake HTTP transport, never a real network call.
  - Air quality client: hourly-to-daily aggregation (max/mean grouping by date), partial/missing-hour handling, and the same error-handling coverage as the weather client.
  - Storage: schema creation, same-sync_day upsert (no duplicate row), a later sync_day creating a new row and preserving the earlier snapshot, and reading back the latest-per-date view.
  - AI note: deterministic fallback output when no API key is set (zero network calls, verified via a transport that raises if called), and the Anthropic-call path with a mocked HTTP client returning a stub response.
  - Dashboard: HTML generation escapes a hostile location-name string (XSS check), includes the pinned Chart.js version, and renders correctly with an empty/short (<7-day) dataset without crashing.
  - CLI: argument parsing for `sync`, `render`, and `demo`, and that `demo` produces a dashboard file with zero network calls.

## Success Criteria

1. All tests pass (zero failures).
2. Running and golf suitability scores are computed from real forecast + air-quality fields via a documented, deterministic formula — not mocked or hardcoded per day.
3. The dashboard is a genuine visual interface (hero cards + at least 2 charts + a data table), satisfying Category A's hard requirement — not a CLI that prints to stdout.
4. `sync` persists real state to local SQLite that survives and accumulates across repeated runs (verified by the upsert/accumulate tests).
5. The optional AI layer has a fully working, zero-network fallback so the tool is complete and useful without any API key.

---

## Scope Changes

None — the scope above was built as planned. (See BUILD_LOG.md for any minor adjustments discovered during implementation.)
