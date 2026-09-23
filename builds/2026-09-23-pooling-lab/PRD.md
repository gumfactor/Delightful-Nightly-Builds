# PRD — Pooling Lab

> **Build date:** 2026-09-23
> **Category:** E — Learning Aid
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday

---

## Goal

An interactive browser trainer that lets the user simulate nested/hierarchical data across groups and watch, live, how a mixed-effects model's partial-pooling (shrinkage) estimator behaves compared to the naive no-pooling (per-group mean) and complete-pooling (grand mean) alternatives as between-group variance and group sample sizes change.

## User Story

As an Associate Professor running a neuroscience/psychology lab who teaches courses that touch on multilevel/nested data (repeated trials within participants, participants within labs or sites) and wants to strengthen statistical intuition and teaching material, I want to manipulate a simulated multi-group dataset's between-group variance, within-group noise, and per-group sample sizes and see the resulting intraclass correlation (ICC) and shrinkage estimates update live, so that I can build (and teach) real intuition for why and how partial pooling works instead of only reading the formula.

## Scope

### In Scope
- Synthetic nested-data generator: G groups, each group g has n_g observations drawn as `obs ~ Normal(group_mean_g, sigma^2)` where `group_mean_g ~ Normal(grand_mean, tau^2)`.
- Seeded PRNG (mulberry32) so a given seed always reproduces the same dataset — needed for deterministic tests and for a "same seed" reproducibility feature in the UI.
- Live-computed statistics, all derived from the same shared `src/stats.js` engine the tests exercise directly:
  - Per-group raw mean (no pooling / "fixed effects" estimate)
  - Grand mean of all observations (complete pooling estimate)
  - Empirical-Bayes partial-pooling (shrinkage) estimate per group: `weight_g = tau2 / (tau2 + sigma2/n_g)`, `estimate_g = weight_g * groupMean_g + (1 - weight_g) * grandMean`
  - True intraclass correlation from the generating parameters: `ICC = tau2 / (tau2 + sigma2)`
  - Empirical ICC estimated from the generated sample via one-way ANOVA variance decomposition (between-group / total variance), so the user can see the sample estimate track the true parameter
- Interactive controls: slider for between-group SD (tau), slider for within-group SD (sigma), a per-group sample-size profile toggle (equal sizes vs. one deliberately small group vs. one deliberately large group), a numeric seed field, and a "Regenerate Data" button.
- Live chart (Canvas 2D): one column per group showing three markers (no-pooling, partial-pooling, complete-pooling) connected by a line, so the shrinkage "pull" toward the grand mean is visually obvious and the amount of pull differs visibly by group sample size.
- Live numeric readouts: true ICC, empirical ICC, per-group shrinkage weights.
- 8-question interactive quiz on random intercepts vs. fixed effects, ICC interpretation, and shrinkage direction/magnitude, mixing fixed conceptual questions with questions generated from the current live simulation state (e.g. "which group is shrinking the most right now, and why?").
- Optional "Explain This" panel: if the user pastes their own Anthropic API key into a session-only field, a "Explain These Results" button sends the current simulation's numeric summary (group sizes, tau, sigma, ICC, shrinkage weights — no personal data) directly from the browser to the Anthropic Messages API (Claude Haiku) and renders the plain-English explanation via `textContent` only. With no key entered, no network call is ever attempted.

### Out of Scope
- Real multi-level regression with covariates/fixed-effect predictors (this build is about the pooling/shrinkage intuition for group intercepts only, not a full mixed-model fitting engine).
- Uploading or importing the user's own real lab data — this is a simulation/teaching tool, not a data-analysis pipeline, so no file upload is included in scope tonight.
- Crossed random effects or more than one level of nesting (only a single grouping factor: observations within groups).
- Server-side or persisted storage of quiz scores across sessions.

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic `<script>` tags, no ES modules, no bundler — opens directly via `file://`)
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev/test only). Runtime: none — no CDN libraries needed since the chart is drawn on a native `<canvas>` with 2D context. Anthropic API is called directly via `fetch` only if the user supplies their own key at runtime.
- **Runtime requirement:** Open `index.html` directly in any modern browser. No install, no server, no build step.

