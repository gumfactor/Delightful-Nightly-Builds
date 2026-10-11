# PRD — Bayes Lab

> **Build date:** 2026-10-11
> **Category:** E — Learning Aid (day 284 → index 4)
> **Complexity:** Ambitious
> **Day of week:** Sunday

---

## Goal

An interactive, offline browser lab with six hands-on lessons that teach Bayesian reasoning (belief updating, base rates, prior sensitivity, Bayes factors vs p-values, shrinkage, calibration) using psychology/neuroscience-flavoured scenarios, all driven by a tested numeric core.

## User Story

As an associate professor building Bayesian statistics skills who teaches psychologists, I want to manipulate priors, data and test properties and see posteriors, credible intervals and Bayes factors update live (and enter my own study's counts or estimates), so that I build real intuition and have a classroom-ready explainer.

## Scope

### In Scope
- Numeric core `src/bayes.js` (no dependencies): log-gamma, beta pdf/cdf/quantile, HDI, beta-binomial update, posterior predictive, exact binomial p-value, Bayes factor (marginal likelihood and Savage–Dickey), ROPE probability, diagnostic-test Bayes + natural frequencies, normal–normal conjugate update, Brier score.
- Lesson 1 "Update a belief": prior presets/custom, sequential success/failure buttons, simulate trials, own-data entry; prior/likelihood/posterior plot; mean, 95% HDI, P(θ>0.5), ROPE, predictive.
- Lesson 2 "Base-rate trap": prevalence/sensitivity/specificity sliders, scenario presets, 1000-person natural-frequency grid, PPV/NPV.
- Lesson 3 "Two researchers": skeptic vs enthusiast priors, same data, sample size slider, convergence plot, n needed to agree.
- Lesson 4 "Bayes factor vs p-value": k/n/θ0 inputs, exact p, BF10/BF01 with verbal label, Savage–Dickey plot, Lindley's paradox preset.
- Lesson 5 "Shrinkage": normal–normal update from prior mean/SD and an estimate/SE; weight on data; replication preset.
- Lesson 6 "Calibration quiz": 8 true/false statements with confidence slider, Brier score, per-question explanation, history in localStorage.
- Responsive, dark/light via CSS variables, keyboard-accessible, hash routing.

### Out of Scope
- MCMC / arbitrary model fitting; server, accounts, network calls of any kind.
- AI tutor (would require sending data and an API key from the browser).

## Tech Stack

- **Language:** HTML/CSS/vanilla JS (classic scripts, global `Bayes`), inline SVG charts
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev only)
- **Runtime requirement:** Open `index.html` in a browser; no build step, no network

## Data Structure

Stateless apart from `localStorage["bayeslab.quiz"]` = JSON array of `{date, brier, correct}` (wrapped in try/catch). Beta distributions are `{a, b}`; lesson state lives in closures.

## Folder Structure

```
builds/2026-10-11-bayes-lab/
├── PRD.md, WhyThis.md, BUILD_LOG.md, FutureFeatures.md, Manual.md
├── index.html
├── package.json, package-lock.json, playwright.config.js
├── src/bayes.js      numeric core
├── src/charts.js     SVG chart helpers
├── src/lessons.js    six lessons + quiz data
├── src/app.js        router/tabs
├── src/style.css
└── tests/core.spec.js, tests/ui.spec.js
```

## Testing Strategy

Playwright (per STANDARDS for HTML/JS). `core.spec.js` loads the page and calls `window.Bayes` via `page.evaluate` against analytically known values (Beta(1,1) update, Γ(5)=24, symmetric HDI, 1% prevalence PPV≈8.3%, Savage–Dickey = marginal-likelihood BF, binomial p for 7/10, edge inputs). `ui.spec.js` drives every lesson through `data-testid` selectors and checks displayed numbers against the core, the quiz scoring, localStorage failure tolerance and invalid input handling. No network calls exist.

## Success Criteria

1. All six lessons render and respond live to inputs; displayed statistics match independently known values.
2. Core functions match analytical results (tolerance 1e-6) including edge cases (k=0, k=n, n=0, a<1).
3. Lindley preset shows p<0.05 while BF01>1; PPV scenario shows <10% for 1% prevalence/90-90 test.
4. Quiz computes Brier score correctly and persists history; works if localStorage throws.
5. ≥15 tests pass; page usable at 375px width with no horizontal scroll.
