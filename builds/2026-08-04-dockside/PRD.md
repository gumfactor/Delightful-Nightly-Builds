# PRD — Dockside: Cottage & Boat Season Readiness Dashboard

> **Build date:** 2026-08-04
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious Project
> **Day of week:** Tuesday (every build is ambitious per CLAUDE.md)

---

## Goal

A CLI tool that tracks recurring cottage/boat seasonal maintenance tasks and scores each one's real-world readiness against live Open-Meteo weather and marine forecast data (dry-day streaks, wind, frost, water temperature), rendering a self-contained HTML dashboard of task readiness and a general boating-comfort outlook.

## User Story

As a cottage- and boat-owning professional who values evidence over guesswork and wants life-admin friction reduced without another thing to remember to check manually, I want to define my recurring seasonal tasks once (dock installation, dock removal, winterizing, engine service) and have the tool tell me, using real forecast data for my actual location, which of them are ready to do this week and which are blocked and why — so that I stop either doing dock work in a windstorm or missing the dry-window before a task becomes overdue.

## Scope

### In Scope
- Multi-site configuration: name a site (e.g. "Cottage Dock") and resolve its location either by place name (geocoded via the free Open-Meteo Geocoding API) or explicit latitude/longitude
- Recurring seasonal task definitions: name, category (dock / boat / water_system / structure / other), a target month window (e.g. April–May), and weather constraints — max wind speed, minimum consecutive dry days, minimum water temperature, frost-free requirement — any subset of which a task may specify
- `sync`: fetches a 7-day forecast (Open-Meteo Forecast API) and, best-effort, marine data (Open-Meteo Marine API — wave height, wave period, and hourly sea-surface temperature resampled to a daily midday value) for every configured site, persists deduplicated daily observations in local SQLite, and prints a terminal readiness summary
- Deterministic readiness scoring engine (no AI, no black box): for each active task, evaluates every day in the current 7-day window against the task's constraints, finds the earliest day (if any) satisfying all of them, and classifies the task as one of `ready_now` / `ready_soon` / `not_ready` / `overdue` / `off_season` / `done_this_season`, with a per-constraint pass/fail/**unknown** breakdown (unknown when marine data isn't available for that site)
- A separate general-purpose deterministic "boating comfort score" (0–100) per site per day, combining wind, wave height (if available), precipitation, and air temperature — independent of any specific maintenance task, answering "is this a nice day to be on the water" rather than "can I do task X"
- `complete`: marks a task done for the current season and automatically schedules its next occurrence (handles month/day rollover and leap years)
- Self-contained dark-mode HTML dashboard (`render`) — per-site boating-outlook chart, 7-day weather trend chart (Chart.js 4.4.4, pinned CDN version, graceful text-table fallback if the CDN is blocked), and task readiness cards showing status badge, best available day, and the itemized constraint breakdown
- Optional Claude Haiku season-readiness briefing (`brief`) using a user-supplied `ANTHROPIC_API_KEY` runtime environment variable; an unconditional deterministic template fallback makes zero network calls when no key is set
- `init` / `add-site` / `add-task` / `list-sites` / `list-tasks` CLI commands to configure everything above
- pytest suite with every external HTTP call (Open-Meteo geocoding/forecast/marine, Anthropic API) mocked

