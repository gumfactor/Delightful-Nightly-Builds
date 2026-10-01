# PRD — Noise Lab

## Goal
A browser tool that synthesises seamless, shapeable noise loops (sleep, focus, masking, tinnitus notch noise) with a live spectrum, level readouts, sleep timer, shareable links and WAV export.

## User Story
As someone who works with sound sensitivity and tinnitus-adjacent research (Kwyeter), I want to design noise by its spectrum instead of picking from a stock-sound app, so I can build a masking or notched-noise sound exactly to spec, check what it really contains, and export it as a loop that plays anywhere.

## Scope
**In:** frequency-domain noise synthesis with adjustable slope (blue to brown), low/high cut, up to 2 peaking bands, a precise notch, up to 3 slow "swell" modulators snapped to whole cycles for seamless loops; stereo (independent channels); Welch spectrum plot; RMS, A-weighted and peak readouts; presets; sleep timer with fade; tinnitus pitch-match tone that sets the notch centre; URL-hash sharing; 16-bit WAV export (loop, 1 min, 10 min); dark/light theme; phone layout.
**Out:** calibrated SPL measurement (device-dependent), medical claims, accounts/cloud storage, AI calls (nothing here needs them), recording microphones.

## Tech Stack
Vanilla HTML/CSS/JS, no build step, no runtime dependencies. Web Audio API for playback. `src/dsp.js` is a UMD module (browser global `NoiseDSP`, or `require` in Node). Playwright (`@playwright/test` 1.56.1) for tests.

## Data Structure
`params`: `{slope, hp, lp, seed, level, notch:{on,freq,width,depth}, bands:[{freq,width,gain}x2], mods:[{rate,depth}x3]}`. Always passed through `sanitizeParams` (clamps, fills defaults, drops unknown keys). Sharing serialises it into `location.hash`. Nothing is persisted or sent anywhere.

## Folder Structure
```
builds/2026-10-01-kwyeter-noise-lab/
├── PRD.md, WhyThis.md, BUILD_LOG.md, FutureFeatures.md, Manual.md
├── index.html
├── package.json, package-lock.json, playwright.config.js, .gitignore
├── src/dsp.js
├── src/app.js
└── tests/dsp.spec.js, tests/ui.spec.js
```
`node_modules/` and `test-results/` are git-ignored.

## Testing Strategy
Playwright runner for both layers. `dsp.spec.js` exercises the pure DSP in Node: FFT correctness, seeded determinism, slope accuracy (pink −3 dB/oct, brown −6), notch depth and locality, filter cutoffs, band gain, loop seamlessness, modulation quantisation, A-weighting, level maths, sanitising of hostile input, hash round trip, timer fade, WAV header/size/clipping/cap. `ui.spec.js` drives the page in Chromium at phone width: presets, sliders, readouts, canvas painted, pitch-match, transport state, timer, share link restore, corrupt-link fallback, WAV download, no horizontal scroll. No network and no audio hardware are needed.

## Success Criteria
1. A notch of 40 dB at 4 kHz removes ≥25 dB there and changes distant bands by <1 dB (tested).
2. Loops are seamless: wrap-around step ≤5× a typical sample step (tested), and exported WAVs repeat identically.
3. Pink/brown spectra match −3/−6 dB per octave within 1.5 dB (tested).
4. The page works from `file://` with no build step, shows a painted spectrum and live readouts, and downloads a valid stereo WAV.
5. All ≥15 tests pass; hostile share-link input cannot break the page.
