# PRD — Signal Detection Lab

> **Build date:** 2026-07-31
> **Category:** E — Learning Aid
> **Complexity:** Ambitious Project
> **Day of week:** Friday → category rotation, not day-of-week complexity — ambitious target set to match the three prior Category E builds (Power Lab, CircuitLab, Bayes Lab)

---

## Goal

An interactive browser trainer that teaches Signal Detection Theory (d', criterion, ROC/AUC) through a live-manipulable dual-Gaussian visualization, an ROC explorer, a publication-ready calculator, and a scenario quiz grounded in forensic/affective-neuroscience research paradigms.

## User Story

As a forensic/affective neuroscience researcher and lab instructor who teaches Social Affective Neuroscience and supervises studies using recognition-memory, threat-detection, and eyewitness-identification paradigms, I want an interactive tool that both computes correct SDT statistics from raw hit/false-alarm data and builds intuition for what sensitivity and bias mean, so that I can use it for my own study analysis and drop it directly into a course session without extra prep.

## Scope

### In Scope
- **Explainer tab**: 2×2 outcome matrix (hit/miss/false-alarm/correct-rejection) with definitions; a Canvas 2D dual-Gaussian plot (noise distribution vs. signal distribution under the equal-variance Gaussian SDT model) with a draggable criterion line; live-updating d', criterion c, likelihood-ratio β, hit rate, and false-alarm rate as the criterion is dragged or the distribution separation (d') is changed via a slider.
- **ROC Explorer tab**: Canvas-drawn ROC curve traced from the current d' by sweeping the criterion across its full range, a chance diagonal, closed-form AUC = Φ(d'/√2), and a marker showing where the Explainer tab's current criterion sits on the curve.
- **Calculator tab**: manual entry of hits/misses/false-alarms/correct-rejections (or direct hit-rate/false-alarm-rate percentages); computes d', criterion c, likelihood-ratio β, the nonparametric A' and B'' (distribution-free sensitivity/bias alternatives), with an explicit loglinear-correction toggle for handling 0%/100% edge rates (Hautus, 1995 method: add 0.5 to counts, add 1 to N).
- **Scenario Quiz tab**: 6 hand-authored scenarios grounded in forensic/affective-neuroscience research paradigms (recognition memory in psychopathy research, threat/fear-face detection, eyewitness lineup identification, a diagnostic screening tool, deception/lie judgment, radiological tumor detection) with plausible hit/miss/false-alarm/correct-rejection counts; the learner picks a d' bucket (poor / weak / moderate / good / excellent) and a bias direction (liberal / neutral / conservative), and the correct answer is always derived live from the same math functions used elsewhere in the tool — never hardcoded. Score (attempts/correct, per-scenario and overall) persists in `localStorage` across sessions.
- Optional AI-generated practice scenario: user types a short research context (e.g., "eyewitness identification under stress"); if a session-only Anthropic API key is supplied, Claude Haiku generates a new scenario description with plausible counts; with no key, a deterministic template generator produces a scenario from the same context string using randomized-but-plausible counts (seeded from the string so it's reproducible within a session, not `Math.random()`-only).
- Colorblind-safe, dark-mode UI; mobile-responsive layout (single-column stacking below 700px).

### Out of Scope
- Unequal-variance ("uneven") Gaussian SDT models — the tool uses the standard equal-variance model only; noted as a future extension.
- Multi-response-category (rating-scale) ROC analysis — only single-criterion, binary-response ROC is covered.
- Server-side persistence or multi-user accounts — `localStorage` only, single browser/session scoped.
- CSV/batch import of many scenarios at once — the calculator handles one set of counts at a time.

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic `<script>` tags, no ES modules — opens directly via `file://`)
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev-only, for tests)
- **Runtime requirement:** Open `index.html` directly in any modern browser; no build step, no server, no install needed to use the tool (only `npm install` is needed to run the test suite)

## Data Structure

Stateless core: `src/sdt-math.js` exports pure functions (no DOM access) operating on plain numbers — hit/false-alarm rates or raw counts in, sensitivity/bias/ROC numbers out. No file I/O.

Scenario bank (`src/scenarios.js`): a static array of objects —
```js
{ id, title, domain, description, hits, misses, falseAlarms, correctRejections }
```

`localStorage` schema (key `sdtLabQuizState`):
```json
{
  "overall": { "attempts": 0, "correct": 0 },
  "byScenario": {
    "<scenarioId>": { "attempts": 0, "correct": 0 }
  }
}
```
No personal data, no API keys, ever written to `localStorage`. The Anthropic API key (when supplied) lives only in a page-lifetime JS variable.

## Folder Structure

```
builds/2026-07-31-signal-detection-lab/
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
│   ├── sdt-math.js       (pure SDT math: normal CDF/quantile, d', c, β, A', B'', ROC, AUC)
│   ├── scenarios.js      (6 hand-authored research scenarios)
│   ├── ai-scenario.js    (optional Claude Haiku scenario generation + deterministic fallback)
│   ├── app.js            (UI wiring, tab switching, Canvas rendering, quiz logic, localStorage)
│   └── styles.css
└── tests/
    └── signal-detection-lab.spec.js
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/signal-detection-lab.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Core math correctness against independently-computable reference values: `normalQuantile` at known percentiles (0.5 → 0, 0.975 → ≈1.95996), `dPrime`/`criterion` from a textbook hit/FA-rate pair, `rocAuc(d')` closed form matching a trapezoidal numeric integration of `rocCurve` for several d' values (self-consistency cross-check), `aPrime`/`bDoublePrime` symmetry property at the unbiased point (H = 1 − FA → B'' = 0)
  - Loglinear correction behavior at the 0%/100% edge (0 false alarms out of N does not produce an infinite d')
  - Explainer tab: dragging the criterion updates displayed d'/c/hit-rate/FA-rate; changing the d' slider updates the ROC tab's curve
  - ROC Explorer tab: AUC display matches `rocAuc` for the current d'; curve passes through (0,0) and (1,1)
  - Calculator tab: entering counts produces correct d'/c and correctly toggles between corrected/raw modes
  - Scenario Quiz: correct/incorrect answers are scored against live-derived buckets (not hardcoded), `localStorage` persists attempts/correct across a reload
  - AI scenario generation: with a mocked successful Anthropic response, the returned scenario text is used and rendered as inert text; with a mocked failed/errored response, the deterministic fallback engages with zero thrown errors; with no key entered, zero network requests are made
  - Security: a `<script>` payload typed into the AI-context field and a `<img onerror>` payload placed into a scenario title both render as inert text, not executed (XSS safety)
  - Mobile viewport: layout does not overflow horizontally at 375px width

## Success Criteria

1. All tests pass (zero failures)
2. All four tabs (Explainer, ROC Explorer, Calculator, Scenario Quiz) are reachable and functionally correct, verified live in headless Chromium
3. Every number the tool displays (d', c, β, A', B'', AUC, quiz answers) is computed live from `sdt-math.js` — no hardcoded lookup tables for anything a formula can produce
4. The deterministic-fallback path works with zero Anthropic API calls when no key is supplied; the AI path makes exactly one request when a key is supplied, confirmed against a mocked endpoint
5. Quiz score correctly persists across a page reload via `localStorage`

---

## Scope Changes

None. The full scope defined above shipped as planned. One test-setup bug was found and fixed during the build (an `addInitScript`-based `localStorage` clear was re-firing on an in-test `page.reload()`) — this was a test authoring issue, not a scope or app-behavior change; see `BUILD_LOG.md`.
