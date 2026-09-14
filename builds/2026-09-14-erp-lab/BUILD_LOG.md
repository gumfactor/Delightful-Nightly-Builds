# Build Log — ERP Lab

### [Step 0] Incomplete-build check
Checked local `builds/` and the most recent open PR branch (`claude/cool-sagan-vvj3j8`, PR #98, 2026-09-13 "Preprint Pulse"). Its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — no interrupted build to resume.

### [Step 1] Orient
Read `PROFILE.md`, `STANDARDS.md`, synced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (91 total builds logged, last build 2026-09-13).

### [Step 2] Decide
Day of year 257 → category index 4 → Category E — Learning Aid. Category E backlog lottery: 25% gate, rolled 56 → missed → fresh idea generation. See `WhyThis.md` for the 3 candidates considered and full reasoning. Selected: ERP Lab (EEG/ERP methodology + P300 Concealed Information Test).

### [PRD] Step 3–4
Wrote `PRD.md` before any code — full scope, tech stack, data structure, folder structure, testing strategy, 5 success criteria.

### [Build] Step 5 — math core
Implemented `src/mathlib.js` (mulberry32 PRNG, Box-Muller Gaussian transform, iterative radix-2 Cooley-Tukey FFT, power spectrum, moving-average filter, Fisher-Yates shuffle, permutation test) and `src/epochs.js` (ERP template generation, epoch/noise generation, eye-blink artifact injection, epoch averaging, peak-to-peak artifact rejection, window-mean amplitude extraction for the CIT permutation test).

Cross-checked every core function against independently computed reference values before writing UI code:
- FFT of `[1,2,0,-1,1,2,0,-1]` matched a direct O(N²) DFT summation computed independently in Python (not derived from the same algorithm).
- Parseval's theorem held exactly (time-domain energy = frequency-domain energy / N).
- FFT recovered a synthetic 10 Hz sine wave's frequency exactly.
- `mulberry32` confirmed deterministic for a fixed seed; the Gaussian sampler's empirical mean/SD converged to 0/1 over 200,000 draws.
- Epoch-averaging baseline noise SD tracked the theoretical `σ/√N` law across N ∈ {1,4,16,64,200}.
- Permutation test correctly separated a null case (p = 0.64) from a strongly separated case (p = 0.0005).

**Calibration finding:** initial artifact-rejection parameters (noiseSD=5µV, blinkAmp=45µV, threshold=30µV) caused clean (uncontaminated) trials to frequently exceed the rejection threshold from noise alone — measured clean-trial peak-to-peak at noiseSD=5 ranged up to 42µV, well past the 30µV threshold. Empirically remeasured the clean-vs-contaminated peak-to-peak distributions and recalibrated to noiseSD=3µV / blinkAmp=45µV / threshold=35µV, which gives a clean gap (clean trials: 14–28µV; contaminated: 52–67µV) — confirmed via a 0-mismatch check between the artifact-injection flag and the threshold-rejection decision on a 200-trial simulated set. Applied this calibration to the quiz's live artifact-rejection question template; the interactive Artifact Rejection tab's default slider values also use these calibrated numbers.

### [Build] Step 5 — UI
Implemented `src/quiz.js` (8 fixed conceptual questions + 4 live-question generator templates instantiated twice each = 8 live questions per attempt, all answers computed from the same math functions used elsewhere in the app), `src/app.js` (tab switching, Canvas 2D rendering for all 4 data tabs, slider wiring, the CIT permutation-test runner, the AI-explain panel with a deterministic fallback and zero-network-without-a-key guarantee, and the quiz state machine with `localStorage` best-score persistence), `index.html`, and `src/styles.css` (dark-mode-first with a light-mode media-query override, CSS custom properties, mobile-responsive).

### [Tests] Step 6 — test run
Wrote `tests/erplab.spec.js` (32 tests) covering: math-core correctness (FFT vs. hand-computed DFT, Parseval, sine-frequency recovery, SNR √N law, artifact-rejection separation, filter frequency-response, permutation-test null/effect calibration, quiz-generator validity/determinism), UI across all 5 tabs, CIT Lab statistical behavior (innocent-toggle zeroing the true effect across repeated runs), AI-explain XSS-safety against a mocked hostile Anthropic response and a hostile API-key field, zero-network-calls with no key set, full 16-question quiz completion with `localStorage` persistence, 375px mobile-viewport overflow, and a full-session console/page-error check.

First run: 31 passed, 1 failed (`Artifact Rejection: rejected + kept always equals the trial count` — the test used a `data-testid` selector for a `<span>` that only carried an `id`, not a `data-testid` attribute; the earlier "ntrials value" readout spans were never given `data-testid`). Fixed by switching that one assertion to an `#id` selector, matching the pattern already used successfully elsewhere in the same test file.

[UTC] Tests: 32 passed, 0 failed.

### [Verify] Step 7 — manual QA and success criteria
Ran a manual headless-Chromium pass independent of the automated suite: screenshotted all 5 tabs plus the CIT tab after running the permutation test plus a 375px mobile viewport, with zero console/page errors recorded during the full pass. Visual confirmation: the ERP Basics average waveform is visibly smoother than the single-trial overlay; the Frequency Domain spectrum shows two distinct peaks exactly at 10 Hz and 60 Hz; the Artifact Rejection tab's post-rejection (green) average is visibly cleaner than the all-trials (red) average; the CIT Lab probe (pink) trace sits visibly above the irrelevant (blue) trace given a nonzero effect size; the mobile layout wraps the tab bar to two rows with no horizontal overflow.

Success criteria review:
1. All tests pass (zero failures) — 32/32 passed. ✅
2. Every statistic is computed live, never hardcoded per-preset — verified by tests that change a slider/toggle and assert the displayed stat changes accordingly (e.g. measured-SD test, threshold-vs-rejected-count monotonicity test, theoretical-SD exact-value test). ✅
3. The CIT Lab permutation test distinguishes a "guilty" from an "innocent" simulated subject across repeated runs, and the UI states the false-positive limitation explicitly (see the "Limitation" callout on the CIT Lab tab) — verified by the innocent-toggle test (detection rate well below what a true 10µV effect produces) and the strong-effect test (p < 0.05). ✅
4. Zero network requests occur with no API key set, and the AI-explain panel degrades safely against a hostile mocked response (zero script execution, zero `<script>` tags in the output DOM) — verified directly. ✅
5. Usable at 375px mobile viewport with no horizontal scroll and zero console errors — verified both by the automated test and the manual screenshot pass. ✅

Security checklist (STANDARDS.md): no `.env` files; grepped `src/`, `index.html`, `tests/` for `password`/`api_key`/`secret`/`token`/`private_key` value-assignment patterns and for `sk-ant-`/`AKIA`/`ghp_`-shaped strings — the only hit was the `placeholder="sk-ant-..."` UI hint text on the (empty) API-key input, not a real credential; no `eval()`/`exec()`/`new Function()` anywhere; no `innerHTML` assignments anywhere in the app (all dynamic text uses `textContent`, including quiz choices, feedback, and the AI-explain output); no `os.system`/`subprocess` calls (pure client-side JS, no shell interaction at all); no file-path handling of any kind (fully client-side, no filesystem reads outside the build's own static assets).

### [Docs] Step 8 — documentation complete
- `FutureFeatures.md`: 9 concrete suggestions.
- `Manual.md`: quick start, tab-by-tab guide, AI-explain panel usage, test run command, known limitations.

Build complete. Success criteria reviewed. All tests passing.
