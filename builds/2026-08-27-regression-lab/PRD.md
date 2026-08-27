# PRD — Regression Lab

> **Build date:** 2026-08-27
> **Category:** E — Learning Aid
> **Complexity:** Ambitious Project
> **Day of week:** Thursday

---

## Goal

An interactive browser trainer where dragging points on a scatterplot updates a live OLS regression fit, and a companion Diagnostics tab teaches how to read residual/Q-Q/leverage plots and the real statistical tests (Breusch-Pagan, a RESET-style linearity test, Cook's Distance, VIF) that reveal when the classic linear-regression assumptions break.

## User Story

As a psychology/neuroscience researcher and instructor who teaches statistics and wants to strengthen their own quantitative footing, I want to drag data points and immediately see how the fitted line, R², and the standard diagnostic plots respond, so that I build intuition for heteroscedasticity, non-linearity, influential outliers, and multicollinearity that no static textbook figure gives me.

## Scope

### In Scope
- Scatterplot & Fit tab: draggable/addable/removable points, live OLS coefficients (b0, b1, R², adjusted R², SE(b1), t-stat, p-value), 5 preset datasets (Well-Behaved, Heteroscedastic, Non-Linear, Outlier/High Leverage, Custom free-draw)
- Diagnostics tab: Residuals-vs-Fitted plot, Normal Q-Q plot of standardized residuals, Leverage-vs-Cook's-Distance plot (with the 4/n rule-of-thumb threshold line), a Breusch-Pagan heteroscedasticity test, a RESET-style quadratic-term linearity test, residual skewness/excess kurtosis, and a single computed verdict banner
- Multicollinearity Lab tab: a correlation slider between two predictors X1/X2 driving a live VIF, joint-model R², and both coefficients' standard errors, demonstrating that R² stays flat while SE inflates as correlation rises
- Quiz tab: 12 questions per session (4 "diagnose this real dataset" questions with a live-computed correct answer, 8 fixed conceptual questions), scored, with a persisted best score
- Optional direct-browser Claude Haiku explanation of the current diagnostic result, with an unconditional deterministic-template fallback
- All regression math (OLS via Gauss-Jordan matrix inversion, t-distribution CDF via regularized incomplete beta, normal quantile via Acklam's algorithm, Cook's Distance, VIF) implemented from scratch in `src/math.js`

### Out of Scope
- Multiple regression beyond 2 predictors in the interactive UI (the underlying engine supports it; the UI does not expose more than 2)
- Real/live external datasets — every dataset is synthetic and deterministically generated (this build needs no external data source; the trainer's value is the interactive mechanic, not live data)
- Formal normality test (Shapiro-Wilk) — skewness/excess kurtosis are used instead and labeled as a heuristic, not a formal test
- Saving/exporting custom datasets between sessions

## Tech Stack

- **Language:** HTML/CSS/JavaScript (vanilla, classic scripts — no ES modules, no bundler)
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev-only, for tests); zero runtime dependencies — no CDN libraries
- **Runtime requirement:** Opens directly in any browser via `file://index.html`, no install or server needed

## Data Structure

All data is synthetic, generated in-browser from a deterministic seeded PRNG (`mulberry32`, see `src/math.js`). No external files, no network calls at runtime except the optional direct Anthropic API call. In-memory state:
```js
points = [{ x: Number, y: Number }, ...]   // current scatterplot dataset
```
`src/datasets.js` exports 4 fixed presets (each an array of `{x, y}` pairs) plus a `buildMulticollinearData(corr, n)` generator for the Multicollinearity Lab. Nothing is persisted to disk; `localStorage` holds only the quiz best-score record (`regressionLabQuizBest`).

## Folder Structure

```
builds/2026-08-27-regression-lab/
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
│   ├── math.js        (OLS regression engine, special functions, seeded PRNG)
│   ├── datasets.js     (deterministic preset datasets + multicollinearity generator)
│   ├── quiz.js          (quiz question bank + live diagnosis-based grading)
│   ├── ai.js             (optional direct-browser Claude Haiku call + deterministic fallback)
│   ├── app.js             (UI controller: canvas rendering, drag interaction, tabs)
│   └── style.css
└── tests/
    ├── math.spec.js
    ├── datasets-quiz.spec.js
    ├── ui.spec.js
    ├── diagnostics.spec.js
    ├── multicollinearity.spec.js
    ├── quiz-ui.spec.js
    └── security.spec.js
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Regression math correctness against hand-worked/textbook values (coefficients, R², t-distribution p-values, normal quantiles, hat-value sum, Cook's Distance, VIF, Breusch-Pagan/RESET tests)
  - Each preset dataset reliably triggers its intended diagnosis via the live `diagnoseDataset` function (not a hardcoded label)
  - Quiz session determinism (same seed → same question order) and correctness of the live-computed answer key
  - Browser interactions: preset switching, click-to-add, drag-to-move, double-click-to-remove, tab navigation, multicollinearity slider
  - Error/edge cases: fewer than 3 points (no crash, helpful message), underdetermined/singular regression inputs (throws cleanly)
  - Security: malicious AI-response payload renders as inert text with zero script execution, API key never leaks into the DOM, zero network requests occur with no API key set

## Success Criteria

1. All tests pass (zero failures) — minimum 15, actual: 52
2. Dragging a point on the Scatterplot & Fit tab updates the fitted line, R², and all displayed coefficients in real time with no page reload
3. Each of the 4 fixed presets (Well-Behaved, Heteroscedastic, Non-Linear, Outlier) is correctly diagnosed by the live statistical tests — verified both in Node-level unit tests and live in the browser
4. The Multicollinearity Lab demonstrably shows VIF and both coefficients' standard errors growing sharply as the correlation slider increases, while joint R² stays roughly flat — the core textbook lesson about what multicollinearity does and doesn't break
5. The app is fully functional with zero network access and no Anthropic API key (verified: zero external requests logged during a full interaction pass)

---

## Scope Changes

None. The build shipped everything scoped above; no features were cut mid-build.
