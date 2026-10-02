# PRD — Replication Lab

> **Build date:** 2026-10-02
> **Category:** E — Learning Aid
> **Complexity:** Ambitious Project
> **Day of week:** Friday (day 275, index 4)

## Goal

An interactive, predict-then-simulate explainer of the five statistical mechanisms that make studies fail to replicate, driven by real Monte Carlo simulation in the browser.

## User Story

As an associate professor who teaches AI and statistics-adjacent courses and writes grants, I want to show students (and check my own intuition) how low power, peeking, many outcomes, the winner's curse and priors behave, so that I can plan sample sizes and teach replication concretely instead of from slides.

## Scope

### In Scope
- Power lab: simulated vs analytic power, p-value histogram, sample size for 80% power, positive predictive value from prior odds
- Peeking lab: optional stopping false-positive inflation curve against a fixed design
- Many-outcomes lab: familywise error with outcome correlation, none/Bonferroni/Holm correction
- Winner's curse lab: effect-size histogram with significance cutoff and published average
- Bayes lab: live beta-binomial updating, three priors, credible interval, practical-equivalence zone, Bayes factor
- Predict-first flow on the four simulation labs with a running calibration score
- Seeded RNG (deterministic reruns, "new random sample" button), dark/light theme, phone layout
- Plain-language takeaway generated from each result

### Out of Scope
- Anthropic API tutor (kept offline and deterministic; see FutureFeatures)
- Tests other than two-group t-tests and beta-binomial models
- Persistence of prediction history across sessions

## Tech Stack

- **Language:** HTML/CSS/JS (no build step)
- **Framework:** None; canvas charts written for this build
- **Dependencies:** `@playwright/test@1.56.1` (dev only)
- **Runtime requirement:** open `index.html` in any modern browser

## Data Structure

Stateless. Each lab is an object `{id, controls[], predict?, run(params, seed) -> {stats[], draw(canvas), takeaway, actual?}}`. Stats core (`src/stats.js`) exposes pure functions: RNG, t distribution, t-test, power, simulation of studies/peeking/forking, beta posterior, Bayes factor.

## Folder Structure

```
builds/2026-10-02-replication-lab/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── package.json
├── package-lock.json
├── playwright.config.js
├── src/
│   ├── stats.js
│   ├── charts.js
│   ├── labs.js
│   ├── app.js
│   └── styles.css
└── tests/
    ├── stats.spec.js
    └── ui.spec.js
```
`node_modules/` is not committed (run `npm install` before tests).

## Testing Strategy

- **Framework:** Playwright test runner (Node-side for the stats core, Chromium for the UI)
- **Test file location:** `tests/stats.spec.js`, `tests/ui.spec.js`
- **Run command:** `npm install && npx playwright test`
- **What will be tested:**
  - Distribution functions against table values; t-test against a hand-computed example
  - Seeded RNG determinism and moments
  - Simulated power vs analytic power; null p-values uniform; winner's curse inflation
  - Peeking inflation, single-look control, monotone cumulative curve
  - Familywise rate vs 1-(1-a)^k, correlation effect, Bonferroni/Holm control, Holm arithmetic
  - Beta posterior, credible interval mass, ROPE, Bayes factor
  - Error handling: invalid n/reps/k, constant data, successes above trials
  - UI flow per lab, prediction scoring, seed determinism, phone width overflow

## Success Criteria

1. All tests pass (zero failures)
2. Simulated power at d=0.5, n=64 is within a few points of 80%, and the required-n solver returns 63–66
3. Each of the five labs renders a chart, headline numbers and a takeaway from the UI
4. Predictions are scored and the running calibration is shown
5. No network calls, no innerHTML, page does not scroll horizontally at 390px
