# PRD — Power Lab

## Goal
An interactive browser tool that teaches statistical power and sample-size planning through live visual simulation, doubles as a real quick-reference calculator for grant applications and study design, and includes a gamified quiz that builds intuition about how often psychology studies are underpowered.

## User Story
As a researcher who writes grants and designs studies (and teaches research methods to graduate students), I want to interactively explore how effect size, sample size, and alpha level trade off against statistical power — see the sampling distributions overlap, get a real sample-size number for a target power, convert between effect-size metrics reported in different papers, and test my own intuition about power — so that I have both a teaching tool for students and a fast sanity-check calculator I can actually use when planning a study or writing a power-analysis paragraph for a grant.

## Scope

### In
- **Power Explorer tab**: sliders/inputs for effect size (Cohen's d), sample size per group, alpha (.01/.05/.10), test type (two-sample independent, one-sample/paired), and tails (one/two-sided). Live-updating:
  - Overlapping distribution chart (H0 vs H1 sampling distributions, shaded rejection region)
  - Power curve chart (power vs N at the current effect size/alpha)
  - Numeric power readout with a qualitative label (severely underpowered / underpowered / adequate / well-powered)
- **Sample Size Calculator tab**: given a target power (e.g. 0.80), effect size, alpha, tails, and test type, compute the required N per group (closed-form inversion of the same power model), with a copy-to-clipboard summary sentence suitable for pasting into a grant methods section
- **Effect Size Converter tab**: convert Cohen's d ↔ Pearson's r, and t-statistic + sample size → Cohen's d, with the conventional small/medium/large benchmark shown for context
- **Power Intuition Quiz tab**: 18-question fixed bank of realistic study scenarios (effect size, n, description). User guesses the power bucket (<50% / 50–70% / 70–90% / >90%) before the tool reveals the calculated power; tracks score and streak; short insight line after each answer connecting the scenario to the replication-crisis "many published effects are underpowered" pattern. Score/streak persisted in `localStorage`.
- Dark/light theme toggle (dark by default), persisted in `localStorage`
- Mobile-responsive layout
- All computation is exact, deterministic client-side math — no network calls, no external data dependency

### Out
- Exact noncentral-t power calculation (uses a well-documented normal approximation instead — see Data Structure below for the accuracy note); listed in FutureFeatures.md
- ANOVA, chi-square, correlation, and other test-family power models beyond the t-test family
- Saving/exporting custom scenarios or PDF report generation
- User accounts or multi-device sync
- Any AI/LLM integration — this build has no dependency on `ANTHROPIC_API_KEY` (verified not present in this session's environment; the tool's value does not require it)

## Tech Stack
- Vanilla HTML/CSS/JS (ES modules), zero runtime dependencies — charts are hand-drawn with the native Canvas 2D API rather than a CDN charting library (see Scope Changes below)
- `@playwright/test` (devDependency, pinned via `package-lock.json`) for browser tests
- No build step — `index.html` opens directly or via a static file server

## Data Structure

### Core math (`src/stats.js`)
Pure functions, no state:
- `normalCDF(x)` — standard normal CDF via the Abramowitz–Stegun erf approximation (max error ≈1.5×10⁻⁷)
- `invNormalCDF(p)` — standard normal quantile function via Acklam's rational approximation
- `computePower({ d, n, alpha, testType, tails })` — `testType`: `"two-sample"` (factor √(n/2)) | `"one-sample"` (factor √n). Returns power in [0,1].
- `computeRequiredN({ d, power, alpha, testType, tails })` — closed-form inversion, returns `Math.ceil(n)`
- `dToR(d)`, `rToD(r)` — exact for equal group sizes: `r = d/√(d²+4)`, `d = 2r/√(1-r²)`
- `tToD({ t, n, testType })` — `d = t·√(1/n₁+1/n₂)`; for equal-n two-sample this reduces to `t·√(2/n)`, for one-sample `t/√n`

**Accuracy note (documented in-app and in Manual.md):** power/N values use a normal approximation to the noncentral-t distribution. This is accurate to within roughly 1–3 percentage points of exact values for n ≥ 20 per group — good enough for planning and teaching, not a substitute for exact software (G*Power, `pwr` in R) when a pre-registration document requires exact figures.

### Quiz bank (`src/quiz-data.js`)
Array of 18 objects: `{ id, description, d, n, testType, tails, insight }`. The correct power bucket is computed at runtime via `computePower` (not hardcoded), so the quiz and the explorer can never disagree.

### Persisted state (`localStorage`)
- `power-lab-quiz-state` — `{ score, streak, bestStreak, answeredIds: [] }`
- `power-lab-theme` — `"dark" | "light"`

## Folder Structure
```
builds/2026-07-04-power-lab/
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
│   ├── stats.js          ← core math, pure functions
│   ├── quiz-data.js       ← fixed 18-question bank
│   ├── charts.js          ← native Canvas 2D rendering (distribution overlap, power curve)
│   ├── quiz.js            ← quiz flow, scoring, localStorage
│   └── app.js             ← tab navigation, form wiring, theme toggle
└── tests/
    ├── stats-math.spec.js       ← unit tests of stats.js pure functions
    ├── power-explorer.spec.js   ← Power Explorer tab interaction
    ├── sample-size.spec.js      ← Sample Size Calculator tab
    ├── effect-size.spec.js      ← Effect Size Converter tab
    └── quiz.spec.js             ← Quiz flow, scoring, persistence
```

## Testing Strategy
- **`stats-math.spec.js`** (~13 tests): exposes `stats.js` functions to the page via a module `<script type="module">` shim and asserts numeric results with tolerance — `normalCDF` at known points (0 → 0.5, 1.96 → ~0.975), `invNormalCDF` round-trips `normalCDF`, `computePower` at the classic textbook scenario (d=0.5, n=64/group, α=.05 two-sided → power in [0.75, 0.85]), power increases monotonically with n and with d, `computeRequiredN` round-trips `computePower` (computed N achieves at least the target power), one-sample factor differs correctly from two-sample factor, `dToR`/`rToD` round-trip within tolerance, `tToD` matches hand-computed values, boundary handling (alpha out of (0,1), n≤0, d=0 → power≈alpha).
- **`power-explorer.spec.js`** (~7 tests): page loads with Power Explorer tab active by default, moving the effect-size slider changes the displayed power value, moving the N slider changes it, switching test type changes the computed power for the same inputs, both canvases (distribution chart, power curve chart) are present and non-empty, alpha selector changes the shaded critical region, qualitative power label updates correctly across low/medium/high power values.
- **`sample-size.spec.js`** (~5 tests): default calculation renders a required-N result, increasing target power increases required N, decreasing effect size increases required N, the copy-to-clipboard summary sentence contains the computed N and effect size, invalid input (power ≥ 1 or ≤ 0) shows a validation message instead of a bogus result.
- **`effect-size.spec.js`** (~5 tests): d→r conversion matches expected value at d=0.5, r→d is the inverse of d→r within tolerance, t→d conversion matches a hand-computed value, switching direction (d→r vs r→d vs t→d) updates the input labels correctly, out-of-range r (|r|≥1) shows a validation message.
- **`quiz.spec.js`** (~7 tests): first question renders on load, selecting a bucket reveals the correct/incorrect feedback and the exact computed power, correct answer increments score and streak, incorrect answer resets streak but not score, "next question" advances to a different question, score/streak persist after page reload (localStorage), reaching the end of the 18-question bank loops back without crashing.

Total: **≥ 37 tests**, run via `npx playwright test`.

## Success Criteria
1. A user can move any control on the Power Explorer tab and see the power readout, distribution chart, and power curve update immediately and correctly (verified by test + manual check).
2. The Sample Size Calculator produces a required-N value that, when fed back into the power formula, achieves at least the requested target power (verified by a round-trip test).
3. The Effect Size Converter's d↔r conversions are mathematically consistent in both directions (round-trip test within tolerance).
4. The Power Intuition Quiz computes its "correct answer" from the same `computePower` function used elsewhere (no hardcoded/duplicated power values), and score/streak persist across a page reload.
5. All ≥37 tests pass with zero failures; the app has no console errors on load or during normal interaction.

## Scope Changes
The original plan (written before any code) used Chart.js via CDN for both charts, consistent with several prior builds in this repo. Mid-build, the first full test run showed the CDN script either failing to load or hanging for many seconds under this session's sandboxed network policy, which left `Chart` undefined at runtime — `initExplorer()` threw on `new Chart(...)`, which aborted the rest of `app.js`'s init sequence and cascaded into unrelated tab failures (Sample Size, Effect Size, Quiz) that had nothing to do with charting. This exact failure mode is already documented in this repo's history (the 2026-07-03 WeatherSong build deliberately avoided a CDN synthesis library for the same reason). Fixed by replacing `charts.js` with hand-rolled native Canvas 2D rendering — same public API (`createDistributionChart`/`createPowerCurveChart` with an `update(params)` method), zero network dependency, and no behavior change visible to the user. See `BUILD_LOG.md` for the diagnosis trail.

## Idea Brief Traceability
No linked Idea Brief — tonight's category (E — Learning Aid) had an empty pending backlog pool, so this idea was freshly generated per Step 2d. See `WhyThis.md` for the three candidates considered and why this one was selected.
