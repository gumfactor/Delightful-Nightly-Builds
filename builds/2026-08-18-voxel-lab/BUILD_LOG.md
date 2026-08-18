# Build Log — Voxel Lab

### [00:00 UTC] Step 0 — Interrupted build check
`ls builds/ | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}-'` locally shows the last dated folder as `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — done, nothing to resume.

Local `main`/this branch is far behind the actual catalog: queried open PRs via the GitHub MCP server (no `gh` CLI available in this environment) and found 30 open PRs, the most recent being #74 (`build(2026-08-17): Maple Press`, branch `claude/cool-sagan-wramd3`). None have been merged to `main` since 2026-06-18 — a known, previously-documented pattern (see Pipeline Pulse, 2026-07-09). Fetched `builds/index.md` and `builds/ideas.md` from that branch per CLAUDE.md Step 1's instruction to always read the most current version. Confirmed 2026-08-17's Maple Press build is `complete` — no resume needed there either.

### [00:05 UTC] Step 1 — Orient
Read `PROFILE.md`, remote `builds/index.md` (67 total builds, 64 complete, last build 2026-08-17), and `STANDARDS.md`.

### [00:08 UTC] Step 2 — Decide
`date +%j` = 230 (2026-08-18). `category_index = (230-1) % 9 = 4` → **Category E — Learning Aid**.

Remote `builds/ideas.md` backlog: 17 rows, zero with Category = E. Lottery skipped per Step 2c (empty pool) → fresh idea generation (Step 2d).

Last 10 builds (2026-08-08 → 2026-08-17): Panel Prep(D), Portfolio Lab(E), Ingest Gate(F), Quarter Call(G), Snipvault(H), Macro Kitchen(I), Earshot(A), Provenance(B), Curriculum Atlas(C), Maple Press(D). Topic-diversity check: investment/finance appears twice (Portfolio Lab, Quarter Call) — at the threshold, not over it, so no domain is forced-excluded.

Existing Category E builds (5 total): Power Lab (statistical power/sample size), CircuitLab (neuroanatomy), Bayes Lab (Bayesian inference), Signal Detection Lab (SDT), Portfolio Lab (Modern Portfolio Theory). All are either general statistics or anatomy — **none touch neuroimaging analysis methodology**, despite PROFILE.md explicitly naming "Neuroimaging methods and forensic neuroscience" as a rabbit-hole interest and "conduct neuroimaging and behavioral studies" as a literal day-to-day duty.

Three fresh candidates generated:
1. **Voxel Lab** — interactive fMRI preprocessing-pipeline walkthrough + a from-scratch multiple-comparisons/false-positive-rate simulator (the "dead salmon" problem: uncorrected vs. Bonferroni vs. Benjamini-Hochberg FDR vs. cluster-extent correction) + HRF convolution demo + quiz.
2. GLM & Regression Diagnostics Trainer — live-manipulable scatterplot regression with assumption-violation diagnostics (heteroscedasticity, leverage, multicollinearity). Rejected: 3rd stats-trainer in the category (after Power Lab, Bayes Lab) with less topic differentiation than option 1.
3. Attention Mechanism Visualizer — from-scratch self-attention/transformer walkthrough on a toy sentence. Rejected: no PROFILE.md data source or day-to-day duty ties as directly as option 1; softer novelty case (a generic ML-education tool rather than something tied to the user's own lab work).

**Selected: Voxel Lab.** Strongest tie to a named, untouched PROFILE.md domain, the only one of the three with a "no prior build touches this" argument, and the multiple-comparisons simulator is a real Monte-Carlo computation (not a prose wrapper), directly answering the AI Lecture Builder failure mode ("a power user replicates this with one prompt").

Ideas 2 and 3 appended to `builds/ideas.md` as backlog rows 18–19 (Category E, complexity `ambitious`, status `pending`). No linked Idea Brief exists for this idea (fresh generation, not lottery) — Step 2e is not applicable.

Stack: browser tool (Learning Aid requires an interactive interface per STANDARDS.md) → vanilla HTML/CSS/JS, classic scripts (no ES modules, opens directly via `file://`, following the established convention from Power Lab/CircuitLab/Bayes Lab/Signal Detection Lab), Playwright tests. No external API needed — this is entirely self-contained synthetic simulation and math, so no live-data design tradeoff applies. Deployment model: on-demand browser tool, not a Routine/Skill/Hook (the user opens it when studying/teaching, not on a recurring trigger).

### [00:15 UTC] Step 4 — PRD
`PRD.md` written before any code.

### [00:20 UTC] Step 5 — Build
Wrote `src/stats.js` (Box-Muller Gaussian RNG, erf/normalCdf, Bonferroni, Benjamini-Hochberg FDR, 4-connected cluster labeling, double-gamma HRF, discrete convolution, Gauss-Jordan least-squares GLM), `src/mc-sim.js` (Monte Carlo trial engine, plus `runComparison` which applies all 4 correction methods to the *same* noise draw per trial for a fair side-by-side rather than four independent samples), `src/pipeline.js` (6 pipeline steps with real canvas computation — the smoothing step runs an actual box-blur convolution over a generated noise field; the HRF/GLM step runs real convolution + least-squares beta recovery), `src/quiz.js` (10 conceptual + 6 computed questions — computed questions regenerate their correct answer and distractors from the live `stats.js` functions at quiz-build time, never a hardcoded fact), `src/app.js` (tab/UI wiring), `src/styles.css`, `index.html`.

