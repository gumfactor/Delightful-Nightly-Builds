# Build Log — WeatherSong

> **Date:** 2026-07-03
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:10 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md, and the most current `builds/index.md` (synced from origin's most recently opened PR branch, `claude/cool-sagan-mx0xwx`, PR #27, since main's copy was behind).
- Step 0: checked the most recent dated build folder (`2026-06-18-regex-dojo`) locally, and confirmed via each subsequent open PR's body that every build through 2026-07-02 (PubMed Research Radar, PR #27) ended with the required "Build complete. Success criteria reviewed. All tests passing." log line and passing tests. No interrupted build to resume.
- Day of year 184 → `(184-1) % 9 = 3` → category **D — Creative/Generative**.
- `builds/ideas.md` has no `pending` rows with `Category = D` → lottery skipped, fresh generation path.
- Ran a quick network probe (`curl` to `api.open-meteo.com`) — the Bash tool denied it outright, confirming this session has no outbound network access, matching the note left in PR #27's body about the prior session's sandboxed network policy. This shaped the design: no CDN-hosted JS libraries (would fail to load during Playwright test runs), native Web Audio/Canvas APIs only, and the one live-data call (Open-Meteo) is mocked in tests via `page.route`.
- Decided to build: **WeatherSong** — a live-weather-driven generative ambient audio/visual instrument with a local Weather Journal.
- Build folder created: `builds/2026-07-03-weathersong/`

### [08:15 UTC] PRD Written

- Goal: turn live weather into a continuously evolving Web Audio soundscape + Canvas visual, with deterministic mapping and a localStorage journal to replay past days.
- Scope: Open-Meteo fetch (5 preset cities + custom lat/long), pure mapping module, native audio engine (oscillators, filter, procedural convolution reverb, scheduled percussion), Canvas visual, play/pause + volume, demo-weather fallback on fetch failure, Weather Journal with deterministic template captions.
- Notable decision: dropped Anthropic API caption generation from scope (see PRD "Out of Scope") — a static client-side page has no safe way to call a keyed API without shipping the key to the browser. Replaced with a deterministic template caption generator instead.

### [09:05 UTC] Build Phase — Core modules

- Wrote `src/mapping.js` (pure functions, no DOM/Web Audio dependency, easiest to unit test directly).
- Wrote `src/weather.js` (Open-Meteo fetch + normalization + city presets + demo dataset fallback).
- Wrote `src/caption.js` (deterministic template captions from a weather snapshot + params).
- Wrote `src/journal.js` (localStorage-backed save/list/load/remove, capped at 60 entries).
- Wrote `src/audio.js` (Web Audio graph: drone oscillator + gain, biquad filter, procedurally generated impulse response for `ConvolverNode` reverb, scheduled percussive blip layer using `setTimeout`-driven lookahead scheduling).
- Wrote `src/visual.js` (Canvas 2D: gradient background, particle field, precipitation streaks, `requestAnimationFrame` loop).
- Wrote `src/main.js` (wires UI controls to the above, owns app state, handles fetch errors/demo fallback).
- Wrote `index.html` + `src/styles.css`.

### [09:40 UTC] Tests Written

- `tests/mapping.spec.js`, `tests/weather.spec.js`, `tests/journal.spec.js`, `tests/caption.spec.js` import the ES modules directly in the Playwright Node process — no browser needed for these, fast and deterministic.
- `tests/ui.spec.js` drives a real headless Chromium page, intercepting `**/api.open-meteo.com/**` with `page.route` so no real network call is made.

### [08:15 UTC] Obstacle — ESM in a plain HTML/JS build

`src/*.js` files use `export`/`import` (ES modules) so `<script type="module">` in `index.html` works, but Node's default CommonJS interpretation of `.js` files would throw a `SyntaxError` on `export` when Playwright test files `import` them directly for unit testing. Fixed by adding `"type": "module"` to `package.json` (so Node treats all `.js` here as ESM) and renaming `playwright.config.js` → `playwright.config.cjs` (keeps the CommonJS `require`/`module.exports` pattern for the one file that needs it).

### [08:16 UTC] Obstacle — CDN libraries would break sandboxed tests

Confirmed via a denied `curl` call that this build session has no outbound network access (same constraint noted in PR #27's body for the prior session). A CDN-hosted synthesis library (e.g. Tone.js) would fail to load during any Playwright test run here. Resolved by using only native Web Audio API (`AudioContext`, oscillators, `BiquadFilterNode`, a procedurally generated `ConvolverNode` impulse response — no external audio file) and native Canvas 2D — zero runtime dependencies, zero CDN calls. This also means the tool works completely offline for the end user except for the one live weather fetch.

### [08:18 UTC] Obstacle — `<script type="module">` fails to load over `file://`

Chromium blocks cross-origin module script loads from `file://` URLs. Serving `index.html` over a local static server sidesteps this. Added a Playwright `webServer` config entry that launches the globally installed `http-server` on `127.0.0.1:4173` before the test run and uses it as `baseURL`.

### [08:22 UTC] Manual smoke test

Ran the app for real: started a local `http-server`, launched headless Chromium via a throwaway Node script (mocking the Open-Meteo route the same way the automated tests do), loaded the page, clicked Play, waited ~800ms, and took a screenshot. Confirmed: the weather panel renders live values and a generated caption ("Warm daylight over Toronto, a light breeze under a steady rain — a major drone at 165 Hz."), the Canvas visual renders a gradient + particle field, and the Play button correctly flips to "Pause" with the underlying `AudioContext` actually running (verified via the `window.__weatherSongEngine.isRunning()` test hook).

### [08:23 UTC] Tests Run

Tests: 50 passed, 0 failed.

### [08:30 UTC] Verify — Step 7 — Success criteria check

1. ✓ All tests pass — 50 passed, 0 failed
2. ✓ Live weather for any preset city or custom coordinates is fetched and normalized correctly — `weather.spec.js` covers parsing/edge cases; `ui.spec.js` covers the full city-switch and custom-coordinate flows against a mocked route
3. ✓ Mapping is deterministic and covers the full documented range without runtime errors, including out-of-range inputs — `mapping.spec.js` exercises clamping and boundary values for every mapped parameter
4. ✓ Play/Pause reliably starts and stops audio + visual together — verified by an automated test asserting real `AudioContext` state via a test-only hook, and by a manual smoke test with a screenshot
5. ✓ A saved journal entry reproduces its exact stored parameters on reload rather than issuing a fresh fetch — verified by an automated test asserting the network request count does not increase when a journal entry is loaded

Security checklist:
- No `.env` files, no hardcoded credentials/API keys (the Anthropic API was deliberately excluded from this build — see PRD "Out of Scope" — so there is no key-exposure risk in this client-side-only app)
- No `eval()`/`exec()` on user input
- The only `innerHTML` write clears a list (`list.innerHTML = ''`); all dynamic content (journal captions, city names) is set via `textContent`/`createElement`, not string-interpolated HTML — no XSS vector
- No `os.system`/`subprocess` calls (browser JS only)
- No file path handling with user input
- All files self-contained under this build's folder

### [08:32 UTC] Docs — Step 8

- `FutureFeatures.md`: 7 concrete suggestions across quick wins, medium effort, and ambitious extensions
- `Manual.md`: quick start, feature walkthrough, configuration, troubleshooting, known limitations

Build complete. Success criteria reviewed. All tests passing.
