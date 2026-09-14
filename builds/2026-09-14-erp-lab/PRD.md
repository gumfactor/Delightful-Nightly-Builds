# PRD — ERP Lab: Event-Related Potentials & the Concealed Information Test

> **Build date:** 2026-09-14
> **Category:** E — Learning Aid
> **Complexity:** Ambitious
> **Day of week:** Monday

---

## Goal

An interactive browser trainer that teaches event-related potential (ERP/EEG) methodology — trial averaging, artifact rejection, and frequency-domain filtering — and applies it to the P300-based Concealed Information Test (CIT), the real forensic-neuroscience paradigm used to detect concealed recognition, with every statistic computed live from synthetic data via from-scratch signal-processing and permutation-test code.

## User Story

As an Associate Professor who runs a forensic and affective neuroscience lab and teaches Stress and Coping, Social Affective Neuroscience, and AI Applications for Psychologists, I want an interactive tool that walks through the actual mechanics of ERP data processing (averaging, artifact rejection, filtering) and the P300 Concealed Information Test methodology used in forensic-neuroscience lie-detection research, so that I have a teaching aid I can point students/RAs to that makes the statistics and its real limitations (false-positive rate, sample-size dependence) tangible rather than abstract, in a topic none of the eight prior Learning Aid builds cover.

## Scope

### In Scope
- **ERP Basics tab**: generate single-trial synthetic EEG epochs (an evoked-potential bump + Gaussian noise); slider for number of trials (1–200) and noise SD; live-redrawn Canvas plot overlaying a sample of single trials against the running grand average; a live-measured SNR readout compared against the theoretical √N improvement law.
- **Artifact Rejection tab**: same epoch generator with an adjustable eye-blink-artifact contamination rate; a peak-to-peak amplitude rejection threshold slider; live plot of the average with vs. without rejection, and a live count of trials rejected/retained.
- **Frequency Domain tab**: a synthetic EEG-like time series (alpha-band oscillation + simulated 60 Hz line noise + broadband noise); a from-scratch radix-2 FFT computes and plots the power spectrum; a moving-average low-pass filter slider shows the filtered time-domain signal and its cleaned spectrum side by side.
- **CIT Lab tab** (P300 Concealed Information Test): simulate a Probe (crime-relevant, "guilty knowledge") vs. Irrelevant stimulus condition for a synthetic subject; sliders for a "concealed-knowledge effect size" and an "innocent suspect" toggle (zero true effect, to teach false positives); grand-average waveforms for both conditions plotted together; a from-scratch permutation test (condition-label shuffling) on mean P300-window amplitude reports an observed difference, a null distribution, and a p-value driving a "detected / not detected" call; an explicit panel stating the test's real false-positive/specificity limitations — this is a teaching tool for the statistical methodology, not an operational lie-detection claim.
- **Quiz tab**: 16 questions — 8 fixed conceptual questions (what averaging does to SNR, why line noise appears at 60 Hz, what a permutation test null distribution represents, CIT false-positive framing) and 8 questions regenerated each load from the live math functions (e.g., "given N trials and noise SD X, what's the expected SNR gain?"), scored with localStorage persistence.
- Optional "Explain this" panel: a session-only, browser-entered Anthropic API key sends only already-computed aggregate numbers (never raw waveform arrays) to Claude Haiku for a plain-English explanation; an unconditional deterministic template fallback when no key is set, verified to make zero network calls in that case.

### Out of Scope
- Real EEG hardware/file format (EDF/BDF) import — everything is synthetic, clearly labeled as such.
- Multi-subject/group-level CIT statistics (this build is single-subject, single-session).
- Any claim of real-world forensic validity beyond what the simulated statistics actually show.
- A build step/bundler — classic `<script>` tags only, so `index.html` opens directly via `file://`.

## Tech Stack