### Out of Scope
- Editing sites/tasks from the HTML dashboard — the dashboard is a static, read-only snapshot; all mutation is CLI-only
- Calendar/push-notification integration
- Multi-user accounts or authentication
- Marina/dock booking or reservation systems
- Multi-year historical trend charts (only the current season's live state is meaningfully charted in v1 — see FutureFeatures.md)
- Southern-hemisphere season-window inversion (the month-window model assumes a Northern Hemisphere calendar, matching the user's Ontario, Canada location)

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`urllib.request` for all HTTP — Open-Meteo and Anthropic — `sqlite3` for persistence, `argparse` for the CLI, `json`, `html`, `datetime`)
- **Runtime requirement:** `python3 src/main.py <command>` — no install step, no virtualenv required beyond a stock Python 3 interpreter

## Data Structure

Local SQLite database at `dockside.db` (created by `init`, in the build folder — never referenced outside it):

```sql
CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    place_name TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    marine_available INTEGER,     -- NULL until first sync attempt; 0/1 after
    created_at TEXT NOT NULL
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    name TEXT NOT NULL,
    category TEXT NOT NULL,        -- dock | boat | water_system | structure | other
    window_start_month INTEGER NOT NULL,  -- 1-12
    window_end_month INTEGER NOT NULL,    -- 1-12
    max_wind_kmh REAL,             -- NULL = no constraint
    min_water_temp_c REAL,
    dry_days_required INTEGER,
    frost_free_required INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    season_year INTEGER NOT NULL,
    completed_date TEXT NOT NULL,
    UNIQUE(task_id, season_year)
);

CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    obs_date TEXT NOT NULL,        -- YYYY-MM-DD
    temp_min_c REAL,
    temp_max_c REAL,
    precip_mm REAL,
    wind_speed_max_kmh REAL,
    wave_height_max_m REAL,        -- NULL if marine unavailable
    water_temp_c REAL,             -- NULL if marine unavailable
    fetched_at TEXT NOT NULL,
    UNIQUE(site_id, obs_date)      -- dedupe: re-sync upserts, never duplicates
);

CREATE TABLE briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    generated_at TEXT NOT NULL,
    source TEXT NOT NULL,          -- 'ai' | 'template'
    text TEXT NOT NULL
);
```

## Folder Structure

```
builds/2026-08-04-dockside/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── conftest.py             ← adds src/ to sys.path for pytest (flat-import, no packaging)
├── src/
│   ├── main.py             ← CLI entry point (argparse subcommands)
│   ├── db.py               ← schema + CRUD + dedupe/upsert logic
│   ├── weather_client.py   ← Open-Meteo geocoding/forecast/marine HTTP clients
│   ├── scoring.py          ← pure readiness + boating-comfort scoring (no I/O)
│   ├── ai_brief.py         ← Anthropic API call + deterministic fallback
│   └── render.py           ← self-contained HTML dashboard generator
└── tests/
    ├── test_scoring.py
    ├── test_db.py
    ├── test_weather_client.py
    ├── test_ai_brief.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Dry-day-streak detection across a 7-day window (streak present, streak too short, streak spanning the whole window)
  - Per-constraint pass/fail/unknown evaluation (wind, frost, water temp) including the "unknown" path when marine data is null
  - Full task status classification across all six states (`ready_now`, `ready_soon`, `not_ready`, `overdue`, `off_season`, `done_this_season`)
  - Boating comfort score bounds (0–100) and directional correctness (calmer/drier/warmer days score higher)
  - SQLite dedupe: re-syncing the same site/date does not create duplicate observation rows, and updates the stored values
  - Completion scheduling correctly rolls to next season, including December→January and leap-year edge cases
  - Geocoding/forecast/marine URL construction and JSON response parsing, including a response with missing/empty marine fields (graceful `marine_available = 0`, no crash)
  - HTTP error handling (mocked non-200 response) does not crash `sync`
  - AI briefing: mocked successful Anthropic call, mocked failed call falling back to template, and the no-API-key path asserted to make **zero** network calls
  - HTML rendering escapes a script-injection payload placed in a site or task name (rendered as inert text, not executed markup)
  - CLI integration: `init` creates the schema; `add-site` geocodes via a mocked client; `add-task` rejects an invalid month (e.g. 13); `sync` end-to-end with a mocked weather client persists and prints a summary; `complete` records a completion and schedules next season

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. Given synthetic 7-day observation data and a task's constraints, the scoring engine correctly identifies the earliest fully-satisfying day, or correctly reports `not_ready`/`overdue` with an itemized list of which constraints failed — verified by hand-computed unit tests
3. Re-running `sync` for the same site and date range never creates duplicate observation rows, and `render` produces a self-contained HTML file that opens standalone (`file://`) and reflects the latest synced readiness state for every active task
4. The tool degrades gracefully — a site with no marine data available shows marine-dependent constraints as "data unavailable" rather than crashing or silently treating them as passed, and `brief` with no `ANTHROPIC_API_KEY` produces a deterministic template with zero network calls (asserted via mock call count)
5. All user-supplied text (site/task names) is HTML-escaped in the rendered dashboard — verified by a test asserting a `<script>` payload in a task name renders as inert text

---

## Scope Changes

None — full scope as planned above was delivered. (If this changes during the build, this section will be updated before commit.)
