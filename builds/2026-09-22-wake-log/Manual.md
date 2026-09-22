# Manual — Wake Log

> **Version:** 1.0 (built 2026-09-22)
> **Complexity:** Ambitious Project

---

## What This Is

Wake Log answers one real question — "is this a good day to take the boat out this week?" — using a live weather forecast and a real maritime wind-classification standard (the Beaufort scale), instead of a vague glance at a weather app. It scores every daylight window of the upcoming week for boating comfort, tells you the best one, and writes a short, factual log entry about it that gets saved into a permanent local journal you can browse later.

---

## Quick Start

1. `cd` into this folder.
2. `python3 main.py forecast --lat 44.55 --lon -78.15 --location-name "Stony Lake"` — see the upcoming week's scores (replace with your own cottage/marina coordinates).
3. `python3 main.py generate --location-name "Stony Lake" --lat 44.55 --lon -78.15` — save a log entry for the best upcoming window.
4. `python3 main.py render --lat 44.55 --lon -78.15 --location-name "Stony Lake"` — write `journal.html`, then open it in any browser.
5. Repeat `generate` after each outing (or each week) to build up a real journal over the season.

---

## How to Use It

### `forecast`

Fetches the live Open-Meteo forecast and prints every morning/afternoon/evening window for the next N days (default 7), with its Beaufort classification, comfort score (0–100), wind/gust/temp/precip/cloud numbers, and marks the single best window.

```
python3 main.py forecast --lat 44.55 --lon -78.15 --location-name "Stony Lake" --days 7
```

### `generate`

Picks the best upcoming window (or a specific `--date YYYY-MM-DD` / `--window morning|afternoon|evening`), writes a trip-log narrative for it, and saves it permanently to the local journal (`wake_log.db` by default).

```
python3 main.py generate --location-name "Stony Lake" --lat 44.55 --lon -78.15
python3 main.py generate --location-name "Stony Lake" --date 2026-09-27 --window afternoon
```

Add `--ai-polish` to have Claude Haiku restyle the entry into more vivid prose (requires `ANTHROPIC_API_KEY` to be set in your shell). Every real number in the entry — wind speed, gusts, temperature, rain risk — is verified present in the AI's output before it's used; if the key is missing, the call fails, or the AI drops a fact, the deterministic version is saved instead. You will never get a broken or fabricated entry.

### `list` / `show` / `search`

```
python3 main.py list --limit 20
python3 main.py show 3
python3 main.py search "gale"
```

### `render`

Writes a self-contained, dark-mode HTML journal (`journal.html` by default) showing the upcoming week's score chart and every saved entry, with a live text search box. Open it by double-clicking the file — no server needed.

```
python3 main.py render --lat 44.55 --lon -78.15 --location-name "Stony Lake" --output journal.html
```

Pass `--offline` to skip the live forecast fetch and render just the saved journal (useful if you're not near the coordinates you'd normally check, or offline).

A pre-rendered example built from realistic synthetic data is included at `sample_output/journal.html` — open it directly to see what a populated journal looks like (this build container cannot reach the live Open-Meteo API to produce a real one).

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--lat` / `--lon` | Toronto (43.6532, -79.3832) | **Override with your own cottage/marina coordinates** — the default is a placeholder, not a real personal location |
| `--location-name` | "Toronto (default...)" | Human-readable label saved with every entry and shown in the journal |
| `--db` | `wake_log.db` (current directory) | Path to the local SQLite journal file |
| `--days` | 7 | Number of forecast days to score (1–10, an Open-Meteo limit) |
| `ANTHROPIC_API_KEY` (env var) | unset | Enables `--ai-polish`; the tool works fully without it |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: failed to reach Open-Meteo` | No internet access, or Open-Meteo is briefly down | Retry later; Open-Meteo requires no API key or account |
| `Error: no usable window found in the forecast` | Every window this week has zero daylight overlap or unscoreable data | Try a different `--date`/`--window`, or check back closer to the date |
| `generate --ai-polish` doesn't change the wording | `ANTHROPIC_API_KEY` isn't set, or the API call failed/dropped a fact | Set the environment variable; the deterministic entry is always a safe fallback, never a failure |
| Journal search finds nothing | Search matches narrative text and location name only (not date/score) | Try a weather-related word from the entry itself |

---

## Known Limitations

- No tide data — Open-Meteo doesn't provide it; a tide-aware build already exists for a different purpose (True Course, 2026-09-07).
- No marine hazard data (buoy reports, water temperature) — a future version could add NOAA/Environment Canada buoy feeds.
- Single local SQLite file, single location's history used for novelty scoring at a time — multiple locations are all stored in the same file but only compete against their own history, by design.
- The narrative bank has 24 templates (3 per Beaufort/precipitation combination); after very heavy use for the same location, repeats become more likely as the novelty scorer runs out of clearly-more-novel options.
