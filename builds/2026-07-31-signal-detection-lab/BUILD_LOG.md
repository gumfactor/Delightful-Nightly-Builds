# Build Log — Signal Detection Lab

> **Date:** 2026-07-31
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [Session Start]

- Checked `builds/` for an incomplete prior session (Step 0): no unfinished build found. Most recent dated folder locally was `2026-06-18-regex-dojo`, already complete. Local `main` is far behind actual build history (46 completed builds sit in unmerged open PRs, #26–#56); pulled the current `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-xza82t`, PR #56, 2026-07-30 Vizstract) per Step 1, and confirmed that PR's `BUILD_LOG.md` ends with the required completion line — nothing to resume.
- Read `PROFILE.md`, the resynced `builds/index.md` (49 total builds, 46 complete / 0 partial / 0 aborted / 3 discarded), and `STANDARDS.md`.
- Day of year: 212. `(212-1) % 9 = 4` → Category **E — Learning Aid**.
- `builds/ideas.md` (resynced from the same branch) had zero pending Category E rows → skipped the lottery, went straight to fresh-idea generation.
- Topic diversity check on the last 10 builds (2026-07-20 through 2026-07-30): no single domain repeated more than twice; research/academia-adjacent topics appear several times but with genuinely different mechanics each time (ownership lookup, analogy generation, Bayesian stats, bias vignettes, bug mining, trip planning, sector investing, prose auditing, citation tracking, visual abstracts).
- Decided to build: **Signal Detection Lab** — an interactive SDT trainer (d', criterion, ROC/AUC) grounded in forensic/affective-neuroscience research paradigms. Full reasoning, two considered-and-passed-over alternatives, and connection to PROFILE.md in `WhyThis.md`.
- Build folder created: `builds/2026-07-31-signal-detection-lab/` (renamed from an initial `builds/2026-07-31/` to match the `YYYY-MM-DD-title-slug` convention required by `STANDARDS.md` and CLAUDE.md Step 3, which the scheduled-task prompt's shorthand `builds/YYYY-MM-DD/` omitted).
- Reviewed `builds/2026-07-22-bayes-lab/` on `origin/claude/cool-sagan-psb5dt` as a structural reference (pure-math module pattern, Playwright config, Anthropic direct-browser-call pattern) — no code copied, only conventions.

### [PRD Written]

- Goal: interactive SDT trainer with 4 tabs (Explainer, ROC Explorer, Calculator, Scenario Quiz).
- Scope locked: equal-variance Gaussian SDT model only (unequal-variance and rating-scale ROC explicitly out of scope tonight); 6 hand-authored scenarios; optional AI scenario generation with deterministic fallback; `localStorage`-only quiz score persistence (appropriate here per PROFILE.md's Data Sources guidance — this is a learning aid with no external live data source, not a productivity tool masking manual entry).
- Notable decision: all math implemented as pure functions in `src/sdt-math.js`, independent of the DOM, so both the UI and the test suite call the exact same code — no duplicated formulas to drift out of sync.

### [Build Phase — Math Core]

Implemented `src/sdt-math.js`: `erf`/`normalCdf` (Abramowitz & Stegun 7.1.26, ~1.5e-7 max error), `normalQuantile` (Acklam's rational approximation + one Halley refinement step), `ratesFromCounts` (loglinear correction per Hautus, 1995 — adds 0.5 to hits/misses/FA/CR and 1 to each N, avoiding infinite z-scores at 0%/100%), `dPrime`, `criterionC`, `likelihoodRatioBeta`, `aPrime`/`bDoublePrime` (Pollack & Norman / Donaldson nonparametric measures), `rocCurve` (criterion sweep from -4 to 4), `rocAuc` (closed form Φ(d'/√2)), and `dPrimeBucket`/`criterionLabel` classification helpers. Cross-checked `normalQuantile(0.975)` against the well-known reference value 1.959964 by hand before writing tests.

### [Build Phase — Scenarios + AI]

Wrote `src/scenarios.js` with 6 scenarios spanning the d' range (near-chance deception judgment through excellent diagnostic screening) and bias direction (liberal threat-detection example, conservative recognition-memory example, near-neutral radiology example), each grounded in a named forensic/affective-neuroscience paradigm. Wrote `src/ai-scenario.js` following the direct-browser-call-to-Anthropic pattern established in prior builds (session-only key, `anthropic-dangerous-direct-browser-access` header, Haiku model), with a deterministic string-seeded fallback generator so the "no API key" path is fully functional and reproducible within a session.

### [Build Phase — UI]

Built `index.html`/`src/styles.css`/`src/app.js`: 4-tab layout, Canvas 2D dual-Gaussian plot with a mouse-draggable criterion line, Canvas 2D ROC curve, calculator form with a correction-mode toggle, and the scenario quiz with `localStorage`-backed scoring. All dynamic text inserted via `textContent`/`createElement`, never `innerHTML`, per the security checklist.

### [Tests Run]

First run: 31 passed, 1 failed — `Quiz: score persists in localStorage across a page reload` failed because the test's `page.addInitScript(() => window.localStorage.clear())` re-fires on every navigation, including the in-test `page.reload()`, wiping the just-saved score immediately before the assertion. This was a test-setup bug, not an app bug: the app's `localStorage` read/write logic was already correct (confirmed by inspecting `loadQuizState`/`saveQuizState` in `src/app.js`). Fixed by clearing storage once via `page.evaluate` + an explicit `page.reload()` in `beforeEach`, rather than an init script that reapplies on every navigation.

Tests: 32 passed, 0 failed. (`npx playwright test`)

### [Manual Visual QA]

Took live screenshots of all 4 tabs in headless Chromium (Explainer, ROC Explorer, Calculator with default counts computed, Scenario Quiz) plus a zero-console-errors check across tab navigation. Cross-checked the Explainer tab's displayed numbers by hand: at the default d′ = 1.5, criterion = 0, hit rate = 93.3% and FA rate = 50.0% (both matching `1 - normalCdf(criterion - dPrime)` / `1 - normalCdf(criterion)`), giving c = -0.75 (liberal) — matches the on-screen "BIAS: liberal" label. ROC tab's AUC (0.856) matches `normalCdf(1.5/√2)`. Ran the STANDARDS.md security checklist via grep: zero matches for `eval(`/`exec(`, zero `innerHTML` usage anywhere in `src/`, `index.html`, or `tests/`, zero hardcoded credential-shaped strings, zero `.env` files, and the only `subprocess`/`os.system` hits are inside `node_modules/playwright-core` (third-party, gitignored, not build code).

### [Verification]

Checked all 5 PRD success criteria — all met (see final BUILD_LOG entry below for detail). No scope changes were needed; the full PRD scope shipped as planned.

Build complete. Success criteria reviewed. All tests passing.
