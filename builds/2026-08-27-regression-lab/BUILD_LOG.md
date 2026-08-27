# Build Log — Regression Lab

> **Date:** 2026-08-27
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Checked `builds/` for an interrupted prior session: none found — the most recent local folder (2026-06-18-regex-dojo) has a completed `BUILD_LOG.md`.
- Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-1vk118`, PR #81, 2026-08-25 Grant Vault) per Step 1, since `main` is weeks behind.
- Read PROFILE.md, the full `builds/index.md` catalog (108 rows), and STANDARDS.md.
- Day of year 239 → `category_index = (239-1) % 9 = 4` → Category E — Learning Aid.
- Category E backlog held 2 pending, unrated ideas. `lottery_chance = 25%`, rolled 13 → draw. Weighted draw (both 5 tickets) rolled 2/10 → idea #18, "GLM & Regression Diagnostics Trainer," won.
- Marked idea #18 `built` in `builds/ideas.md`.
- Build folder created: `builds/2026-08-27-regression-lab/`.

### [00:15 UTC] PRD Written

- Goal: interactive drag-a-point OLS regression trainer with real diagnostic plots and tests.
- Scope: Scatterplot & Fit tab, Diagnostics tab (residual/QQ/leverage plots, Breusch-Pagan, RESET-style test, Cook's Distance), Multicollinearity Lab (VIF/SE demonstration), Quiz tab, optional direct-browser Claude Haiku explanation layer.
- Notable decision: build one general multiple-regression engine (OLS via Gauss-Jordan matrix inversion) and derive simple regression, the quadratic RESET test, and the 2-predictor multicollinearity demo from the same function, rather than three separate implementations.

### [00:20 UTC] Math Engine Built and Cross-Checked

- Wrote `src/math.js`: matrix algebra (transpose, matMul, Gauss-Jordan inverse with partial pivoting), Lanczos log-gamma, regularized incomplete beta (continued-fraction `betacf`), Student's t CDF/p-value, Acklam's normal-quantile algorithm, the general `multipleRegression` engine (coefficients, SE, t-stats, p-values, hat values, standardized residuals, Cook's Distance), `resetTest`, `breuschPaganTest`, `vifPair`, and a seeded `mulberry32` PRNG for deterministic synthetic data.
- Verified numerically via a scratch Node script before building anything on top of it: t two-tailed p at t=2.228/df=10 and t=2.042/df=30 both landed at 0.0500 (textbook critical values); t-distribution at df=1 reduced exactly to the Cauchy distribution (p=0.5 at t=1, matching the closed-form Cauchy CDF); `normalQuantile(0.975)` matched 1.959964 to 6 decimals; a hand-worked textbook simple-regression example (x=1..5, y=[2,4,5,4,5]) reproduced b0=2.2, b1=0.6, R²=0.6 exactly; hat values summed to p=2 as required.

### [00:35 UTC] Preset Datasets Tuned

- Wrote `src/datasets.js` with 4 deterministic seeded-PRNG-generated presets (Well-Behaved, Heteroscedastic, Non-Linear, Outlier/High Leverage) plus a `buildMulticollinearData(corr, n)` generator.
- Iteratively tuned noise scale/seed via scratch scripts until each preset reliably triggered its intended diagnostic: Heteroscedastic → Breusch-Pagan p=0.0158 (significant); Non-Linear → RESET p≈0.0000 (significant); Outlier → a single point's Cook's Distance 40x its nearest rival (8.17 vs. 0.204); Well-Behaved → neither test significant (p=0.18, p=0.71).
- Real finding during tuning: the 4/n Cook's-Distance rule-of-thumb is aggressive enough that even genuinely well-behaved synthetic data can cross it by a small margin (0.335 vs. 0.25 threshold, a 1.3x overage) purely by chance on the single most-extreme-x point. Rather than keep re-seeding to force a flag-free "clean" preset (which would misrepresent how the threshold behaves on real data), the app surfaces the actual magnitude — not just a boolean — so a mild 1.3x overage on Well-Behaved reads very differently from the Outlier preset's 40x dominance ratio. The quiz's `diagnoseDataset` classifier uses that dominance ratio (top Cook's D vs. second-highest), not the raw threshold crossing, specifically so this edge case doesn't misclassify Well-Behaved as an outlier scenario.
- Verified the multicollinearity generator against the textbook prediction: as target correlation rose from 0 → 0.99, VIF grew 1.00 → 32.18 and SE(b1)/SE(b2) grew roughly 5-6x, while joint R² stayed essentially flat (0.795 → 0.853).

### [00:50 UTC] UI Built

- `index.html` / `src/style.css`: 4-tab dark-mode layout (Scatterplot & Fit, Diagnostics, Multicollinearity Lab, Quiz), mobile-responsive grid that collapses to a single column under 900px.
- `src/app.js`: canvas coordinate transforms (data↔pixel, auto-scaled bounds with padding), drag/add/remove point interactions (drag works on any point in any preset; click-to-add is Custom-mode-only; double-click removes in any mode), live-updating fit stats, three diagnostic plots (residual-vs-fitted, Q-Q, leverage-vs-Cook's-D with threshold line), the Multicollinearity Lab slider wiring, and the full quiz flow.
- `src/quiz.js`: reuses the same `math.js` tests to compute each diagnose-question's correct answer live at session-build time — verified the dominance-ratio classifier correctly labels all 4 presets (well-behaved, heteroscedastic, non-linear, outlier) with zero misclassification.
- `src/ai.js`: direct-browser Claude Haiku call with a session-only key, unconditional deterministic-template fallback built from the same computed numbers shown elsewhere in the UI.
- Manual smoke-testing in headless Chromium (global npm Playwright 1.62.1, installed via `npm install` in this build folder — `@playwright/test` was not pre-installed globally, unlike the `playwright` CLI package) caught one real bug before the formal test suite was written: dragging a point immediately after adding several points via click could silently add a duplicate point instead of moving the intended one, because reused stale screen coordinates no longer matched the just-recomputed auto-scaled bounds. This was a test-methodology issue, not an app bug — confirmed by recomputing the drag's target pixel from the live `__testHooks` transform functions, after which the drag worked correctly. All Playwright drag tests use this live-transform approach rather than fixed screen coordinates.

### [01:05 UTC] Tests Written and Run

- 52 tests across 7 files: `math.spec.js` (16, pure Node-level correctness against hand-worked/textbook values), `datasets-quiz.spec.js` (12, preset diagnosis + quiz-session determinism), `ui.spec.js` (9, drag/add/remove/tab interactions), `diagnostics.spec.js` (6), `multicollinearity.spec.js` (2), `quiz-ui.spec.js` (5), `security.spec.js` (3, XSS payload safety, API key never in DOM, zero network calls with no key).
- First run: 51/52 passed. The one failure was a test assertion checking for the literal word "heteroscedasticity" in the verdict banner text, which actually reads "isn't constant" — a test wording mismatch, not an app defect. Fixed the assertion; re-ran.

Tests: 52 passed, 0 failed.

### [01:10 UTC] Verify

- Manual QA pass in headless Chromium: 375px mobile viewport shows zero horizontal overflow (`scrollWidth === clientWidth`) across the Scatterplot & Fit and Diagnostics tabs; desktop (1280x900) screenshot of the Diagnostics tab against the Outlier preset confirms all 3 diagnostic charts render correctly and the verdict banner, test numbers, and influential-point callout all match the computed values.
- Security checklist: no `.env` files, no hardcoded credentials, no `eval()`/`exec()`, only one `innerHTML` usage in the entire codebase (`optionsEl.innerHTML = ''` — clearing to empty string, not inserting content), no `os.system`/subprocess calls, no file-path handling of any kind. A mocked malicious Anthropic API response (`</script><script>...` + an `<img onerror>` payload) rendered as inert visible text with zero script execution, zero dialogs, and exactly the 5 `<script>` tags this build itself authors.
- All 5 PRD success criteria reviewed and met (see below).

### [01:15 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions.
- `Manual.md`: usage guide covering all 4 tabs, configuration, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
