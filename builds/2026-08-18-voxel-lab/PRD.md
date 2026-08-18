# PRD — Voxel Lab

## Goal
An interactive browser trainer that teaches the fMRI preprocessing/analysis pipeline and the multiple-comparisons ("dead salmon") problem through live, from-scratch simulation rather than static explanation.

## User Story
As a neuroscience lab director who teaches neuroimaging methods and runs fMRI studies, I want an interactive tool that lets me (and my students/RAs) see *why* each preprocessing step matters and *why* voxel-wise statistical correction is not optional, so that I have a teaching aid grounded in real computation rather than a slide deck, and a quick refresher I can open myself before writing a methods section.

## Scope

### In scope
- **Pipeline tab**: 6 canonical fMRI preprocessing/analysis steps (Motion Correction, Slice Timing Correction, Spatial Normalization, Spatial Smoothing, HRF Convolution & GLM, Statistical Thresholding), each with:
  - A plain-English explanation of what the step does and why it's needed
  - A live Canvas 2D before/after visual demonstration generated from synthetic data (procedurally generated 2D "slice" grid with injected motion jitter / smoothing kernel / etc. — no real patient data, ever)
  - One common pitfall if the step is skipped or misapplied
  - The HRF/GLM step includes a live double-gamma hemodynamic response function convolved against a boxcar task design, rendered as a chart, plus least-squares beta-weight recovery from a synthetic noisy signal
- **Multiple Comparisons Lab tab**: the flagship interactive simulator.
  - User picks voxel count (100–20,000), a correction method (None / Bonferroni / Benjamini-Hochberg FDR / simplified cluster-extent), and alpha (0.01–0.10)
  - "Run simulation" generates N independent standard-normal noise voxels (Box-Muller, no true signal anywhere), computes p-values, applies the selected correction, and reports how many voxels survive as "significant" — i.e., false positives, since there is no true signal
  - Runs configurable repeated trials (1–200) and shows a live histogram of false-positive counts per trial across methods, plus a side-by-side "brain slice" visualization highlighting surviving (false-positive) voxels under the different methods on the same noise draw
  - All statistics computed from scratch and cross-checked against hand-worked reference values in tests (Bonferroni threshold = alpha/n; BH-FDR step-up procedure; cluster labeling via 4-connected flood fill)
- **Quiz tab**: ~15 questions mixing conceptual multiple-choice (pipeline step order/purpose/pitfalls) and live-computed questions (e.g., "with alpha=0.05 and 8,000 voxels, what is the Bonferroni-corrected threshold?" — answer checked against the real formula, not a hardcoded string), with a running score and a final grade.
- Dark-mode UI, mobile-responsive, accessible semantic HTML, no external network calls of any kind (fully self-contained, no AI integration needed — the differentiating layer here is the from-scratch statistical simulation, not AI-generated prose).
- Playwright test suite covering math correctness, UI flows, and security.

### Out of scope
- Real DICOM/NIfTI file loading or real neuroimaging data of any kind — this is a teaching simulator on synthetic data only, never a research analysis tool
- 3D brain rendering (WebGL) — 2D Canvas slice visualizations only, to keep scope shippable in one session
- Full SPM/FSL/AFNI feature parity — this teaches the concepts, not a working pipeline
- Any AI/LLM integration — the domain here doesn't benefit from an AI prose layer the way editorial/summarization builds do; the differentiator is the interactive simulation itself
- Saving/exporting results — this is a single-session teaching tool; no persistence layer needed (no user data worth persisting)

## Tech Stack
Vanilla HTML/CSS/JS, classic `<script>` tags (no ES modules, no bundler) so `index.html` opens directly via `file://` with zero build step, following the established convention of prior Category E builds (Power Lab, CircuitLab, Bayes Lab, Signal Detection Lab). Native Canvas 2D for all visualizations — no charting library needed. Playwright (`@playwright/test`) for tests, matching `builds/2026-06-18-regex-dojo/playwright.config.js`'s pinned-executable pattern for this container's Chromium install.

