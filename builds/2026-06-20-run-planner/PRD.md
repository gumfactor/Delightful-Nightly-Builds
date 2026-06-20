# PRD — Run Planner

## Goal

A Python CLI + HTML dashboard that logs running workouts locally, fetches a real 7-day weather forecast for Toronto, and scores each upcoming hour for running comfort — so a distance runner can plan training windows intelligently rather than checking weather apps manually.

## User Story

As a distance runner who trains 4–6 days per week, I want to log my runs with distance, time, and effort, then see a clear picture of this week's mileage, my current streak, my recent pace trend, and the best upcoming windows to run — all from a single command — so I can make good training decisions without context-switching to multiple apps.

## Scope

### In
- `log` command: record a run with date, distance (km), duration (mm:ss or hh:mm:ss), effort (easy/moderate/hard), optional notes
- `week` command: print this week's run count, total km, and average pace
- `streak` command: print current consecutive-day streak
- `plan` command: fetch Open-Meteo 7-day hourly forecast for Toronto (default lat/lon configurable), score each daytime hour, print top 5 windows
- `report` command: generate self-contained HTML dashboard with weekly mileage bar chart (last 12 weeks), top 10 best windows table, recent runs table
- Runs stored in `runs.json` in the build folder root (plain JSON, human-readable, no external DB)
- Weather via Open-Meteo public API (no auth, no rate limit for personal use)
- Dark-mode HTML with Chart.js CDN, mobile-responsive

### Out
- Garmin/Strava API integration (requires OAuth credentials not in PROFILE.md)
- GPS route display or mapping
- Training plan generation / periodization advice
- Notification or scheduling system
- Multi-user support
- Any cloud sync or remote storage

## Tech Stack

- Python 3.8+ stdlib only at runtime (`json`, `urllib.request`, `argparse`, `pathlib`, `datetime`)
- No external runtime dependencies → `requirements.txt` is empty (signals stdlib intent)
- `pytest` for tests
- HTML report uses Chart.js 4.4.4 via CDN

## Data Structure

`runs.json` in build root:
```json
{
  "runs": [
    {
      "id": "2026-06-20-001",
      "date": "2026-06-20",
      "distance_km": 8.5,
      "duration_seconds": 3030,
      "effort": "easy | moderate | hard",
      "notes": "optional free text",
      "pace": "5:55"
    }
  ]
}
```

Open-Meteo response (hourly, Toronto timezone):
- `apparent_temperature` — feels-like °C
- `wind_speed_10m` — km/h
- `precipitation_probability` — 0–100%

## Folder Structure

```
builds/2026-06-20-run-planner/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── runs.json                  ← created on first log, gitignored in spirit
├── src/
│   ├── main.py               ← CLI entry point
│   ├── store.py              ← JSON persistence, parse_duration, format_pace
│   ├── analytics.py          ← weekly_summary, current_streak, mileage_by_week
│   ├── weather.py            ← Open-Meteo fetch, scoring functions
│   └── report.py             ← HTML report generator
└── tests/
    ├── test_store.py         ← 10 tests
    ├── test_analytics.py     ← 8 tests
    ├── test_weather.py       ← 12 tests
    └── test_report.py        ← 5 tests
```

## Testing Strategy

- Pure logic tested directly — no subprocess or file-system mocking for scoring and analytics
- `store.py` tests patch `store.RUNS_FILE` to a `tmp_path` fixture so tests never touch real data
- `weather.py` scoring functions are pure (no I/O) — tested without network calls
- `parse_forecast` tested with a hand-crafted dict matching the Open-Meteo schema
- HTML report tested with `render_html()` called directly; checks structure, escaping, and key content
- Minimum 35 tests across 4 test files

Run command: `python -m pytest tests/ -v`

## Success Criteria

1. `python src/main.py log --date 2026-06-20 --distance 8.5 --time 50:30` writes the run to `runs.json` and prints a confirmation with calculated pace
2. `python src/main.py plan` fetches a live Open-Meteo forecast and prints at least 5 scored windows with temperature, wind, rain %, and a readable label (Excellent / Good / Fair / Poor)
3. `python src/main.py report --no-weather` generates `report.html` with a valid Chart.js mileage chart, a recent runs table, and a correct weekly stats header — all tests pass
4. All 35+ pytest tests pass with zero failures
5. The HTML report is self-contained (opens in a browser without a server, works on mobile)