- **Language:** HTML/CSS/JS (classic scripts, no ES modules)
- **Framework:** None — native Canvas 2D for all plots
- **Dependencies:** None at runtime (no CDN libraries); Playwright (`@playwright/test`) as a dev-only test dependency
- **Runtime requirement:** Open `index.html` directly in any modern browser — no server, no install needed

## Data Structure

Entirely client-side and stateless between sessions except quiz score, which persists in `localStorage` under key `erplab_quiz_best` (a single integer, 0–16). All EEG data is synthetically generated in-browser via a seeded PRNG (`mulberry32`) + Box-Muller Gaussian transform — no files, no external data source. Core in-memory shapes:
- **Epoch**: `Float64Array` of length 256 (1 second @ 256 Hz), one per simulated trial.
- **EpochSet**: `{epochs: Epoch[], sampleRate: 256, preStimSamples: 51}` (≈200ms pre-stimulus baseline).
- **PermutationResult**: `{observedDiff, nullDistribution: number[], pValue, nPermutations}`.

## Folder Structure

```
builds/2026-09-14-erp-lab/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── package.json
├── playwright.config.js
├── src/
│   ├── styles.css
│   ├── mathlib.js       # PRNG, Gaussian noise, FFT, filter, permutation test
│   ├── epochs.js         # ERP waveform generation, averaging, SNR, artifact rejection
│   ├── quiz.js            # question bank + live-generated question logic
│   └── app.js             # tab wiring, sliders, Canvas rendering, AI-explain panel
└── tests/
    └── erplab.spec.js
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/erplab.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - `mulberry32`/Gaussian RNG: determinism for a fixed seed, and mean/SD of a large sample land within tolerance of 0/1.
  - FFT correctness: a hand-computed 8-point DFT reference (computed independently before the JS was written) matches `fft()`'s output to floating-point tolerance; Parseval's theorem (sum of squared time-domain samples ≈ sum of squared-magnitude spectrum / N) holds as an independent cross-check.
  - FFT recovers a known synthetic sine frequency's peak bin correctly.
  - Epoch averaging: SNR measured from an averaged waveform improves proportionally to √N across trial counts, within tolerance.
  - Peak-to-peak artifact rejection: a synthetic epoch set with known contaminated trials is rejected at the expected count for a given threshold.
  - Moving-average filter: known effect on a synthetic signal (attenuates a high-frequency component while preserving a low-frequency one), verified via before/after power spectra.
  - Permutation test: on a null case (two samples drawn from the identical distribution) the p-value is not systematically small (sanity/calibration check across repeated runs); on an extreme separated case the p-value is small — both cross-checked against a hand-computed reference.
  - CIT "innocent suspect" toggle produces a p-value distribution consistent with no true effect (guards against false-positive framing failing silently).
  - UI: each tab renders and switches correctly; sliders update displayed numeric stats and redraw the canvas; artifact-rejection count updates with the threshold slider; quiz completes end-to-end and persists best score in `localStorage`.
  - Security: a hostile string typed into the AI-context field, and a mocked hostile Anthropic API response (`<script>`/`onerror` payloads), both render as inert text; zero network requests occur anywhere with no API key set.
  - Responsive: no horizontal overflow at a 375px mobile viewport; zero console/page errors across a full interaction pass.

## Success Criteria

1. All tests pass (zero failures).
2. Every statistic shown in the UI (SNR, FFT peak frequency, rejection count, permutation p-value) is computed live from the visible slider parameters, never a hardcoded per-preset number — verified by tests that change a slider and assert the displayed stat changes accordingly.
3. The CIT Lab tab's permutation test correctly distinguishes a simulated "guilty" (true effect present) subject from an "innocent" (no true effect) subject across repeated runs, and the UI states the test's false-positive limitation explicitly.
4. The build makes zero network requests when no Anthropic API key is supplied, and the optional AI-explain panel degrades safely (no XSS, no crash) against a hostile mocked response.
5. The page is usable at a 375px mobile viewport with no horizontal scroll and zero console errors.

---

## Scope Changes

None — the full scope above was built as planned.