## Data Structure
No persistence — everything is generated in-memory per session:
- `SimVoxel = { value: number, pValue: number, significant: boolean }` — one simulated noise voxel
- `SimTrial = { method: string, alpha: number, voxelCount: number, falsePositives: number, voxels: SimVoxel[] }` — one Monte Carlo trial
- `QuizQuestion = { id: string, prompt: string, type: 'choice'|'computed', choices?: string[], correctIndex?: number, computeAnswer?: (params) => number, tolerance?: number }`
- `PipelineStep = { id: string, title: string, explanation: string, pitfall: string, render: (ctx, phase) => void }`

## Folder Structure
```
builds/2026-08-18-voxel-lab/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── playwright.config.js
├── index.html
├── src/
│   ├── styles.css
│   ├── stats.js        (RNG, Bonferroni, BH-FDR, cluster labeling, double-gamma HRF, convolution, least-squares)
│   ├── pipeline.js      (6 pipeline step definitions + canvas renderers)
│   ├── mc-sim.js        (multiple comparisons Monte Carlo engine)
│   ├── quiz.js           (question bank + scoring)
│   └── app.js            (tab wiring, DOM init, glue code)
└── tests/
    ├── stats.spec.js
    ├── pipeline.spec.js
    ├── mc-sim.spec.js
    ├── quiz.spec.js
    ├── security.spec.js
    └── responsive.spec.js
```

## Testing Strategy
Playwright drives the real page in headless Chromium (pinned `executablePath`, no live browser install). Pure math functions (`stats.js`) are exposed on `window` and asserted directly via `page.evaluate` against hand-worked reference values — this is the highest-risk correctness surface (wrong stats would teach the wrong lesson) so it gets the most direct coverage:
- Bonferroni threshold exactly equals `alpha / n` for several `(alpha, n)` pairs
- Benjamini-Hochberg FDR reproduces the textbook worked example (a small fixed p-value array with a known number of rejections)
- Gaussian RNG (Box-Muller) sample mean/std over a large N falls within tolerance of 0/1
- Double-gamma HRF peaks near ~5-6s post-stimulus and is normalized to a peak of 1.0
- Least-squares GLM beta recovery on a synthetic signal-plus-noise series recovers the true injected beta within tolerance
- 4-connected cluster labeling on a small hand-built binary grid produces the expected cluster count/sizes

UI-level tests cover: pipeline step navigation and that each step renders non-blank canvas content and its explanation/pitfall text; the multiple-comparisons simulator actually runs and that, at a large voxel count, uncorrected false-positive counts are on average meaningfully higher than Bonferroni/FDR-corrected counts (a live behavioral assertion, not just a math unit test — this is the tool's core teaching claim and it must hold when exercised through the real UI); quiz answer submission, scoring, and that a computed-answer question is checked against the live formula rather than a hardcoded value. Security tests inject `</script><script>alert(1)</script>` and `<img onerror=...>` payloads into any free-text areas (none of the quiz/pipeline content is user-supplied in this build, so this is a defense-in-depth check on the one place a future extension could add user text) and confirm zero dialogs/page errors. Responsive test confirms the layout doesn't break at a 375px mobile viewport.

Minimum 15 tests, all must pass before commit (`npx playwright test`).

## Success Criteria
1. All 6 pipeline steps are navigable and each renders a distinct, non-blank before/after Canvas visualization with correct explanatory text — verified by `pipeline.spec.js`
2. The multiple-comparisons simulator, run through the real UI at a large voxel count (≥5,000) with ≥50 trials, shows uncorrected false positives statistically and substantially exceeding Bonferroni/FDR-corrected false positives on average — verified live, not asserted only in a math unit test
3. All core statistics (Bonferroni, BH-FDR, HRF peak timing, GLM beta recovery, cluster labeling, Gaussian RNG moments) match hand-worked reference values within stated tolerance — verified by `stats.spec.js`
4. The quiz tracks score correctly across all 15 questions including at least one live-computed question checked against the real formula, and reports a final grade
5. Zero external network requests are made anywhere in the app (fully self-contained), and a live script-injection payload renders as inert text with zero dialogs/page errors
6. All ≥15 Playwright tests pass with zero failures
