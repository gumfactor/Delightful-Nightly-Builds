# Build Log — Earshot

> **Date:** 2026-08-14
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:52 UTC] Session Start

- Step 0: checked `builds/` for an interrupted prior session. Most recent dated folder is `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — done, nothing to resume. All later builds (2026-06-19 through 2026-08-13) live on open PR branches, not in this branch's local `builds/` folder, which is expected — this repo's own history (see Pipeline Pulse, 2026-07-09) shows most nightly builds sit unmerged for weeks.
- Read PROFILE.md, CLAUDE.md, STANDARDS.md.
- Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-l6k9tn`, PR #70, 2026-08-13 Macro Kitchen) before reading — the local `main`-based copy on this branch was missing backlog rows #13–#27 and index rows through 2026-08-13.
- Day of year (UTC 2026-08-14) = 226. `category_index = (226 - 1) % 9 = 0` → **Category A — Dashboard / Visualizer**. Consistent with the observed 9-day rotation (2026-08-13 was I, the category immediately before A).
- Read `builds/ideas.md`. Category A pending rows: #3 (Lab Research Project Tracker, rating 4, user note says "No need — already use Teamwork.com"), #5 (GitHub Repository Health Scorecard, unrated), #6 (Open-Meteo Activity Planner, unrated).
- Corrected #5 before running the lottery: its description is a verbatim duplicate of the already-built 2026-06-21 GitHub Repository Health Scorecard. This was actually flagged once before (2026-07-27, SiliconWatch's WhyThis.md) when it was drawn and overridden, but the correction to `builds/ideas.md` was never made — fixed tonight, marked `skipped`.
- Lottery pool after correction: #3 (rating 4) and #6 (blank → 5 tickets). R = count with a numeric rating = 1. `lottery_chance = min(75, 25 + 1*2) = 27%`.
- Rolled a random integer 1–100 via Python's OS-seeded `random.randint`: **84**. 84 > 27 → miss → fresh idea generation (Step 2d).
- Scanned the last 10 builds for topic saturation: investing/finance appeared twice (Portfolio Lab 2026-08-09, Quarter Call 2026-08-11) — not yet "more than twice," but a third in a row was avoided per the diversity check. GitHub-API dashboards have appeared repeatedly across Category A's own history (2026-06-21, 2026-06-30) and elsewhere (Landing Pattern 2026-08-03) — avoided a third GitHub dashboard.
- Generated 3 fresh Category A candidates (full reasoning in `WhyThis.md`); selected **Earshot**, an ambient sound-level exposure dashboard for PROFILE.md's named **Kwyeter** project (environmental noise awareness / accessibility for tinnitus and sensory sensitivity), which had zero prior builds anywhere in the catalog despite being one of five explicitly named active projects. Appended the two non-winning ideas to `builds/ideas.md` as #26 and #27 (per instructions, the winning idea itself is not added to the backlog).
- Build folder created: `builds/2026-08-14-earshot/`

### [09:05 UTC] PRD Written

- Goal: a browser dashboard that measures real ambient sound level from the device microphone in real time, classifies it against WHO/NIOSH exposure guidance, logs venue-tagged sessions locally, and tracks a running daily noise-exposure dose.
- Scope: live meter (real getUserMedia + Web Audio, not mocked/simulated data), one-time calibration against a known reference, session logging with venue tags, a history dashboard with per-session summary and trend chart, an OSHA/NIOSH-style exposure-dose calculator, and an optional direct-browser Claude Haiku plain-English exposure briefing (aggregate stats only, session-only key, unconditional deterministic fallback).
- Notable constraint: the build container has no microphone hardware and no display server. Chromium's fake-device flags (`--use-fake-device-for-media-stream --use-fake-ui-for-media-stream`) provide a synthetic audio track so the full capture pipeline can be exercised live in headless Playwright without any mocked application code — the app itself never knows it isn't talking to a real microphone. All dB-domain math (RMS→dB conversion, A-weighting approximation, exposure dose integration) is implemented as pure, dependency-free functions and unit-tested directly, independent of the audio pipeline.

### [09:20 UTC] Build Phase — Core Math

