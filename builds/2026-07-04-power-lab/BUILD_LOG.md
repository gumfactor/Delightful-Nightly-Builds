# Build Log — Power Lab

## [Step 0] Resume check
No incomplete build found. All local dated folders (2026-06-06 through 2026-06-18) end with "Build complete. Success criteria reviewed." Proceeding to a fresh build.

## [Step 1] Orient
Read `PROFILE.md`, `STANDARDS.md`, and the most current `builds/index.md` (synced from the most recent open PR branch, `claude/cool-sagan-fp5h9l`, 2026-07-03 — 8 builds ahead of what's on `main`). Also synced `builds/ideas.md` from the same branch before appending tonight's non-winning ideas.

## [Step 2] Decide
- Day of year 185 → category index 4 → **E — Learning Aid**.
- `builds/ideas.md` pending pool for category E: empty → skipped lottery, went to fresh idea generation (Step 2d).
- Checked environment for `ANTHROPIC_API_KEY`: **not present** in this session (only `ANTHROPIC_BASE_URL` and `GITHUB_TOKEN` are set), despite PROFILE.md/CLAUDE.md stating it's always available. This ruled out any idea depending on live AI calls as a core feature.
- Generated 3 candidates, selected **Power Lab** (interactive statistical power / sample-size / effect-size / power-intuition-quiz tool). Full reasoning in `WhyThis.md`. Appended the two runner-ups to `builds/ideas.md` as IDs 15–16.

## [Step 3-4] PRD
`PRD.md` written before any code. Scope: 4 tabs (Power Explorer, Sample Size Calculator, Effect Size Converter, Power Intuition Quiz), pure client-side math (normal-approximation power model), Chart.js visualizations, 18-question quiz bank, dark/light theme, localStorage for quiz state and theme only.

## [Step 5] Build
Wrote `stats.js` (core power/sample-size/effect-size math with a documented normal-approximation caveat), `quiz-data.js` (18-scenario bank), `charts.js`, `quiz.js`, `app.js`, `styles.css`, `index.html`, and all 5 test spec files. Initial version of `charts.js` used Chart.js via CDN (`chart.js@4.4.4`), matching prior builds in this repo.

**Mid-build pivot #1 (CDN dependency):** First full `npx playwright test` run produced widespread failures — most non-explorer tests timed out at the full 15s test timeout, and several explorer tests failed fast because moving sliders did nothing. Diagnosis: this session's sandboxed network policy does not reliably let the Chart.js CDN `<script>` tag load, so `Chart` was undefined at runtime; `new Chart(...)` inside `createDistributionChart()` threw during `initExplorer()`, which is called synchronously inside `app.js`'s `DOMContentLoaded` handler before `initSampleSize()`, `initEffectSizeConverter()`, and `initQuiz()` — the uncaught exception stopped the handler, so those three tabs never initialized at all. This is the same failure mode the 2026-07-03 WeatherSong build hit and deliberately avoided for its audio library. Fixed by rewriting `charts.js` to draw both charts with the native Canvas 2D API (no external library, same public `update()`-based interface, no changes needed to `app.js` or tests). Documented in `PRD.md`'s Scope Changes section.

**Mid-build pivot #2 (ES modules break under file://):** Second test run still failed almost everywhere, now with fast failures across every non-Explorer tab. Wrote a standalone Playwright debug script to capture console/page errors directly (not just test assertions) and found the real cause: Chromium refuses to load `<script type="module">` at all when a page is opened via a bare `file://` URL (`Access to script ... has been blocked by CORS policy ... origin 'null'`), so `app.js` and every module it imported (`stats.js`, `charts.js`, `quiz.js`) never ran — `window.PowerLabStats` was simply never defined. This is unrelated to the earlier CDN issue and would have broken the app for any real user double-clicking `index.html`, not just in this sandboxed test environment. Fixed by converting all five `src/*.js` files from ES modules to classic (non-module) `<script>` tags, each wrapped in an IIFE and attaching its API to a namespaced `window` global (`window.PowerLabStats`, `window.PowerLabQuizData`, `window.PowerLabCharts`, `window.PowerLabQuiz`), loaded in dependency order in `index.html`. The IIFE wrapper was necessary because top-level `let`/`const` in separate classic `<script>` tags on the same page share one global lexical scope — an unwrapped second attempt hit `Identifier 'computePower' has already been declared` from the naive destructuring imports.

**Two real bugs found once the infra issues were cleared (not further infra):**
- `computePower`'s two-sided formula only modeled the upper rejection tail, so `d=0` incorrectly returned `alpha/2` instead of `alpha`. Fixed by adding the symmetric lower-tail term (`normalCDF(ncp - zAlpha) + normalCDF(-ncp - zAlpha)` for two-tailed; single term unchanged for one-tailed). Negligible effect on all realistic d/n values already covered by other tests — verified the classic d=0.5, n=64 benchmark still lands at ~80.7% after the fix.
- `.control-row[hidden]` was invisible because `styles.css` already had a `.control-row { display: flex; ... }` rule of equal specificity to the browser's default `[hidden] { display: none }` UA rule — author CSS beats UA CSS regardless of specificity, so the row never actually hid. Fixed with an explicit `.control-row[hidden] { display: none; }` rule.

## [Step 6] Tests
`npx playwright test` — **39 passed, 0 failed** (all 5 spec files, ~9s runtime once the infra issues above were fixed).

## [Step 7] Verify
All 5 PRD success criteria checked manually (screenshots + interaction) and via the test suite:
1. Power Explorer controls update the readout and both charts live — confirmed by screenshot and `power-explorer.spec.js`.
2. Sample Size Calculator's required N, fed back into `computePower`, achieves at least the target power — confirmed by `stats-math.spec.js`'s round-trip test.
3. Effect Size Converter's d↔r round-trips within tolerance — confirmed by `effect-size.spec.js`.
4. Quiz's correct answer is always derived from `computePower` at runtime (never hardcoded), and score/streak persist across reload — confirmed by `quiz.js` source (no duplicated power values) and `quiz.spec.js`'s reload test.
5. All 39 tests pass; manual screenshot pass of both the Explorer and Quiz tabs opened directly via a `file://` URL showed no console errors and correct rendering.

STANDARDS.md security checklist: no hardcoded credentials/secrets, no `eval`/`exec`, no `innerHTML` from user-controlled input (`.innerHTML` assignments in `app.js` only ever insert app-computed numbers, never raw user text), no shell calls, no path traversal, nothing read outside this build folder. No AI dependency (`ANTHROPIC_API_KEY` absent, and by design not needed). No network calls at runtime at all — confirmed no CDN or fetch/XHR usage remains anywhere in `src/`.

## [Step 8] Documentation
`Manual.md` written (open-directly instructions, accuracy caveat, design-decision notes). `FutureFeatures.md` written with 7 concrete extensions.

Build complete. Success criteria reviewed. All tests passing.
