# PRD — TripKit: Weather-Aware Trip Prep & Packing Planner

## Goal

Give the user a single command that turns "I'm going to X from date A to date B for [conference/cottage/boating/golf/...]" into a real-weather-informed, categorized packing checklist and trip briefing, so packing prep stops being a last-minute mental checklist.

## User Story

As someone who travels for conferences, cottage weekends, boating, and golf trips, I want to record a trip's destination, dates, and activity type and get back a packing list that actually reflects the weather I'll face there — not a generic "bring a jacket" checklist — so I stop either over-packing or forgetting weather-specific gear.

## Scope

### In Scope

- CLI to add/list/show/delete trips, each with a destination resolved via live geocoding, a date range, and one or more activity tags
- Live weather resolution with two modes, chosen automatically by date:
  - **Forecast mode** (trip starts within the next 16 days): real Open-Meteo daily forecast for the exact trip dates
  - **Climate-normal mode** (trip starts further out): Open-Meteo historical archive data averaged across the same calendar dates in the previous 5 years, clearly labeled as a historical estimate, not a forecast
- Deterministic packing rule engine producing a categorized list (Clothing, Gear, Documents & Admin, Health & Comfort) driven by temperature band, precipitation, wind, trip duration, activity tags, and whether the destination country differs from Canada
- Optional AI trip briefing via Claude Haiku (`ANTHROPIC_API_KEY` read from the environment at runtime) that turns the structured weather + packing data into a short natural-language paragraph; a deterministic template produces the same kind of paragraph when no key is set or the call fails
- SQLite persistence of trips and their most recent weather snapshot, so `dashboard`/`show` don't require re-fetching every run
- Self-contained dark-mode HTML dashboard: one card per trip (soonest first), a Chart.js daily temperature/precipitation chart, the categorized packing list with checkboxes (check-state persisted client-side via `localStorage`, keyed by trip id), and the AI-or-template briefing text
- `refresh` command to re-fetch weather for an existing trip (e.g. once a far-future trip enters the 16-day forecast window)

### Out of Scope

