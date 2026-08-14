# PRD — Earshot

> **Build date:** 2026-08-14
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious Project
> **Day of week:** Friday

---

## Goal

A browser dashboard that measures real ambient sound level from the device microphone in real time, classifies exposure against WHO/NIOSH noise-safety guidance, and tracks venue-tagged noise sessions and daily exposure dose over time.

## User Story

As a founder building Kwyeter (an environmental noise-awareness and accessibility platform for people with sensory sensitivities, tinnitus, or hearing-related concerns), I want a working tool that measures and classifies real ambient noise from my own microphone, so that I can experience the core loop Kwyeter is meant to deliver — "how loud is this place, and is it safe to be here" — before building it as a product.

## Scope

### In Scope
- **Live Meter tab**: real-time sound level from the device microphone via `getUserMedia` + Web Audio `AnalyserNode`, sampled on a fixed interval, converted to an approximate dB(A) reading via a calibration offset and a simplified A-weighting curve.
- **Calibration**: a one-time (re-runnable) step where the user matches the live reading against a known reference value (their phone's sound-meter app, or a documented rule-of-thumb reference level) to set a per-device offset. Uncalibrated by default, and clearly labeled "uncalibrated / relative" until the user calibrates — never presents an unverified number as an authoritative SPL reading.
- **Noise zone classification**: Quiet / Moderate / Loud / Hazardous bands mapped to published NIOSH/OSHA/WHO reference points, shown as a color + text + icon badge (never color alone).
- **Live rolling chart**: Canvas 2D scrolling line plot of the last 60 seconds of dB readings, hand-drawn, no external charting library.
- **Session logging**: start/stop a timed session, tag it with a venue/location name and optional note, and save average dB, peak dB, duration, and computed noise-exposure dose to local storage.
- **Exposure dose**: a NIOSH-style time-weighted noise dose using the standard 3 dB exchange rate against an 85 dB / 8-hour reference, accumulated across a rolling 24-hour window from saved sessions, shown as a percentage of the daily recommended limit with a plain-language safety message.
- **History dashboard**: a searchable/sortable table of past sessions plus a trend chart of average dB per session over time; click a session to see its detail (venue, notes, avg/peak/dose, mini chart of its own dB-over-time series, which is stored downsampled — never raw audio).
- **Optional AI briefing**: a direct-browser call to the Anthropic API (session-only key entered in the UI, never persisted) that turns a completed session's aggregate numbers into a plain-English exposure/comfort briefing. Sends only avg dB, peak dB, duration, dose %, and venue label — never raw audio or waveform data. Unconditional deterministic-template fallback with zero network calls when no key is present.
- **Privacy**: raw audio is never recorded, stored, or transmitted anywhere — only derived numeric summaries (avg/peak/dose) ever leave the live-analysis loop, and those never leave the browser except in the optional AI-briefing call the user explicitly triggers.

### Out of Scope
- True IEC 61672-calibrated SPL measurement (would require a calibrated hardware reference and a full-order A-weighting filter bank — not achievable or honestly claimable from a laptop/phone microphone in one session). Documented explicitly as a limitation.
- Cross-device sync or a backend — this is a fully local, single-browser tool (matches Kwyeter's long-term vision but is a thin, complete vertical slice, not the full platform).
- Continuous background monitoring / notifications — the meter only runs while the tab is open and the user has started a session.
- Venue database / crowdsourced venue noise ratings (a real future direction for Kwyeter itself, noted in FutureFeatures.md, but out of scope for a one-session local tool with no server).

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic `<script>` tags — no build step, opens directly via `file://` or a local static server)
- **Framework:** None
- **Dependencies:** None (no CDN libraries — Web Audio API, Canvas 2D, and localStorage are all native browser APIs; Anthropic API called directly via `fetch` when the user supplies a key)
- **Runtime requirement:** Opens directly in a browser (`index.html`). Requires microphone permission for the Live Meter tab; History and Calibration tabs work with no permission needed.

## Data Structure

All data lives in `localStorage` under a single namespaced key, as JSON:

```json
{
  "schemaVersion": 1,
  "calibration": {
    "offsetDb": 0,
    "calibratedAt": null,
    "referenceLabel": null
  },
  "sessions": [
    {
      "id": "uuid-like string",
      "venue": "string, user-entered, escaped on render",
      "note": "string, optional, escaped on render",
      "startedAt": "ISO 8601 timestamp",
      "endedAt": "ISO 8601 timestamp",
      "durationSec": 42,
      "avgDb": 61.4,
      "peakDb": 78.2,
      "doseDeltaPct": 3.1,
      "series": [{"t": 0, "db": 55.1}, {"t": 1, "db": 57.9}]
    }
  ]
}
```

`series` is downsampled to roughly one point per second regardless of the underlying sampling interval, so a long session never grows unbounded.

## Folder Structure

```
builds/2026-08-14-earshot/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── playwright.config.js
├── package.json
├── src/
│   ├── styles.css
│   ├── audio-math.js       ← pure dB/exposure math, no DOM/Web Audio dependency
│   ├── storage.js          ← localStorage read/write/schema
│   ├── audio-engine.js     ← getUserMedia + AnalyserNode wrapper, event-based
│   ├── ai-briefing.js      ← optional direct-browser Anthropic call + template fallback
│   └── app.js              ← UI wiring, tabs, chart rendering
└── tests/
    ├── audio-math.spec.js  ← pure-function unit tests
    └── app.spec.js         ← full UI + fake-device live-capture tests
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`), matching the repo's convention for vanilla HTML/JS builds.
- **Pure math tests** (`audio-math.spec.js`): run entirely in Node via Playwright's `test()` blocks calling into the loaded module — RMS→dB conversion at known reference points, calibration-offset arithmetic, A-weighting monotonicity across the band table, zone-classification boundary values (exactly at 50/70/85 dB), exposure-dose formula cross-checked against a hand-computed 3 dB-exchange-rate reference table, and edge cases (all-zero/silent buffer, clipped/full-scale buffer, zero-duration session).
- **Live-capture tests** (`app.spec.js`): launch Chromium with `--use-fake-device-for-media-stream --use-fake-ui-for-media-stream` so `getUserMedia` auto-grants and returns a real (synthetic) `MediaStream` — the app's own audio pipeline runs unmodified and untested code paths in `audio-engine.js` are genuinely exercised, not stubbed. Covers: calibration flow end-to-end, starting a live session and observing the dB reading and chart update from real (fake-device) audio, stopping and saving a session with a venue tag, history table/detail/trend-chart rendering, dose-percentage accumulation across two saved sessions, localStorage persistence across a page reload, an injected `<script>`/`<img onerror>` payload in a venue name and note verified to render as inert text (zero dialogs, zero page errors), the AI-briefing deterministic fallback verified to make zero network requests with no key present, the AI-briefing path verified against one mocked Anthropic `fetch` response, and a narrow mobile viewport layout check.
- **Run command:** `npx playwright test` (documented in Manual.md).
- **Minimum 15 tests, all passing before commit** — actual count and pass/fail logged in `BUILD_LOG.md`.

## Success Criteria

1. The Live Meter genuinely reads real audio data end-to-end through `getUserMedia` → `AnalyserNode` → the same `audio-math.js` functions used in unit tests — verified live under Chromium's fake-device flags, not simulated with fabricated numbers in the app code.
2. Calibration changes the displayed dB reading by exactly the entered offset, and the UI clearly marks the reading as uncalibrated until the user calibrates.
3. A completed session is saved with correct avg/peak/duration/dose values, persists across a page reload, and appears correctly in the History tab and trend chart.
4. The exposure-dose calculation matches a hand-computed NIOSH 3 dB-exchange-rate reference value within floating-point tolerance for at least 3 independent test cases.
5. All 15+ tests pass with zero failures, and a live script-injection payload in a venue name or note is confirmed to render as inert escaped text with zero dialogs and zero page errors.
