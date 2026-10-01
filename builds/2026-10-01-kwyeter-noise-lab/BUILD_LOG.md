# BUILD_LOG — Noise Lab

- [start] Step 0: latest dated folder on this branch (2026-06-18-regex-dojo) is complete; no interrupted build. Local `builds/index.md` (through 2026-06-24) used; `gh` is unavailable in this environment, so the open-PR resync was skipped and `origin/main`'s index was not newer than the local copy.
- Orient: day 274, category index 3 = D. No pending D ideas, so fresh generation. Chose Noise Lab (see WhyThis.md); non-winners added to ideas.md as IDs 13-15.
- PRD written before code.
- Build: `src/dsp.js` (FFT, spectral shaping, seamless loops, Welch measurement, WAV encoder) then `index.html` + `src/app.js`.
- Decision: classic scripts rather than ES modules, because Chrome blocks module loading from `file://`.
- Decision: synthesis in the frequency domain on a cached white spectrum, so slider moves cost one inverse FFT per channel (~150 ms) and the loop is circular by construction. Swell rates are snapped to whole cycles per loop.
- Obstacle: the first test run hung for minutes. Cause was a per-sample `expect` over ~500k values in the WAV clipping test. Replaced with a running max.
- Bug found by UI test: RMS meter ignored the volume setting. Fixed in app.js.
- Bug found by test: size-cap test used too few repeats. Fixed the test input.
- Tests: 37 passed, 0 failed (25 DSP, 12 UI).
- Security checklist: no innerHTML, no eval, no network calls, no credentials, share-link input sanitised and clamped.
- Not verified: actual audible playback (no audio device in the build container). Transport state, graph setup and exports are tested; sound output itself was not heard.
- Build complete. Success criteria reviewed. All tests passing.