- Currency/exchange-rate info for international trips (a plausible companion feature, but not essential to packing prep — cut to keep this build's core weather↔packing logic reliable rather than shipping a shallow second data source; see FutureFeatures.md)
- Flight/itinerary booking data or calendar integration (no credentialed data source for this exists in PROFILE.md)
- Multi-user or account sync — this is a single local SQLite file
- Editing an existing trip's fields after creation (delete + re-add covers this at v1 scope)

## Tech Stack

- Python 3.11+, standard library only (`urllib.request` for HTTP, `sqlite3` for storage, `argparse` for the CLI, `datetime`, `html`, `json`) — no third-party runtime dependency, so `requirements.txt` is intentionally empty of runtime deps and lists only `pytest` for testing
- Chart.js `4.4.4` via pinned CDN URL in the generated HTML (matches the version already proven across this repo's other dashboards)
- Anthropic API (optional, runtime-only, via `urllib` — no `anthropic` SDK dependency needed for a single-call use case)
- pytest for tests, with every network call (Open-Meteo geocoding, forecast, archive; Anthropic) mocked

## External APIs

| API | Auth | Purpose | Called in tests? |
|-----|------|---------|-------------------|
| Open-Meteo Geocoding (`geocoding-api.open-meteo.com/v1/search`) | None | Resolve a typed destination to lat/lon + country | No — mocked |
| Open-Meteo Forecast (`api.open-meteo.com/v1/forecast`) | None | Daily forecast for trips within 16 days | No — mocked |
| Open-Meteo Historical Archive (`archive-api.open-meteo.com/v1/archive`) | None | Climate-normal estimate for trips beyond 16 days | No — mocked |
| Anthropic Messages API (`api.anthropic.com`) | `ANTHROPIC_API_KEY` (runtime env var, not present in build container) | Optional trip-briefing prose | No — mocked |

## Data Structure

SQLite database at `output/tripkit.db` (created on first run), two tables:

```sql
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    destination_query TEXT NOT NULL,       -- what the user typed
    resolved_name TEXT NOT NULL,           -- geocoded display name
    country TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    start_date TEXT NOT NULL,              -- ISO 8601 date
    end_date TEXT NOT NULL,
    activity_tags TEXT NOT NULL,           -- comma-separated, from fixed vocabulary
    created_at TEXT NOT NULL
);

CREATE TABLE weather_snapshots (
    trip_id INTEGER NOT NULL,
    mode TEXT NOT NULL,                    -- 'forecast' | 'climate_normal'
    fetched_at TEXT NOT NULL,
    daily_json TEXT NOT NULL,              -- list of {date, temp_max, temp_min, precip_mm, wind_max_kmh, weathercode}
    FOREIGN KEY (trip_id) REFERENCES trips(id)
);
```

Packing lists and AI briefings are derived on demand from a trip + its latest weather snapshot (not stored separately) — they're pure functions of stored data plus the deterministic rule engine, so there's nothing to keep in sync.

## Folder Structure

```
builds/2026-07-26-tripkit-trip-prep-planner/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── main.py            # CLI entry point (argparse subcommands)
│   ├── geocoding.py        # Open-Meteo geocoding client
│   ├── weather.py          # forecast/archive clients + 16-day routing + climate-normal averaging
│   ├── packing.py          # deterministic packing rule engine
│   ├── briefing.py         # AI (Claude Haiku) + deterministic-template briefing
│   ├── storage.py          # SQLite schema + CRUD
│   └── dashboard.py        # self-contained HTML dashboard generator
├── tests/
│   ├── test_geocoding.py
│   ├── test_weather.py
│   ├── test_packing.py
│   ├── test_briefing.py
│   ├── test_storage.py
│   ├── test_dashboard.py
│   └── test_cli.py
└── output/                 # generated at runtime: tripkit.db, dashboard.html (gitignored contents, folder kept via .gitkeep)
```

## Testing Strategy

Every test uses `unittest.mock` to stub `urllib.request.urlopen` (or the module-level HTTP helper) — no test makes a real network call, per CLAUDE.md's hard requirement. Minimum 15 tests, covering:

1. Geocoding: successful parse of a well-formed result → lat/lon/country/display name
2. Geocoding: no-match response raises a clear, catchable error
3. Weather: trip starting in 5 days routes to forecast mode
4. Weather: trip starting in 40 days routes to climate-normal mode
5. Weather: boundary case — trip starting exactly 16 days out routes to forecast mode (inclusive)
6. Weather: climate-normal averaging correctly averages multiple years' data for the same calendar date and skips a year if that year's fetch fails (partial-data resilience)
7. Packing: cold + wet + boating produces the expected gear categories (rain gear, life-jacket reminder, layered clothing)
8. Packing: hot + dry + golf produces sun protection and golf-specific items, omits cold-weather items
9. Packing: high wind flag adds a windbreaker/secure-loose-items note
10. Packing: destination country != Canada adds a passport/ID reminder to Documents & Admin; same-country trip does not
11. Packing: clothing quantities scale with trip duration but are capped at a sane maximum
12. Briefing: with a mocked successful Anthropic response, returns the AI text
13. Briefing: with no `ANTHROPIC_API_KEY` set, returns the deterministic template (no network call attempted)
14. Briefing: with an API-key set but a mocked network failure, falls back to the deterministic template without raising
15. Storage: adding a trip and reading it back round-trips all fields correctly
16. Storage: deleting a trip removes it and its weather snapshot
17. Storage: listing returns trips sorted by start date ascending
18. Dashboard: generated HTML escapes a trip name containing `<script>` — verifies no unescaped injection into the output (`html.escape` applied)
19. Dashboard: generated HTML contains one card per trip and the correct forecast/climate-normal badge text
20. CLI: `add` with `end_date` before `start_date` exits non-zero with a clear error instead of proceeding

Run with: `python -m pytest tests/ -v` from the build folder.

## Success Criteria

1. `tripkit add` resolves a destination via (mocked-in-tests / real-at-runtime) geocoding, correctly classifies the trip into forecast or climate-normal mode based on the 16-day boundary, and persists it — verified by tests 3–6, 15
2. The packing rule engine produces materially different, activity- and weather-appropriate lists for at least 3 distinct activity/weather combinations (not the same generic list every time) — verified by tests 7–11
3. `tripkit dashboard` produces a single self-contained HTML file that opens directly (`file://`) with no external file dependencies besides the pinned Chart.js CDN, renders every trip, and safely escapes user-entered trip names — verified by tests 18–19 and a manual open
4. The AI briefing path and its deterministic fallback both produce non-empty, trip-specific prose, and the fallback path never attempts a network call when no API key is present — verified by tests 12–14
5. All 20 tests pass with zero failures

## Idea Brief Traceability

Not applicable — this build came from fresh idea generation (Step 2d), not a lottery draw with a linked Idea Brief.
