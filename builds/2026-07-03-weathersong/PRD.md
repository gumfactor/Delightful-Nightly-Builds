# PRD — WeatherSong

> **Build date:** 2026-07-03
> **Category:** D — Creative / Generative
> **Complexity:** Ambitious
> **Day of week:** Friday

---

## Goal

A browser instrument that turns a city's live weather into a continuously evolving ambient soundscape and generative visual, built entirely from native Web Audio/Canvas APIs with a local journal to replay past days.

## User Story

As a person who spends time on the water, on the road running, and thinking in systems, I want to hear and see today's weather rendered as an evolving piece of ambient music and generative art rather than a spreadsheet of numbers, so that I get something genuinely surprising and pleasant to have open in the background — and can look back at what a given day "sounded like."

## Scope

### In Scope
- Live weather fetch from Open-Meteo (current conditions + hourly cloud cover/precipitation probability/wind + daily sunrise/sunset) for a small preset list of Canadian cities (Toronto, Vancouver, Halifax, Calgary, Montreal) plus a custom latitude/longitude input
- A pure, deterministic mapping module (`src/mapping.js`) that converts weather parameters into synthesis + visual parameters: temperature → drone pitch (quantized to a pentatonic scale) and major/minor mode via day/night; wind speed → arpeggio tempo and filter cutoff; cloud cover → reverb wetness; precipitation probability → density of percussive "raindrop" blips; WMO weather code → an optional distinct texture layer (e.g. thunder rumble)
- A native Web Audio synthesis engine (`src/audio.js`) with no external audio library — oscillators, a biquad filter, a gain-based drone, a procedurally generated convolution reverb impulse, and a scheduled percussive layer — all driven by the mapping output and updatable live
- A native Canvas 2D generative visual (`src/visual.js`) synchronized to the same parameters — gradient background from temperature, particle field density/speed from wind, particle blur/opacity from cloud cover, falling streaks from precipitation probability
- Play/Pause control, master volume control, city selector
- Graceful degradation: if the live fetch fails (network error, bad response), show an inline error and offer a "Use Demo Weather" fallback dataset so the tool stays usable and testable offline
- A local Weather Journal (localStorage) — "Save Today" stores the date, city, raw weather snapshot, derived params, and a deterministically generated one-line caption; a Journal panel lists saved days and can reload any entry's exact stored parameters (no new fetch) to replay it
- A template-based caption generator (`src/caption.js`) that produces a short descriptive line from the weather snapshot (e.g. "Overcast and brisk over Halifax — a hushed grey drone with rain caught in the wind.") — deterministic, no external API call

### Out of Scope
- Anthropic API–generated captions — a static HTML/JS page has no backend, so calling the Anthropic API from client-side code would require shipping the API key to the browser (visible in devtools/network tab), which is a real credential-exposure risk. STANDARDS.md forbids hardcoded credentials and this environment has no server component to proxy the call safely. The deterministic template caption generator substitutes for this.
- Recording/exporting audio to a file
- User accounts, sharing, or any multi-user features
- Weather for non-Canadian cities beyond the custom lat/long override
- Mobile touch-specific gesture controls beyond standard tap/click (still responsive/usable on a phone browser)

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, ES modules)
- **Framework:** None — native Web Audio API and Canvas 2D API only, zero runtime JS dependencies
- **Dependencies (dev/test only):** `@playwright/test`
- **Runtime requirement:** Open `index.html` directly in any modern browser (Chrome/Edge/Firefox/Safari); requires internet access at runtime to reach `api.open-meteo.com` (falls back to bundled demo data if unreachable)

## Data Structure

**Weather snapshot** (normalized from the Open-Meteo response, shape used throughout the app):
```js
{
  city: "Toronto",
  latitude: 43.65, longitude: -79.38,
  temperatureC: 21.4,
  windSpeedKmh: 14.2,
  cloudCoverPct: 62,
  precipProbabilityPct: 30,
  weatherCode: 61,          // WMO code
  isDay: true,
  fetchedAt: "2026-07-03T14:00:00Z"
}
```

**Derived params** (output of `mapping.js`, consumed by `audio.js` and `visual.js`):
```js
{
  scaleDegree: 3, mode: "major",      // drone pitch selection
  droneFreqHz: 220.5,
  tempoHz: 1.8,                       // arpeggio/LFO rate
  filterCutoffHz: 1200,
  reverbWetness: 0.62,                // 0–1
  percussionDensity: 0.3,             // 0–1, blips per second scaled
  textureLayer: "rain" | "thunder" | "clear" | null
}
```

**Journal entry** (localStorage key `weathersong.journal`, array of):
```js
{ id, savedAt, city, weatherSnapshot, params, caption }
```

## Folder Structure

```
builds/2026-07-03-weathersong/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── package-lock.json
├── playwright.config.js
├── index.html
├── src/
│   ├── main.js
│   ├── weather.js
│   ├── mapping.js
│   ├── audio.js
│   ├── visual.js
│   ├── journal.js
│   ├── caption.js
│   └── styles.css
└── tests/
    ├── mapping.spec.js
    ├── weather.spec.js
    ├── journal.spec.js
    ├── caption.spec.js
    └── ui.spec.js
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - `mapping.js`: pure-function unit tests run directly in the Playwright Node process (no browser needed) — temperature/wind/cloud/precip boundary and midpoint values, day vs. night mode selection, weather-code texture layer selection, clamping of out-of-range inputs, monotonicity of tempo vs. wind speed
  - `weather.js`: parsing a valid mocked Open-Meteo JSON response into a normalized snapshot, handling a response missing optional fields, city-preset lookup, custom lat/long validation, demo-fallback dataset shape
  - `journal.js`: saving an entry, listing entries newest-first, loading a specific entry by id, removing an entry, capping storage at a maximum entry count
  - `caption.js`: deterministic caption text for a range of weather snapshots (hot/cold, windy/calm, clear/rainy/thunder, day/night) — same input always produces the same caption
  - `ui.spec.js` (real browser via Playwright): page loads and shows a title, weather panel populates from a mocked `page.route` response, Play button starts and Pause stops (AudioContext state), city selector triggers a re-fetch, a failed fetch shows the error banner and demo-fallback button works, Save-to-Journal adds a visible entry, clicking a journal entry loads its stored snapshot without issuing a new network request
  - Edge/error cases: unreachable network, malformed API response, empty journal state, empty custom-coordinate input

## Success Criteria

1. All tests pass (zero failures)
2. Live weather for any of the 5 preset cities (or custom coordinates) is fetched and normalized correctly, verified by mocked-route tests
3. The mapping from weather → audio/visual parameters is deterministic and covers the full documented range (temperature, wind, cloud, precipitation, day/night, weather code) without runtime errors, including out-of-range inputs
4. Play/Pause reliably starts and stops audio playback and the visual animation loop together
5. A saved journal entry can be reloaded later and reproduces the exact same parameters (not a fresh, possibly different, live fetch)

---

## Scope Changes

Dropped: Anthropic API–powered caption generation (see "Out of Scope" — client-side-only architecture makes this unsafe without a backend to hold the API key). Replaced with a deterministic template generator, which still delivers the "generative text" touch without the security risk.