- Wrote `src/audio-math.js`: RMS-from-samples, RMS→dB(FS) conversion with a user-settable calibration offset, a simplified A-weighting attenuation curve (single-pole approximation over 6 octave bands, not a full IEC 61672 filter — documented as an approximation in Manual.md's Known Limitations), NIOSH/OSHA-style noise zone classification, and time-weighted exposure-dose accumulation using the standard 3 dB exchange-rate formula.
- Wrote `src/storage.js`: localStorage-backed calibration setting and session log (CRUD), schema-versioned.
- Wrote `src/audio-engine.js`: thin wrapper around `getUserMedia` + `AnalyserNode`, sampling at a fixed interval and feeding `audio-math.js`'s pure functions. Exposes a small event-based interface so `app.js` and tests can both drive it without touching the DOM.
- Wrote `src/app.js` and `index.html`/`src/styles.css`: three-tab UI (Live Meter, History, Calibration), dark-mode dashboard, Canvas 2D rolling dB chart (no external chart library needed — a single scrolling line plot), colorblind-safe zone badges (color + text label + icon, never color alone), all session/venue text rendered via `textContent`/`createElement`, never `innerHTML`.
- Wrote `src/ai-briefing.js`: optional direct-browser Anthropic API call sending only the finished session's aggregate numbers (avg/peak/dose/venue label — never raw audio or waveform data), session-only key stored in a JS variable (never persisted), deterministic template fallback with zero network calls when no key is present.

### [10:05 UTC] Tests Written

- `tests/audio-math.spec.js` (28 tests, Playwright pure-function tests, no browser chrome needed): RMS/dB conversions, calibration offset arithmetic, A-weighting table interpolation/clamping/monotonicity, zone-classification boundaries (exact 50/70/85 dB edges), exposure-dose formula cross-checked against three independent hand-computed 3 dB-exchange-rate reference cases (8hr@85dB, 4hr@88dB, 16hr@82dB all correctly land at 100%), edge cases (silence, full-scale clipping, zero/negative duration).
- `tests/app.spec.js` (16 tests, Playwright, full UI + fake-device live capture launched via `--use-fake-device-for-media-stream --use-fake-ui-for-media-stream`): calibration flow, starting/stopping a live session against Chromium's synthetic audio device (confirms real numbers flow end-to-end through `getUserMedia` → `AnalyserNode` → `audio-math.js`, not fixtures), venue-tagged session save with validation, history table/search/sort/detail/delete, trend chart, localStorage persistence across reload, XSS-safety of a `</script><script>` + `<img onerror>` payload placed in venue and note fields, AI-briefing deterministic fallback with no key (asserted via `page.route` interception that zero requests reach `api.anthropic.com`), mocked-Anthropic-response briefing path, mic-permission-denied error state, narrow mobile viewport layout.

### [10:40 UTC] Tests Run

Tests: 44 passed, 0 failed (28 in `audio-math.spec.js`, 16 in `app.spec.js`).

### [10:42 UTC] Manual Visual QA

Ran a live headless-Chromium QA pass (same fake-device flags as the test suite) with `page.on('pageerror'/'console')` capture and screenshots across all three tabs, a saved-session flow, and a 375px mobile viewport: zero page errors, zero console errors. One real UX issue found and fixed: with Chromium's synthetic fake-audio-device signal (a mostly-silent stream with periodic tone bursts, quieter overall than a typical real microphone in an actual room), uncalibrated readings landed deep in negative dB territory (e.g. "-92.2 dB(A)") with no visual cue that this was expected pre-calibration behavior rather than a broken reading. Rather than fudging the honestly-computed number, added a "(uncalibrated)" suffix to the live reading display whenever `calibration.calibratedAt` is unset — matching the wording already used on the Calibration tab's raw-reading display — so an implausible-looking number reads as "expected, not yet calibrated" instead of "broken." Re-ran the full suite after the fix: still 44 passed, 0 failed.

### [10:45 UTC] Verify — Step 7

Checked all 5 PRD success criteria (see PRD.md) — all met. Ran the STANDARDS.md security checklist manually: no `.env`, no hardcoded credentials, no `eval()`/`exec()`, no `innerHTML` anywhere in `src/` (grepped, zero matches — all dynamic DOM content uses `textContent`/`createElement`, verified live with injection payloads in tests), no shell/`os.system`/`subprocess` calls at all (pure browser build), no path traversal (no filesystem access — everything is `localStorage`), nothing outside `builds/2026-08-14-earshot/`.

### [10:50 UTC] Docs

- `FutureFeatures.md`: 9 concrete suggestions (4 quick wins, 3 medium effort, 2 ambitious extensions).
- `Manual.md`: quick start, tab-by-tab usage guide, configuration, troubleshooting, known limitations (A-weighting approximation, manual per-device calibration, no cross-device sync, foreground-only monitoring, per-session-average dose model).

Build complete. Success criteria reviewed. All tests passing.
