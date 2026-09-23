# Build Log — Pooling Lab

> **Date:** 2026-09-23
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: local `builds/` only contains old complete folders (2026-06-06 through 2026-06-18); most recent local dated folder (2026-06-18-regex-dojo) is confirmed complete via its BUILD_LOG. Checked GitHub directly: the true most recent nightly session is PR #106 (2026-09-22, "Wake Log"), whose `BUILD_LOG.md` ends with the required "Build complete. Success criteria reviewed. All tests passing." line — no interrupted build to resume.
- Noted for the record (not part of tonight's build, but material): PRs #3 through #106 (2026-06-11 through 2026-09-22, ~100 nightly builds) are open on GitHub and unmerged into `main`; `main` itself only carries the first handful of builds. `builds/index.md` on `main` is therefore ~75 builds behind the true catalog. Per CLAUDE.md Step 1, resynced orientation from the most recent open PR branch (`claude/cool-sagan-j1h4o4`) instead of `main`.
- Day of year for 2026-09-23 is 266 → `category_index = (266-1) % 9 = 4` → **Category E — Learning Aid**.
- Backlog (from the resynced `builds/ideas.md`) had 4 pending Category E rows, all unrated → `R=0` → lottery chance 25%. Rolled 29 → miss → fresh generation.
- Fresh-generation candidate pool: backlog rows #19 (Attention Mechanism Visualizer), #44 (Meta-Analysis/Forest Plot Trainer), #59 (Multilevel/Mixed-Effects Modeling Lab), #60 (Psychometrics/IRT Lab). Chose #59 — see `WhyThis.md` for full reasoning.
- Decided to build: **Pooling Lab** — an interactive nested-data / partial-pooling (shrinkage) simulator and trainer.
- Build folder created: `builds/2026-09-23-pooling-lab/`.
- Checked title/slug for collisions against the full catalog — none found.

### [00:20 UTC] PRD Written

- Goal: live, slider-driven simulator contrasting no-pooling / partial-pooling / complete-pooling estimates and true vs. empirical ICC as between-group variance and group sample sizes change.
- Stack: vanilla HTML/CSS/JS (classic scripts, no bundler, `file://`-openable), Canvas 2D chart, Playwright tests — matching the established pattern for this category (ERP Lab, Regression Lab).
- Notable decisions: kept the statistical core (`src/stats.js`) as pure, DOM-free functions so Playwright can unit-test the math directly via `addScriptTag`, independent of UI wiring. Added an optional "Explain This" panel using the Anthropic API (direct browser call, session-only key, `textContent`-only rendering) as the AI-integration differentiating layer, following the exact safety pattern ERP Lab already validated (mocked hostile-payload test).

### [00:25 UTC] Build Phase — stats engine

- Wrote `src/stats.js`: seeded mulberry32 PRNG + Box-Muller Gaussian sampler (so a given seed always reproduces the identical dataset), `generateNestedData`, `computeGrandMean` (size-weighted, not a naive average of group means), `computeTrueICC`, `computeEmpiricalICC` (one-way ANOVA variance-decomposition estimator, `null` on <2 usable groups instead of NaN), `computeShrinkageWeight`, and `computePoolingSummary`.
- Sanity-checked the math by hand in a throwaway Node script before wiring any UI: `trueICC(4,9)` matched the hand-computed fraction exactly; a 50-group × 200-obs simulation's empirical ICC (0.313) tracked the true ICC (0.308) closely; the tau2=0 / sigma2=0 collapse behaviors were exact to floating-point tolerance; a single-group dataset returned `null` rather than crashing or NaN-ing.

### [00:45 UTC] Build Phase — rendering, quiz, AI-explain, and app wiring

- `src/render.js`: native Canvas 2D chart, one column per group, dashed complete-pooling reference line, hollow no-pooling marker connected to a filled partial-pooling marker. Resolves the page's actual computed text color so the chart respects light/dark mode without hardcoding either palette.
- `src/quiz.js`: 5 fixed conceptual questions (shrinkage limits, ICC interpretation, random intercepts vs. fixed effects) + 3 questions generated from whatever `computePoolingSummary` output is live right now (smallest group, least-shrunk group, empirical-vs-true ICC direction). Kept as pure functions (`buildQuestionBank`, `checkAnswer`) so they're directly unit-testable.
- `src/explain.js`: optional Anthropic API panel following the exact pattern already validated in ERP Lab (2026-09-14) — direct browser `fetch` to `api.anthropic.com`, `claude-haiku-4-5-20251001`, only fires with a user-supplied key, always renders via `textContent`, always has a deterministic non-AI fallback built from the same numbers.
- `src/app.js`: wires sliders/buttons together. Deliberate design decision — the τ/σ sliders recompute `computePoolingSummary` against the *already-generated* sample's groups with the slider values substituted for `tau2`/`sigma2`, rather than redrawing new random data on every slider tick. This is what makes "drag the slider, watch it update live with no reload" (PRD success criterion 2) possible without the chart visually "jumping" to a brand-new random sample on every tick; "Regenerate Data" is the action that actually draws a fresh sample, using the current slider values as the new generating truth. Documented this behavior explicitly in `Manual.md` and as a known limitation in `FutureFeatures.md` since it means the τ/σ sliders can temporarily disagree with what actually generated the visible sample until Regenerate is clicked.
- Changed the default sample-size profile from "equal" to "one small group (n=3) among large (n=30)" after eyeballing a screenshot of the equal-sizes default: with equal group sizes every shrinkage weight is identical, so the very first thing the user sees would not demonstrate the build's core teaching point. The uneven-sizes default makes the differential shrinkage (weight 0.57 for n=3 vs. 0.93 for n=30 in the seed-42 sample) visible immediately without any interaction.
- Verified visually via a real headless Chromium screenshot (not just Playwright's DOM assertions): zero console/page errors, chart renders with the expected marker layout, quiz renders all 8 questions, dark/light CSS variables are wired correctly.

### [01:05 UTC] Tests Written and Run

- `tests/stats.spec.js` (14 tests): ICC formula edge cases, seeded-RNG determinism and non-collision across seeds, exact group-size honoring, size-weighted grand mean, tau2=0/sigma2=0 collapse behavior, partial-pooling-always-between-the-two-endpoints property test, shrinkage-weight monotonicity in sample size, large-sample empirical-ICC recovery within tolerance, single-group graceful `null` handling, and a malformed-input error case.
- `tests/ui.spec.js` (14 tests): initial load with zero console/page errors, live tau-slider updates (including the tau=0 edge case), regenerate producing a new sample, profile switching, the small-vs-large shrinkage-weight comparison rendered in the actual table, quiz correct/incorrect feedback and score updates, quiz-choice disabling after answering, the AI-explain panel making zero network calls with no key, the AI-explain panel rendering a mocked hostile (`onerror`) payload as inert `textContent` with zero script execution, and a 375px mobile-viewport overflow check.
- Ran `npx playwright test`.

Tests: 28 passed, 0 failed.

### [01:15 UTC] Verification — Step 7

Checked every PRD success criterion against the running build:
1. All tests pass (28/28, zero failures) — confirmed above.
2. Dragging the τ slider live-updates the chart and both ICC readouts with no page reload — confirmed by `tests/ui.spec.js` and by manual screenshot inspection (slider drag → readout change, same DOM, no navigation).
3. Partial pooling is always mathematically between no-pooling and complete-pooling, inclusive at the tau=0/sigma=0 limits — confirmed by a dedicated property test across a mixed-size dataset, plus the two exact-collapse tests at the boundaries.
4. A small-sample group shrinks visibly more than a large-sample group under identical τ/σ — confirmed both by the `computeShrinkageWeight` monotonicity unit test and, concretely, in the running app's default view: Group 0 (n=3) has shrinkage weight 0.57 versus 0.93 for the n=30 groups, and the chart's connecting lines visibly differ in length.
5. The AI-explain panel never calls the network without a key, and any AI response text is rendered without executing as HTML/script — confirmed by two dedicated tests, one intercepting the network call to prove it's never made with no key, one feeding a mocked `<img onerror=...>` payload through the real rendering path and confirming zero script execution and an escaped `innerHTML`.

Security checklist (STANDARDS.md):
- No `.env` files, no hardcoded credentials/secrets/personal data anywhere in `src/` or `index.html` — confirmed by grep.
- No `eval()`/`exec()`/`new Function()` anywhere in this build — confirmed by grep.
- The only `innerHTML` assignments (`src/app.js`) clear a container to an empty string before rebuilding it with `textContent`-based nodes; no user- or API-controlled data is ever assigned via `innerHTML` — confirmed by grep and by the hostile-payload test.
- No `os.system()`/`subprocess` calls anywhere in this build (pure client-side JS, no Python).
- No file paths are constructed from user input anywhere in this build.
- All files live under this build folder; only `builds/index.md` and `builds/ideas.md` are touched outside it.

### [01:25 UTC] Documentation — Step 8

- `Manual.md` written (this build has a UI: the interactive simulator itself).
- `FutureFeatures.md` written with 8 concrete suggestions across three effort tiers.

Build complete. Success criteria reviewed. All tests passing.
