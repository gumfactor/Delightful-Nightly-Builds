# PRD — Wake Log

> **Build date:** 2026-09-22
> **Category:** D — Creative / Generative
> **Complexity:** Ambitious Project (every nightly build targets ambitious per CLAUDE.md's calibration note)
> **Day of week:** Tuesday

---

## Goal

A Python CLI that turns a live Open-Meteo forecast into a real boating/cottage-day recommendation (via a deterministic Beaufort-scale comfort-scoring engine) and a fact-grounded written trip-log entry for the best window, building a persistent, browsable personal boating journal over time.

## User Story

As a boating/cottage-owning user who wants a fast, trustworthy answer to "is this a good day to take the boat out," I want a tool that scores the upcoming week's weather windows using real maritime wind classification and generates a short log entry for the best one, so that I can plan outings with actual meteorological grounding instead of a vague forecast glance, and end up with a running log of outings over the season.

## Scope

### In Scope
- `openmeteo.py`: live Open-Meteo API client (hourly + daily forecast, wind speed in knots, no auth); aggregates into fixed clock windows (morning/afternoon/evening) while tracking each window's real daylight-hour overlap separately for scoring; typed error on failure/malformed response
- `scoring.py`: a real Beaufort wind-force classifier (0–12, knots-based, the actual maritime standard) and a documented, weighted boating-comfort score (0–100) per 3-hour-block window (morning/afternoon/evening) per day, factoring wind, gust factor, precipitation probability, temperature, cloud cover, and daylight overlap
- `narrative.py`: a deterministic mad-libs-style template bank (multiple phrasings per Beaufort/precipitation/temperature combination) that assembles a trip-log entry from the window's real computed facts, with novelty selection (Jaccard token-overlap scoring against the persisted local library) so repeated generations for similar conditions don't read identically
- `ai_polish.py`: optional Claude Haiku rewrite of the deterministic draft — every extracted numeric/factual string (wind speed, gust, temp, Beaufort number, precip probability) must still appear verbatim in the AI output or the deterministic draft is used instead; zero network calls when `ANTHROPIC_API_KEY` is unset
- `store.py`: local SQLite persistence of every generated log entry (append-only, never overwritten) plus the novelty-scoring corpus
- `render.py`: a self-contained dark-mode HTML journal (Chart.js 4.4.4 comfort-score chart with a DOM-table fallback if the CDN is blocked) — browsable, searchable list of past entries plus the upcoming week's score table
- `cli.py`: `forecast`, `generate`, `list`, `show`, `search`, `render` subcommands
- Location is a CLI argument (`--lat`/`--lon`/`--location-name`), defaulting to a placeholder public location (Toronto) the user is expected to override with their own cottage/marina coordinates — never a hardcoded real personal address
- `sample_output/`: a rendered example HTML journal built from a realistic synthetic forecast, since this build container's egress proxy blocks live Open-Meteo access (confirmed this session — a direct `curl` to `api.open-meteo.com` was denied by the sandbox permission layer before even reaching the network policy)

### Out of Scope
- Tide data (Open-Meteo has none; a real tide-aware build already exists for a different mechanic — True Course, 2026-09-07)
- Audio/visual synthesis of any kind (WeatherSong's territory, 2026-07-03)
- Multi-user or cloud sync — single local SQLite file, exactly like every other nightly build's persistence model
- Marine-specific hazard data (buoy reports, water temperature) — Open-Meteo doesn't expose these; a future build could add NOAA/ECCC buoy data as a richer signal (see FutureFeatures.md)

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`urllib.request` for both Open-Meteo and the optional Anthropic call, `sqlite3`, `argparse`, `json`, `datetime`, `html`). No `requirements.txt` entries needed — left present but empty per STANDARDS.md.
- **Runtime requirement:** `python3 main.py <command> ...` — no install step

## Data Structure

**Open-Meteo request** (per generation): hourly `temperature_2m`, `precipitation_probability`, `windspeed_10m`, `windgusts_10m`, `cloudcover`, `weathercode`; daily `sunrise`, `sunset`; `windspeed_unit=kn`; `forecast_days` up to 10.

**Window aggregate** (computed, not persisted independently):
```python
{
  "date": "2026-09-27",
  "window": "afternoon",       # morning | afternoon | evening
  "hours": [12, 13, ..., 17],  # clipped to daylight
  "wind_knots": 9.4,           # mean
  "gust_knots": 14.1,          # max
  "beaufort": 3,                # int 0-12
  "beaufort_name": "Gentle Breeze",
  "temp_c": 21.3,               # mean
  "precip_probability": 10,     # max, percent
  "cloud_cover": 35,             # mean, percent
  "daylight_hours": 6,
  "score": 78.4,                 # 0-100
}
```

**SQLite schema** (`wake_log.db`):
```sql
CREATE TABLE entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,       -- ISO 8601 UTC, when the entry was generated
  location_name TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  target_date TEXT NOT NULL,      -- YYYY-MM-DD, the forecasted day
  window_label TEXT NOT NULL,     -- morning | afternoon | evening
  score REAL NOT NULL,
  beaufort INTEGER NOT NULL,
  beaufort_name TEXT NOT NULL,
  wind_knots REAL NOT NULL,
  gust_knots REAL NOT NULL,
  temp_c REAL NOT NULL,
  precip_probability REAL NOT NULL,
  cloud_cover REAL NOT NULL,
  narrative TEXT NOT NULL,
  ai_polished INTEGER NOT NULL DEFAULT 0   -- 0/1
);
```
Every row is a permanent, append-only log entry — no updates, no deletes exposed via the CLI. Novelty scoring reads every prior `narrative` for the same `location_name` as its comparison corpus.

## Folder Structure

```
builds/2026-09-22-wake-log/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── openmeteo.py
│   ├── scoring.py
│   ├── narrative.py
│   ├── ai_polish.py
│   ├── store.py
│   ├── render.py
│   └── cli.py
├── sample_output/
│   └── journal.html
└── tests/
    ├── conftest.py
    ├── test_scoring.py
    ├── test_openmeteo.py
    ├── test_narrative.py
    ├── test_ai_polish.py
    ├── test_store.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Beaufort classification at every documented knot-speed boundary (0, 1, 4, 7, 11, 17, 22, 28, 34, 41, 48, 56, 64 kn)
  - Comfort score: monotonic response to wind/precip/temp changes (e.g., raising precip probability never increases the score); windows entirely outside daylight are excluded/scored 0
  - `openmeteo.py`: successful parse of a realistic mocked API response into window aggregates; malformed/missing-field response raises a typed error; the module never makes a live network call inside a test (verified via mocked `urlopen`)
  - Narrative assembly: every generated draft contains every extracted fact string verbatim; novelty scoring picks a different template than one already in a mocked history when alternatives exist; a script-injection payload in `location_name` never appears unescaped in generated narrative meant for HTML rendering
  - AI polish: a mocked Anthropic response missing a required numeric fact is rejected and falls back to the deterministic draft; a valid mocked response is accepted; zero network calls attempted with no `ANTHROPIC_API_KEY` set
  - SQLite store: `save` persists and `list`/`search`/`get` retrieve correctly; entries are append-only (no update/delete method exists); search matches on narrative text and location name
  - `render.py`: output HTML never contains an unescaped `<script>` from a hostile stored narrative or location name (verified by asserting the malicious substring appears only inside the escaped JSON payload, never as a live tag); renders correctly with zero saved entries (empty state)
  - CLI: `forecast`, `generate`, `list`, `show`, `search`, `render` each exercised end-to-end against a mocked Open-Meteo/Anthropic layer and a temp SQLite file; invalid arguments (bad date format, unknown window) produce a clean error, not a traceback

## Success Criteria

1. All tests pass (zero failures)
2. `forecast` correctly classifies a full range of realistic mocked wind speeds into the right Beaufort category and produces a sane 0–100 score for at least 3 distinct condition profiles (calm/sunny, windy/showery, dangerous-gust)
3. `generate` produces a narrative in which every real computed fact (wind speed, Beaufort name, temperature, precipitation probability) appears verbatim in the final text, whether deterministic or AI-polished
4. Two consecutive `generate` runs against near-identical mocked conditions produce measurably different narrative text (novelty scoring is actually doing something, not a no-op)
5. `render` produces a self-contained HTML file that opens directly (`file://`) and safely displays a stored entry containing a `<script>`-injection attempt in its location name with zero executed script (verified live in headless Chromium)

---

## Scope Changes

None — full scope as planned was completed in-session. The only adjustment from the original idea-backlog description is documented above under "Out of Scope" (no audio/visual output, no tide data) to keep the mechanism cleanly distinct from WeatherSong and True Course, per the idea's own backlog note.
