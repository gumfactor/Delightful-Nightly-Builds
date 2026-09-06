# Manual — Almanac

> **Version:** 1.0 (built 2026-09-06)
> **Complexity:** Ambitious Project

---

## What This Is

Almanac is a browser tool that turns decades of real historical daily weather data for any location into an explorable climate picture. Instead of a 7-day forecast, it pulls Open-Meteo's free historical weather archive and computes real statistics: what a "normal" month actually looks like (percentile bands, not just an average), how often heat waves, cold snaps, heavy-rain days, and high-wind days actually happen, and — for running, golf, boating, or a custom activity — what fraction of days in a chosen season actually meet your comfort thresholds. It's the tool to open before deciding whether "July at the cottage" is really boating weather, or how heat-wave-prone your usual golf season has become.

---

## Quick Start

1. Open `index.html` in a browser (double-click it, or run any static server and open it there — no build step, no install).
2. Type a location name (e.g. "Toronto" or "Muskoka") and click **Search**. If there's one clear match it's selected automatically; if there are several (e.g. "Springfield"), pick the right one from the list.
3. Set a start year and end year, optionally narrow to a season (e.g. June–August), and pick an activity preset (Running, Golf, Boating, or Custom with your own thresholds).
4. Click **Fetch historical data**.
5. Explore the climatology chart, the year-by-year chart, the extreme-events list, and the sortable summary table. Export either the raw daily data or the year summary as CSV from the buttons at the bottom.

---

## How to Use It

### Location search

Search uses Open-Meteo's free Geocoding API — no API key needed. A single unambiguous match (e.g. "Toronto") selects itself; multiple matches (e.g. "Springfield", "Paris") show a picker. Your 5 most recent locations are remembered (in your browser's local storage only) for one-click reuse next time.

### Year range and season window

Start/end year controls the historical range fetched from Open-Meteo (available from roughly 1940 through yesterday, depending on the location). The season-start/season-end month controls then filter that fetched data client-side — so you can fetch once and flip between "all year" and "just summer" without a second network call. The season window wraps around the year boundary correctly (e.g. December→February for winter).

### Activity presets

| Preset | Comfortable temp range | Max wind | Max precipitation |
|--------|------------------------|----------|--------------------|
| Running | 0–22°C | 30 km/h | 2 mm |
| Golf | 12–28°C | 25 km/h | 1 mm |
| Boating | 15–32°C | 20 km/h | 1 mm |
| Custom | you set all four | you set | you set |

A day counts as "suitable" only if its max temp, min temp, wind, and precipitation all fall within the preset's bounds. Days with any missing data are excluded from the calculation entirely (never treated as automatically suitable or unsuitable).

### Charts and table

- **Monthly climatology chart**: for each month, shows the P10/P50/P90 band of daily high temperatures across every year you fetched — a real "normal range," not just a single average line.
- **Year-over-year chart**: pick a variable (avg high, avg low, total precipitation, or % suitable days) and compare it across every fetched year as a bar chart.
- **Extreme events panel**: lists every heat wave (3+ consecutive days ≥30°C), cold snap (2+ consecutive days ≤-10°C), and counts of heavy-rain days (≥25mm) and high-wind days (≥40km/h).
- **Year table**: click any column header to sort by it (click again to reverse).

### Exporting data

Two CSV buttons: one exports every raw daily row that was fetched (date, high, low, precipitation, wind), the other exports the computed year-by-year summary. Both are plain CSV you can open in Excel, Google Sheets, or pandas.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| Heat wave threshold | ≥30°C for ≥3 consecutive days | Fixed in this version — see FutureFeatures.md for making it user-configurable |
| Cold snap threshold | ≤-10°C for ≥2 consecutive days | Fixed in this version |
| Heavy rain threshold | ≥25mm/day | Fixed in this version |
| High wind threshold | ≥40km/h | Fixed in this version |
| Recent locations remembered | 5 | Stored in `localStorage`, most-recent-first |

No configuration file, no API key, no account required.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "No locations found" | Spelling, or a very small/ambiguous place name | Try a nearby larger city, or add a province/state/country |
| "Could not fetch historical data: …" | The year range is outside what Open-Meteo has for that location, or you're offline | The message is Open-Meteo's own error text — adjust the year range it names |
| Charts don't appear but the table and events do | The Chart.js CDN script didn't load (offline, or a restrictive network) | Everything except the two charts still works fully offline-of-CDN; reconnect to see charts |
| Recent locations don't persist | Some browsers restrict `localStorage` when a page is opened via `file://` with strict privacy settings | Run a local static server (e.g. `python3 -m http.server`) and open it via `http://localhost` instead |

---

## Known Limitations

- Daily resolution only — no hourly data, so a single very hot afternoon on an otherwise mild day won't register.
- Extreme-event thresholds (30°C heat wave, -10°C cold snap, etc.) are fixed, not yet user-editable — they're tuned for a temperate climate and may need adjustment for very different locations.
- No marine-specific variables (wave height, water temperature, tide) — "Boating" suitability is based on air temperature, wind, and rain only.
- Requires an internet connection at run time to reach Open-Meteo; there's no offline/cached mode.
