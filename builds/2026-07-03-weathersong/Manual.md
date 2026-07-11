# Manual — WeatherSong

> **Version:** 1.0 (built 2026-07-03)
> **Complexity:** Ambitious Project

---

## What This Is

WeatherSong turns live weather for a city into a continuously evolving ambient soundscape and generative visual — no external audio library, just the browser's native Web Audio and Canvas APIs driven by a deterministic mapping from weather data. Temperature sets the pitch and mode, wind sets the tempo and brightness, cloud cover sets the reverb, and precipitation chance adds scattered percussion. A local Weather Journal lets you save a day's soundscape and replay the exact same one later, even after the weather itself has changed.

---

## Quick Start

1. Open `index.html` directly in a modern browser (Chrome, Edge, Firefox, or Safari). No build step, no server required for normal use.
2. It loads Toronto's current weather automatically. Pick a different preset city from the dropdown, or choose "Custom coordinates…" and enter a latitude/longitude.
3. Click **Play** to start the audio and the generative visual together.
4. Adjust **Volume** with the slider.
5. Click **Save Today to Journal** to keep a permanent record of today's sound — it's stored in your browser's local storage, so it stays on this device.

---

## How to Use It

### Choosing a location

The city dropdown includes five preset Canadian cities (Toronto, Vancouver, Halifax, Calgary, Montreal). Selecting "Custom coordinates…" reveals latitude/longitude fields — enter a value between -90/90 (latitude) and -180/180 (longitude) and click "Use these coordinates."

### If the weather fetch fails

If your network can't reach `api.open-meteo.com` (offline, firewall, etc.), an error banner appears. Click **Use Demo Weather** to load a fixed sample weather snapshot so you can still try the instrument.

### The Weather Journal

Each saved entry stores the exact weather snapshot and derived sound parameters at the moment you clicked Save — not just the weather itself. Click any entry in the journal list to reload that exact soundscape (no new network request is made; it replays from what was stored). Click "Remove" on an entry to delete it. The journal keeps the most recent 60 entries.

### Reading the soundscape

The italic caption under the weather stats (e.g. "Warm daylight over Toronto, a light breeze under a steady rain — a major drone at 165 Hz.") is a deterministic, template-generated description of what you're about to hear — the same weather always produces the same caption and the same sound.

---

## Configuration

No configuration required — it works as soon as you open `index.html`. If you want to run the automated test suite instead of just using the app:

```
npm install
npx playwright test
```

| Setting | Default | Description |
|---------|---------|--------------|
| Default city | Toronto | Loaded automatically on page open |
| Journal capacity | 60 entries | Oldest entries drop off once exceeded |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| No sound after clicking Play | Some browsers block audio until a real click/tap has occurred on the page | Click directly on the Play button (not just anywhere on the page) — this satisfies the browser's autoplay policy |
| Error banner on load | No network access to `api.open-meteo.com`, or the requested city is temporarily unreachable | Click "Use Demo Weather," or check your connection and reload |
| Journal is empty after reopening the page later | Browser was set to clear site data / private browsing mode | Journal data is stored in `localStorage`, which some browsers clear on exit in private/incognito mode — use a normal browsing window to keep entries |

---

## Known Limitations

- Weather updates only on page load or when you switch city/coordinates — it does not silently refresh in the background while left open.
- The demo weather fallback is a single fixed sample, not live or varied.
- Precipitation probability is read from Open-Meteo's hourly forecast (matched to the current hour), since it isn't part of the "current conditions" fields Open-Meteo exposes — this is a close approximation, not a live instantaneous reading.