## Data Structure

All state lives in memory in the page (no persistence needed — this is a live simulation, not a journal). The core data shape produced by `generateNestedData`:

```js
{
  seed: 12345,
  tau2: 4.0,        // true between-group variance
  sigma2: 9.0,       // true within-group (residual) variance
  groups: [
    { id: 0, n: 5,  trueMean: 51.2, observations: [49.1, 53.0, ...] },
    { id: 1, n: 30, trueMean: 48.7, observations: [47.9, 50.1, ...] },
    ...
  ],
  grandMeanTrue: 50.0   // population mean used to generate group means
}
```

Derived stats (computed by pure functions in `src/stats.js`, never mutated back into the raw data object):

```js
{
  grandMean: 49.6,                 // observed grand mean (complete pooling)
  trueICC: 0.308,                  // tau2 / (tau2 + sigma2)
  empiricalICC: 0.27,              // ANOVA-based estimate from the sample
  perGroup: [
    { id: 0, noPooling: 51.0, shrinkageWeight: 0.31, partialPooling: 50.1 },
    ...
  ]
}
```

## Folder Structure

```
builds/2026-09-23-pooling-lab/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── package-lock.json
├── playwright.config.js
├── .gitignore
├── index.html
├── src/
│   ├── styles.css
│   ├── stats.js       (pure simulation + statistics engine, no DOM)
│   ├── render.js       (Canvas 2D chart drawing)
│   ├── quiz.js          (question bank + scoring)
│   ├── explain.js       (optional Anthropic API call, textContent-only rendering)
│   └── app.js           (wires sliders/buttons to stats.js + render.js)
└── tests/
    ├── stats.spec.js    (unit-style tests against the stats engine via addScriptTag)
    └── ui.spec.js        (page-level interaction, mobile viewport, XSS-safety tests)
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/stats.spec.js`, `tests/ui.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - ICC formula correctness at known parameter values, including tau2=0 and sigma2=0 edge cases
  - Shrinkage weight formula correctness, monotonicity in group sample size, and the tau2→0 / tau2→∞ limiting behavior
  - Partial-pooling estimate collapses to grand mean when tau2=0, and to the raw group mean when sigma2=0
  - Grand mean is the size-weighted average of group means (not a naive average of group means) when group sizes differ
  - Seeded RNG determinism: same seed ⇒ identical dataset; different seed ⇒ different dataset
  - Requested per-group sample sizes are honored exactly in the generated dataset
  - Empirical ICC (ANOVA-based) recovers the true ICC within a stated tolerance on a large simulated sample
  - Graceful handling of a single-group dataset (no crash, ICC reported as not computable rather than NaN)
  - UI: page loads, canvas renders, ICC readouts populate on load
  - UI: moving the tau slider to 0 updates the displayed ICC to 0 and visually collapses partial-pooling markers onto the complete-pooling line
  - UI: "Regenerate Data" produces a new dataset without a page reload
  - UI: quiz answer selection gives correct/incorrect feedback and updates the score
  - UI: "Explain This" panel with no API key present never issues a network request
  - UI: "Explain This" panel renders a mocked hostile API response (`<script>`/`onerror` payloads) as inert text with zero script execution and zero console/page errors
  - UI: page renders without horizontal overflow at a 375px mobile viewport

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests, run via `npx playwright test`
2. Dragging the between-group SD (tau) slider live-updates the chart, the true ICC readout, and the empirical ICC readout with no page reload
3. The partial-pooling estimate for every group is mathematically between its no-pooling and complete-pooling estimate (inclusive at the tau=0/sigma=0 limits), verified both by unit test and visually in the chart
4. A group with a small sample size visibly shrinks more toward the grand mean than a group with a large sample size under identical tau/sigma, both in the numbers and in the chart's line angles
5. The optional AI-explain panel never calls the network without a user-supplied key, and any AI response text is rendered without executing as HTML/script (verified against a mocked hostile payload)

---

## Scope Changes

None — the full scope above was completed as planned tonight.