`npm install` (local `@playwright/test`) succeeded without network issues — this build makes zero external calls of any kind, so no build-container egress-proxy constraint applies (unlike most prior builds, there is no "design for the user's runtime" tradeoff to document here).

### [00:45 UTC] Step 6 — Tests
Wrote 6 spec files (`stats.spec.js`, `pipeline.spec.js`, `mc-sim.spec.js`, `quiz.spec.js`, `security.spec.js`, `responsive.spec.js`), 33 tests total. `playwright.config.js` pins `executablePath` to this container's pre-installed Chromium (`/opt/pw-browsers/chromium-1194/...`), following the established pattern from `2026-06-18-regex-dojo`.

First run: 30 passed, 3 failed — all 3 failures in `quiz.spec.js`, all timing out waiting for `[data-testid="quiz-feedback"]` after the first answer. Root cause: `app.js`'s `selectAnswer()` was reassigning `feedbackEl.dataset.testid = 'quiz-feedback-shown'` after the first click, which changes the element's actual `data-testid` attribute away from `"quiz-feedback"` — so the selector Playwright (and any future querying code) uses stops matching after the very first interaction. This was a genuine bug, not a test artifact: it would have broken any external automation or accessibility tooling targeting that element post-interaction. Fixed by deleting the stray reassignment; re-ran and all 33 passed. Re-ran the full suite 3 additional times back-to-back to check for flakiness from the app's `Math.random()`-seeded runtime behavior (quiz question order/distractors, MC simulation draws) — 33/33 passed all 4 runs.

`[00:52 UTC] Tests: 33 passed, 0 failed.`

### [00:55 UTC] Manual QA pass
Ran a standalone Playwright script (not part of the committed test suite) against the real page in headless Chromium to screenshot every tab, both pipeline phases, the thresholding step, the MC lab after running a simulation, and the quiz mid-answer — at both desktop (1280px) and mobile (375px) viewports. Zero page errors, zero console errors, zero dialogs across the whole session.

The MC Lab screenshot at voxelCount=5000/alpha=0.05/trials=50 showed uncorrected mean false positives of 254.34 versus 0.06 (Bonferroni), 0.08 (FDR), and 0.42 (cluster-extent) — a clean, visually obvious demonstration of the core teaching claim (success criterion #2), not just a passing assertion.

Found and fixed one real visual bug during this pass: the Statistical Thresholding pipeline step's canvas only filled the left half of its 640x320 area, because its 900-voxel grid is laid out as a 30x30 square (`gridWidthFor` uses `sqrt(voxelCount)`) but the canvas is a 2:1 rectangle, and the render code was drawing from the canvas's left edge instead of centering the square grid. Fixed by centering the grid horizontally (`src/pipeline.js`'s `renderThresholding`); re-verified visually and re-ran the full test suite (still 33/33 passing — no test had covered this framing/centering detail, since the non-blank canvas check doesn't care about layout).

Cleaned up the standalone QA script and the `test-results/` Playwright artifact directory afterward — neither belongs in the committed build folder.

### [01:00 UTC] Step 7 — Verify success criteria
1. ✓ All 6 pipeline steps navigable, each renders distinct non-blank canvas with correct explanation/pitfall text — `pipeline.spec.js`, manually screenshotted
2. ✓ MC simulator run through the real UI at 8,000 voxels / 60 trials shows uncorrected mean false positives >200 while Bonferroni/FDR means stay under 1/10th and 1/5th of that respectively — `mc-sim.spec.js`, and manually verified at 5,000/50 trials (254.34 vs 0.06/0.08/0.42)
3. ✓ Bonferroni, BH-FDR, HRF peak timing, GLM beta recovery, cluster labeling, and Gaussian RNG moments all match hand-worked reference values within tolerance — `stats.spec.js` (10 tests)
4. ✓ Quiz tracks score correctly across all 16 questions (10 conceptual + 6 computed), including verifying a computed question's correct answer is checked against the live formula across 5 different seeds, not a fixed string — `quiz.spec.js`
5. ✓ Zero external network requests anywhere in the app (`security.spec.js`); no innerHTML/eval/Function/document.write in any source file (static scan); a live full-session run produces zero dialogs/page errors
6. ✓ 33/33 Playwright tests pass, confirmed stable across 4 consecutive runs

Security checklist (STANDARDS.md):
- No `.env` files
- No hardcoded credentials (verified by a dedicated test scanning all source files)
- No `eval()`/`Function()`/`document.write` anywhere (verified by a dedicated test)
- No `innerHTML` assignment anywhere — all DOM construction via `createElement`/`textContent` (verified by a dedicated test)
- No file paths from user input; no `subprocess`/`os.system` calls at all (pure client-side JS)
- All code self-contained in the build folder; zero external API/network calls of any kind

### [01:05 UTC] Step 8 — Documentation
- `FutureFeatures.md`: 6 concrete enhancements
- `Manual.md`: usage guide, tab-by-tab walkthrough, test command

Build complete. Success criteria reviewed. All tests passing.
