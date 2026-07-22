# PRD — Bayes Lab

> **Build date:** 2026-07-22
> **Category:** E — Learning Aid
> **Complexity:** Ambitious
> **Day of week:** Wednesday

---

## Goal

An interactive browser trainer that teaches Bayesian inference for proportions (the Beta-Binomial model) through psychology-research-grounded scenarios — you set a prior, feed in real trial-by-trial outcomes, and watch the posterior, credible interval, and Bayes factor update live, side by side with the frequentist answer to the same question.

## User Story

As a psychology/neuroscience researcher who explicitly wants to "develop advanced Bayesian statistical workflows" but has never had a hands-on tool to build that intuition, I want to elicit a prior belief about a response rate, sequentially add trial outcomes from a real or hypothetical study, and see exactly how the posterior distribution, credible interval, and Bayes factor evolve — so that I build correct, durable intuition for Bayesian reasoning instead of just reading about it.

## Scope

### In Scope
- 5 pre-built scenario templates grounded in the user's own research domain (clinical response rate, screening-tool positive rate, manipulation-check pass rate, replication success rate, and a free-form Custom scenario), each pre-filling a threshold/null value (`p0`) and a short description
- Beta-Binomial conjugate updating: exact posterior `Beta(α + successes, β + failures)` computed on every trial added
- Two prior-elicitation modes: "Belief mode" (target rate % + prior weight/equivalent sample size slider → computed α, β) and "Advanced mode" (direct α, β numeric inputs), always kept in sync with the same underlying state
- Sequential trial entry: `+ Success`, `+ Failure`, batch add (n successes / m failures at once), Undo last entry, Reset to prior
- Live-updating Canvas 2D chart overlaying the prior curve (faded) and posterior curve (solid) as trials are added
- A step-by-step history table logging n, posterior mean, and 95% credible interval after every update
- Posterior summary panel: mean, mode (when defined), variance/SD, 95% equal-tailed credible interval, and P(θ > p0) / P(θ < p0)
- Bayes Factor panel via the Savage-Dickey density ratio at `p0`: BF10, BF01, and a plain-language strength label (Jeffreys/Lee & Wagenmakers scale)
- Frequentist contrast panel computed from the same (successes, n) data: MLE point estimate, Wilson score 95% CI, and an exact two-sided binomial test p-value against `p0` — displayed alongside the Bayesian panel with explicit interpretation-difference labels
- Optional AI narrative: a session-only Anthropic API key field (never persisted, never sent anywhere but `api.anthropic.com` directly from the browser) that generates a plain-English paragraph interpreting the current computed numbers; a deterministic template always produces the same kind of paragraph from the same numbers when no key is supplied
- All custom-scenario text and AI-generated text rendered via `textContent`/`createElement`, never `innerHTML`, to prevent script injection
- Mobile-responsive dark-mode layout

### Out of Scope
- Full MCMC / non-conjugate models (only the Beta-Binomial conjugate case is covered — sufficient for the core pedagogical goal of building Bayesian intuition)
- Highest Density Interval (HDI); only the simpler, standard equal-tailed credible interval is implemented (clearly labeled as such)
- Multi-parameter / hierarchical models
- Server-side persistence of sessions — state lives only in the current page load (a "Custom" scenario plus manual re-entry is the workaround for resuming a session)
- Numerical optimization-based prior elicitation (matching arbitrary quantiles); the simpler, fully-correct "target rate + equivalent prior sample size" method-of-moments approach is used instead

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic `<script>` tags, no ES modules — opens directly via `file://`)
- **Framework:** None
- **Dependencies:** None at runtime (no CDN libraries — all math and charting is hand-written); Playwright (dev/test only)
- **Runtime requirement:** Open `index.html` directly in a browser, no install or build step needed

## Data Structure

Stateless across page loads — all state lives in an in-memory JS object for the duration of one browser session:

```js
{
  scenario: { key, label, description, p0 },
  prior: { alpha, beta },       // always kept in sync regardless of elicitation mode
  trials: [ { type: 'success'|'failure', n: 1 } , ... ],  // ordered log, replayable
  successes: number,             // derived: sum of trial successes
  failures: number,               // derived: sum of trial failures
  posterior: { alpha, beta }      // derived: prior.alpha + successes, prior.beta + failures
}
```

No files are read or written. The only network call is an optional, user-initiated `fetch` to `api.anthropic.com` carrying no personal data — only the scenario label, the numeric prior/posterior/CI/BF/p-value values already computed and shown on screen.

## Folder Structure

```
builds/2026-07-22-bayes-lab/
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
│   ├── beta-math.js       (pure statistical functions — no DOM — exposed on window for direct testing)
│   ├── ai-narrative.js    (prompt construction + fetch call + deterministic template fallback)
│   └── app.js             (state management, DOM wiring, canvas rendering)
└── tests/
    └── bayes-lab.spec.js
```

## Testing Strategy

- **Framework:** Playwright
- **Test file location:** `tests/bayes-lab.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Core math functions (`window.BetaMath`) called directly via `page.evaluate` and checked against independently-computed reference values (posterior update, credible interval, P(θ>p0), Bayes factor reciprocity, Wilson CI, exact binomial p-value)
  - Scenario selection sets the correct `p0` and description; Custom scenario accepts free text and a custom `p0`
  - Belief-mode and Advanced-mode prior elicitation stay in sync and produce the expected α, β
  - Sequential `+ Success` / `+ Failure` / batch-add correctly update n, posterior mean, and the history table
  - Undo restores the immediately prior state; Reset restores the original prior with an empty history
  - Credible interval bounds always satisfy `0 ≤ lower < upper ≤ 1`
  - Invalid inputs (negative/non-numeric prior or batch counts) are rejected rather than corrupting state
  - AI narrative: no key present → deterministic template renders with zero network calls; key present → the request is intercepted/mocked (never a live API call) and the mocked response renders correctly
  - Script-injection payload in the Custom scenario description field is rendered inert (no `alert`/`pageerror`/execution)
  - Layout remains usable at a narrow (mobile) viewport width

## Success Criteria

1. All tests pass (zero failures)
2. All Beta-Binomial math (posterior update, credible interval, posterior tail probability, Savage-Dickey Bayes factor, Wilson CI, exact binomial test) matches independently-computed reference values within numerical tolerance
3. A user can pick a scenario, set a prior via either elicitation mode, add trials one at a time or in a batch, and see the posterior chart, credible interval, and Bayes factor update correctly and live, with Undo/Reset both working
4. The frequentist contrast panel and Bayesian panel are both visible simultaneously and clearly labeled with their differing interpretations
5. No live network call is ever made without an explicit user-supplied API key, and no custom or AI-generated text can execute as script

---

## Scope Changes

None — the full scope above was implemented as planned. The one deliberate simplification decided during PRD writing (method-of-moments prior elicitation instead of a numerical-optimization quantile-matching elicitation, and equal-tailed credible intervals instead of HDI) is recorded above in "Out of Scope" rather than as a mid-build cut.
