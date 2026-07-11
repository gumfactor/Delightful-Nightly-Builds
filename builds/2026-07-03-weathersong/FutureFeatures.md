# Future Features — WeatherSong

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Export a journal entry as an audio recording** — Use `MediaRecorder` on the `AudioContext`'s destination stream (via a `MediaStreamAudioDestinationNode` tee) to capture 30–60 seconds of a loaded soundscape as a downloadable `.webm`/`.wav` file.
2. **Keyboard shortcuts** — Space to play/pause, arrow keys to cycle through preset cities, `J` to open the journal — small but meaningfully improves one-handed use while it's running in the background.
3. **"Surprise me" city button** — Randomly picks one of the five presets (or a small expanded list) instead of requiring a manual selection every time.

## Medium Effort (roughly one nightly build session)

4. **Multi-day comparison view** — A small chart (native SVG, no library needed) plotting temperature/wind/cloud across all saved journal entries over time, so patterns in "what different weeks sounded like" become visible.
5. **A second, distinct instrument voice** — Add a slower secondary drone an interval away (fifth or third based on humidity, if/when Open-Meteo's humidity field is added to the fetch), giving the harmony more depth without changing the core architecture.

## Ambitious Extensions (multi-session effort)

6. **Location auto-detect + hourly evolution mode** — Use the browser Geolocation API for the default city, and instead of a static snapshot, smoothly interpolate the soundscape across the next 24 hours of Open-Meteo's hourly forecast so the instrument tells the story of an entire day, not just the current moment.
7. **Shareable soundscape links** — Encode a journal entry's params into a URL query string so a specific day's soundscape can be sent to someone else and replayed without needing the original journal (no server required — this is pure encode/decode).

---

## Possible Integration Points

- **Run Planner** (2026-06-20) already scores Open-Meteo data for running/golf/boating comfort windows. WeatherSong's mapping engine could be reused there as an optional "hear this window" preview for a scored comfort slot, rather than only showing it as a number.
- No other catalog build touches audio synthesis or Canvas-based generative visuals, so WeatherSong's `audio.js`/`visual.js` engines are a reusable base for any future Category D (Creative/Generative) or Category G (Game/Puzzle) build that wants a native, dependency-free audio layer.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The demo-weather fallback dataset is a single fixed snapshot, not a rotating set | Bundle 3–4 demo snapshots (clear/rain/snow/thunder) and cycle through them so offline use still shows variety |
| Percussion scheduling uses `setTimeout`, which can drift slightly under heavy CPU load | Move to Web Audio's own lookahead-scheduler pattern (schedule the next N blips ahead of time using `AudioContext.currentTime` instead of wall-clock `setTimeout`) |
| No visual indicator of *which* city's data the canvas gradient currently reflects, if the user has stepped away and forgotten | Add a small persistent label overlay on the canvas itself, not just the text panel above it |
