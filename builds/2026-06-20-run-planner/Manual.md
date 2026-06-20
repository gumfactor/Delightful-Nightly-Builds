# Manual — Run Planner

## Overview

Run Planner is a Python CLI that logs running workouts and fetches real weather data to identify the best training windows in the next 7 days. All data is stored locally in `runs.json` in the build folder.

## Requirements

- Python 3.8+
- No external runtime dependencies (stdlib only)
- Internet access for weather commands (`plan`, `report` without `--no-weather`)

## Commands

### `log` — Record a run

```bash
python src/main.py log --date YYYY-MM-DD --distance KM --time MM:SS [--effort easy|moderate|hard] [--notes "text"]
```

**Examples:**
```bash
# Log a 10km easy run in 55 minutes
python src/main.py log --date 2026-06-20 --distance 10.0 --time 55:00 --effort easy

# Log a hard 8.5km workout in 50 minutes 30 seconds with notes
python src/main.py log --date 2026-06-20 --distance 8.5 --time 50:30 --effort hard --notes "tempo intervals, felt strong"

# Long run — use hh:mm:ss format
python src/main.py log --date 2026-06-21 --distance 21.1 --time 1:58:30 --effort moderate
```

**Fields:**
| Field | Format | Required | Notes |
|-------|--------|----------|-------|
| `--date` | YYYY-MM-DD | Yes | Date of the run |
| `--distance` | float (km) | Yes | e.g. 8.5, 21.1, 42.2 |
| `--time` | mm:ss or hh:mm:ss | Yes | e.g. 50:30 or 1:58:30 |
| `--effort` | easy / moderate / hard | No | Default: moderate |
| `--notes` | string | No | Optional free text |

---

### `week` — This week's summary

```bash
python src/main.py week
```

Prints total runs, total km, average pace, and current streak for the current ISO week.

---

### `streak` — Current streak

```bash
python src/main.py streak
```

Prints the number of consecutive days with at least one run (counting back from today or yesterday).

---

### `plan` — Best running windows

```bash
python src/main.py plan [--lat LATITUDE] [--lon LONGITUDE]
```

Fetches a 7-day hourly forecast from Open-Meteo and prints the top 5 daytime windows scored for running comfort. Scores are based on:

| Factor | Weight | Best | Worst |
|--------|--------|------|-------|
| Feels-like temperature | 45% | 5–20°C | <-10°C or >35°C |
| Precipitation probability | 30% | 0–10% | >80% |
| Wind speed | 25% | 0–10 km/h | >50 km/h |

**Labels:** Excellent (90+) / Good (75–89) / Fair (60–74) / Poor (<60)

**Default location:** Toronto (43.65°N, 79.38°W). Override with `--lat` and `--lon`.

```bash
# Custom location (e.g. Ottawa)
python src/main.py plan --lat 45.42 --lon -75.69
```

---

### `report` — HTML dashboard

```bash
python src/main.py report [--output FILE] [--lat LAT] [--lon LON] [--no-weather]
```

Generates a self-contained dark-mode HTML report with:
- Stats cards (this week's km, run count, avg pace, all-time km)
- Weekly mileage bar chart (last 12 weeks, Chart.js)
- Best running windows table (fetched from Open-Meteo)
- Recent runs table (last 30)

```bash
# Generate report with weather data
python src/main.py report --output ~/Desktop/run-report.html

# Generate report without network access
python src/main.py report --no-weather
```

Open the output HTML file in any browser — no server required.

---

## Data File

Runs are stored in `runs.json` in the build folder root. The file is created automatically on first use.

Structure:
```json
{
  "runs": [
    {
      "id": "2026-06-20-001",
      "date": "2026-06-20",
      "distance_km": 8.5,
      "duration_seconds": 3030,
      "effort": "moderate",
      "notes": "felt good",
      "pace": "5:56"
    }
  ]
}
```

You can edit this file directly if you need to correct a logged run.

---

## Running Tests

```bash
cd builds/2026-06-20-run-planner
python -m pytest tests/ -v
```

Expected output: 74 tests, all passing.

---

## Notes

- Weather commands (`plan`, `report`) require outbound HTTPS access to `api.open-meteo.com`. No API key is required.
- The `--no-weather` flag lets you generate a report offline.
- `runs.json` is not committed to git — it lives locally in the build folder.
