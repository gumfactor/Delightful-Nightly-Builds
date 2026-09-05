# Build Log

### [Orient] Step 0-1
No incomplete build found — most recent local dated folder (2026-06-18-regex-dojo) ended with the required "Build complete." line. This session's branch (`claude/cool-sagan-mltlo1`) is a fresh fork of `main` with no prior commits of its own, confirming nothing of this session's own was left mid-build.
Synced `builds/index.md` and `builds/ideas.md` from the most recently opened PR branch (`claude/cool-sagan-gb5aul`, PR #89, build(2026-09-04): CaseForge) since local `main` was stale back to 2026-06-24 while 82 further builds existed on unmerged PR branches.

### [Decide] Step 2
Day of year 248 → category_index 4 → Category E (Learning Aid). Category E backlog held 1 pending matching idea (#19, unrated). Lottery gate 25% (R=0), rolled 33/100 — missed, routed to fresh generation. Selected: Mediation & Moderation Analysis Lab. Full reasoning in WhyThis.md. New backlog idea #44 (Meta-Analysis / Forest Plot Trainer) logged as a non-winner.

### [Design] Reference values
Before writing any JS, built an independent pure-Python (stdlib-only) Gauss-Jordan OLS reference implementation and hand-verified:
- A 10-row mediation fixture (X→M→Y): path a=1.495151515151516, b=2.2116019493789736, c'=0.17938060053438676, c=3.486060606060608, indirect=3.306680005526019, and the algebraic identity c ≈ c'+a·b held to 9 significant figures.
- A 15-row moderation fixture (centered X,Z): beta=[10.035270724890479, 1.2076187802311653, 0.8238704155315291, 0.5773905609676386], full 4x4 covariance matrix, dof=11, simple slopes at k=-1/0/+1 SD, and Johnson-Neyman roots at t_crit=2.200985160 (df=11, α=.05): z ≈ -1.996152224371137 and -2.19090829611953, each independently re-verified by plugging the root back into slope/SE and confirming |t| = t_crit exactly.
These fixture datasets and expected values are hardcoded into the JS test suite and are the ground truth the JS engine is checked against, not derived from the JS code itself.

### [Build] Step 5
Built the full engine and UI: `rng.js` (seeded mulberry32 PRNG + Box-Muller Gaussian noise + string-seed hashing), `stats.js` (Gauss-Jordan matrix inversion with partial pivoting, OLS regression with full coefficient covariance matrix, Lanczos log-gamma, regularized incomplete beta via continued fraction, Student t CDF/critical-value bisection, normal CDF via an Abramowitz-Stegun erf approximation), `mediation-engine.js` (path a/b/c/c′, bootstrap percentile CI, Sobel test), `moderation-engine.js` (centered-interaction regression, simple slopes from the covariance matrix, Johnson-Neyman quadratic solve), `quiz-data.js` (8 fixed + 8 live-generated questions), `ai-explain.js` (aggregate-only Claude Haiku call with deterministic fallback), and `app.js` (tab switching, slider wiring, Canvas 2D path diagram/scatterplot/JN-strip rendering, quiz flow).

### [Tests] Step 6
`npm install` pulled `@playwright/test@1.56.1` locally into this build folder (the global `playwright` CLI package is pre-installed in this container but `@playwright/test` is not, matching the pattern several prior catalog builds already documented). `playwright.config.js` points at the container's pre-installed Chromium (`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`).

First full run: 44/49 passed. Five real issues found and fixed, not test-fudged:
1. `stats.spec.js`'s "OLS multiple regression" test had its own fixture assertions mislabeled (checked `beta[1]`/`beta[2]` against the intercept/c′ values in the wrong slots) — fixed the test, the engine's own output was already correct against the Python reference.
2. `mediation-engine.spec.js`'s original "zero-noise" test tried `noiseSD: 0`, which makes M an exact affine function of X with no independent variation — a genuine mathematical constraint (X and M become perfectly collinear, so the Y~X+M regression is singular), not a bug. Replaced with a cleaner, statistically well-founded test: a larger sample size (n=400 vs n=20) produces a narrower bootstrap CI, holding the true model fixed.
3. `moderation-ui.spec.js`'s slider test used `0.25` on a slider with `min=-1, step=0.02` — HTML range inputs sanitize a programmatically-set value to the nearest valid step, and 0.25 isn't step-aligned from that min (snaps to 0.26). Fixed by using a step-aligned test value (0.30).
4. `quiz.spec.js`'s "answering incorrectly" test assumed it was on the *second* fixed question when the test actually starts fresh on the *first* one (whose correct index is 0) — clicking index 0 was answering correctly, not incorrectly. Fixed by clicking the actually-wrong index (1) on question 1.
5. `stats.spec.js`'s `sampleSD` test used the classic textbook array `[2,4,4,4,5,5,7,9]` expecting the well-known *population* SD of 2, but `sampleSD()` deliberately implements the *sample* (n-1) formula throughout this codebase (consistent with its use for the moderator's SD in `moderation-engine.js`) — correct sample SD for that array is sqrt(32/7) ≈ 2.138. Fixed the test's expected value rather than changing the formula, since the sample-SD convention is the one that must match the simple-slopes math elsewhere in the app.

Second run: 49/49 passed.

Tests: 49 passed, 0 failed.

### [Verify] Step 7 — Manual QA and success criteria
Ran a standalone Playwright script (not part of the committed suite) against the real rendered app in the container's pre-installed headless Chromium: generated a mediation sample and a moderation sample, screenshotted all three tabs plus a 375px mobile viewport, and confirmed zero `pageerror`/console-error events throughout. Screenshots confirmed the path diagram, scatterplot with three correctly-ordered simple-slope lines, and the Johnson-Neyman significance strip all render correctly and match the numbers in the results tables; the mobile viewport showed no layout breakage. Also manually exercised the AI-explain deterministic fallback (both tabs) and the full 16-question quiz completion flow end-to-end — text output was substantively correct and the review screen listed all 16 answered questions.

Security checklist (STANDARDS.md): grepped all source files for `innerHTML`, `eval(`/`exec(`/`new Function(`, and hardcoded credential-like strings — zero matches. No `.env` files present. All DOM updates use `textContent`/`createElement` exclusively (confirmed by the dedicated XSS tests in `security.spec.js`, which round-trip a live `</script><script>` + `<img onerror>` payload through the AI-explanation render path and confirm it never executes). No `subprocess`/`os.system`/shell calls anywhere (pure client-side JS, no server component). No file-path handling of user input at all.

Success criteria review (from PRD.md):
1. Mediation engine matches independently hand-computed Python reference values within 1e-6 (tests 1-2 in `mediation-engine.spec.js`, `stats.spec.js`), and the c = c′ + a×b identity holds on every freshly generated sample (test 2) — met.
2. Moderation engine's coefficients, simple slopes, and Johnson-Neyman roots match the independently hand-computed reference within 1e-6, including a root plugged back into the slope/SE formula reproducing t_crit exactly — met.
3. Same-seed determinism verified bit-for-bit for both engines (mediation and moderation determinism tests) — met.
4. All 16 quiz questions answerable/scored correctly, with live questions' answers traced to the same engine functions shown in the lab tabs (verified by construction in `quiz-data.js` and exercised in `quiz.spec.js`) — met.
5. Full Playwright suite (49 tests, well above the 15 minimum) passes with zero failures, including the XSS-inertness and zero-network-calls-without-a-key security tests — met.

Build complete. Success criteria reviewed. All tests passing.
