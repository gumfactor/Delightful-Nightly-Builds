# PRD — Mediation & Moderation Analysis Lab

## Goal

An interactive browser-based trainer that teaches mediation analysis (indirect effects through a third variable) and moderation analysis (interaction effects that change a relationship's strength), the two most commonly taught and applied multivariate techniques in social, affective, and stress psychology research, using live-manipulable synthetic data and statistics computed fresh from scratch on every sample — never a hardcoded answer.

## User Story

As a professor who teaches Stress and Coping and Social Affective Neuroscience, and who supervises students running mediation/moderation models on their own data, I want an interactive tool where I can manipulate the strength of a simulated relationship, generate a fresh random sample, and see the actual regression paths, bootstrap confidence interval for the indirect effect, and the region of significance for an interaction — computed live, correctly, and explained — so I can use it in class to build intuition that a static slide deck or textbook diagram cannot provide, and so students can build the same intuition on their own between classes.

## Scope

### In Scope

- **Mediation Lab tab**: X → M → Y path model. Sliders control the true data-generating process (path a, path b, direct effect c′, noise level, sample size N, random seed). A "Generate Sample" button draws a fresh dataset and computes, live, from that exact sample:
  - Path a (X→M), path b and c′ (Y→X+M), total effect c (Y→X), with standard errors
  - Indirect effect (a×b) with a bootstrap percentile 95% confidence interval (resampling with replacement, 2000 resamples by default, using the same seeded PRNG stream so results are exactly reproducible for a given seed)
  - Sobel test (delta-method standard error and z) shown alongside the bootstrap CI as a teaching contrast (why bootstrap is generally preferred for the non-normal sampling distribution of a product of coefficients)
  - A live path diagram (Canvas 2D) labeled with the four computed path coefficients
  - Algebraic identity check displayed: c ≈ c′ + a×b
- **Moderation Lab tab**: Y = b0 + b1·X + b2·Z + b3·(X×Z) model, X and Z mean-centered before the interaction term is formed. Sliders control the true interaction strength (b3), main effects, noise, N, and seed. On "Generate Sample":
  - Full regression output (all four coefficients, SEs, t, p) via one general OLS engine
  - Simple slopes of X on Y at Z = −1 SD, mean, +1 SD, each with its own SE, t, and p (derived from the coefficient covariance matrix, not re-run regressions)
  - Johnson–Neyman region of significance: the exact Z value(s), solved analytically as roots of a quadratic in Z, where the simple slope's significance boundary is crossed
  - A scatterplot of X vs Y colored by Z, with the three simple-slope lines drawn, and a Z-axis strip showing the significant/non-significant region
- **Quiz tab**: 16 questions — 8 fixed conceptual questions (mediation vs. moderation, what a CI crossing zero means, why centering matters, etc.) and 8 questions answered from a freshly generated scenario each time the quiz is taken, whose correct answer is derived live from the same engine functions used in the two lab tabs (never a hardcoded fact). Final screen shows score, per-question review, and a restart option.
- **Optional AI interpretation**: a per-result "Explain this in plain English" button that sends only the already-computed aggregate numbers (path coefficients, CI bounds, p-values, simple slopes, JN boundary — never raw sample rows) directly from the browser to the Claude API (model `claude-3-5-haiku-20241022`) using a user-supplied session-only API key field (never persisted to localStorage or sent anywhere else). An unconditional deterministic template sentence is shown instead whenever no key is set, verified to make zero network calls in that case.
- Dark-mode-only self-contained HTML/CSS/JS app, mobile-responsive, opens directly via `file://` (classic scripts, no ES modules, no build step).

### Out of Scope

- Multi-category moderated mediation, serial/parallel multiple mediators, or latent-variable (SEM) models — single-mediator and single-moderator models only, which is the level actually taught in the named undergraduate/graduate courses
- Real participant data upload — this is a teaching simulator over synthetic data, not a data-analysis tool for the user's own studies (a different, non-Learning-Aid build would be needed for that)
- Any server component or persistence beyond the current page session — no localStorage is needed since there is no cross-session state to preserve (quiz score resets each session by design, matching the "generate a fresh scenario" teaching goal)

## Tech Stack

- Vanilla HTML/CSS/JS, classic `<script>` tags (no ES modules, no bundler) so the app opens directly via `file://`
- Native Canvas 2D for the path diagram, scatterplots, and region-of-significance strip — no charting library
- Direct `fetch()` call to the Anthropic Messages API from the browser for the optional AI interpretation layer, gated on a session-only API key input
- Playwright for tests, run against the pre-installed Chromium

## Data Structure

All state lives in page-scoped JS variables (no persistence):

- `mediationState`: `{ trueA, trueB, trueCPrime, noiseSD, n, seed, sample: {X, M, Y}, results: {a, aSE, b, bSE, cPrime, cPrimeSE, c, cSE, indirect, bootstrapCI: [lo, hi], sobelSE, sobelZ, sobelP} }`
- `moderationState`: `{ trueB1, trueB2, trueB3, noiseSD, n, seed, sample: {X, Z, Y}, results: {beta: [b0,b1,b2,b3], se: [...], cov: 4x4 matrix, dof, simpleSlopes: [{ zLabel, zVal, slope, se, t, p, sig }], jnRoots: [z1, z2] | null } }`
- `quizState`: `{ questions: [{ type: 'fixed'|'live', prompt, choices, correctIndex, explanation }], currentIndex, score, answers: [] }`

## Folder Structure

```
builds/2026-09-05-mediation-moderation-lab/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── playwright.config.js
├── src/
│   ├── style.css
│   ├── rng.js            — seeded PRNG (mulberry32) + Box-Muller Gaussian noise
│   ├── stats.js           — OLS via Gauss-Jordan (partial pivoting), covariance matrix, Student t CDF (regularized incomplete beta) and bisection-based inverse t CDF, normal CDF
│   ├── mediation-engine.js — path a/b/c/c', bootstrap CI, Sobel test
│   ├── moderation-engine.js — centered interaction regression, simple slopes, Johnson-Neyman quadratic solve
│   ├── quiz-data.js        — 8 fixed conceptual questions + 8 live-question generators
│   ├── ai-explain.js       — aggregate-only Claude Haiku call + deterministic fallback
│   └── app.js              — tab switching, UI wiring, Canvas rendering for all three tabs
└── tests/
    ├── stats.spec.js            — OLS/matrix/t-distribution correctness vs. hand-computed fixtures
    ├── mediation-engine.spec.js — path coefficients, bootstrap CI, Sobel test, identity check
    ├── moderation-engine.spec.js— regression, simple slopes, Johnson-Neyman roots vs. hand-computed fixtures
    ├── mediation-ui.spec.js     — UI interaction, path diagram values, seed reproducibility
    ├── moderation-ui.spec.js    — UI interaction, JN region rendering
    ├── quiz.spec.js             — question flow, scoring, live-answer correctness
    └── security.spec.js         — XSS payload inertness, no network calls without API key, mobile viewport
```

## Testing Strategy

- **Engine correctness (`stats.spec.js`, `mediation-engine.spec.js`, `moderation-engine.spec.js`)**: every core statistical function is tested via `page.evaluate()` against fixture datasets whose expected coefficients, standard errors, and Johnson-Neyman roots were independently hand-computed in a from-scratch pure-Python reference implementation (Gauss-Jordan matrix inversion with partial pivoting, written independently of the JS engine) during the design phase of this build, not derived from the JS code itself. Assertions use a numeric tolerance of 1e-6 relative to those independently-computed reference values.
- **Determinism**: because all randomness (sample generation and bootstrap resampling) is drawn from a single seeded PRNG, tests assert that the same seed reproduces bit-for-bit identical results across two separate "Generate Sample" runs — a real regression-catcher for any hidden non-determinism (e.g. an accidental `Math.random()` call).
- **UI behavior**: slider changes update displayed values, the path diagram/scatterplot render without console errors, significance styling (color/label) matches the sign of the CI or JN boundary actually computed for that sample.
- **Quiz**: both fixed and live-question paths are exercised; a live question's correct answer is verified against the same engine function it displays, not a separately hardcoded value; scoring and restart are tested.
- **Security**: a `</script><script>` + `<img onerror>` payload is round-tripped through the AI-explanation text-rendering path (mocked Claude response) and confirmed to render as inert text with zero script execution; a run with no API key set is confirmed to make zero network requests.
- Run with `npx playwright test` from this build folder; `playwright.config.js` sets `testDir: './tests'` and points `use.launchOptions.executablePath` at the container's pre-installed Chromium.
- Minimum 15 tests, all must pass with zero failures before this build is committed.

## Success Criteria

1. The mediation engine's path coefficients, standard errors, and Sobel statistic exactly match (within 1e-6) the independently hand-computed pure-Python reference values for the fixture dataset, and the identity c ≈ c′ + a×b holds for every freshly generated sample.
2. The moderation engine's regression coefficients, simple slopes at ±1 SD, and Johnson-Neyman region boundary exactly match (within 1e-6) the independently hand-computed pure-Python reference values for the fixture dataset.
3. Given the same seed, two separate sample-generation runs (mediation and moderation) produce bit-for-bit identical results, demonstrating no hidden non-deterministic randomness.
4. All 16 quiz questions are answerable and correctly scored, with every live-computed question's correct answer traceable to the same engine output shown elsewhere in the app — never a separately hardcoded fact.
5. The full Playwright suite (minimum 15 tests) passes with zero failures, including the XSS-inertness and zero-network-calls-without-a-key security checks.
