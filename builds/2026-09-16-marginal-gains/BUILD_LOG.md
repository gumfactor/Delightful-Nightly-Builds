# Build Log — Marginal Gains

> **Date:** 2026-09-16
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:12 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md, and the most current `builds/index.md` / `builds/ideas.md` (resynced from the most recent open PR branch, `claude/cool-sagan-n20e0j`, PR #100, since `main` is far behind — 100 open PRs exist, none merged since 2026-06-18. This repo's own backlog has flagged that staleness before; it is a pre-existing condition of the repo, not something this session can fix without merging PRs, which is outside this build's scope).
- Step 0: most recent local dated folder was `2026-06-18-regex-dojo`; its `BUILD_LOG.md` ends with "### [08:30 UTC] Verify — Step 7

PRD success criteria:
1. All tests pass (zero failures) — ✓ 34/34, confirmed across 4 consecutive runs.
2. DP solver cross-checked against brute-force enumeration, never beaten — ✓ `tests/engine.spec.js` runs this over 40+ randomized small instances plus a separate 20×200-sample random-search-never-beats-optimum check.
3. A full round is playable end-to-end with zero console/page errors — ✓ verified both in the committed Playwright suite (`a full play-through produces zero console errors and zero page errors`) and in the manual headless-Chromium QA pass.
4. Daily Challenge deterministic per UTC date, one attempt per day enforced — ✓ `daily RNG determinism` (engine) and the two Daily Challenge tests (game) cover both halves.
5. No AI-returned/player-influenced string ever inserted via `innerHTML`; script-injection payload confirmed inert — ✓ `a malicious AI response renders as inert text` injects a live `<img onerror>` + `</script><script>` payload through a mocked Anthropic response and confirms zero dialogs, zero `window.__pwned`, zero injected `<img>` nodes.

STANDARDS.md security checklist run against every file in `src/`, `tests/`, `index.html`:
- No `.env` files
- No occurrences of real `password`/`api_key`/`secret`/`token`/`private_key` values (the only "key" in the codebase is the user-supplied, session-only, never-persisted Anthropic API key input)
- No `eval()`/`exec()`
- No `innerHTML` assignments anywhere in `src/` — every dynamic node uses `createElement`/`textContent` via the `el()` helper in `game.js`
- No `os.system()`/`subprocess` (pure client-side JS, no Python in this build)
- No file-path handling of any kind (browser-only, no filesystem access)
- All files self-contained under `builds/2026-09-16-marginal-gains/`; the only file outside this folder that will be touched is `builds/index.md`

Also confirmed: this build never sends the flavor-text "project" data or any real personal data to a third party — the only network call the code can make is the opt-in AI Advisor request, and even that sends only already-computed generic numbers/labels (project names from the static pool, hours, values), never anything about the actual user.

### [08:32 UTC] Documentation

- `FutureFeatures.md`: 9 concrete suggestions across Quick Wins / Medium Effort / Ambitious Extensions, plus Known Limitations.
- `Manual.md`: written, covering quick start, every mode, configuration, troubleshooting, and known limitations.

Build complete. Success criteria reviewed. All tests passing." — no interrupted build to resume. (The catalog shows builds through 2026-09-15 on open PR branches that never merged to `main`/never existed locally in this container's checkout; those are separate completed sessions, not incomplete work for this session to resume.)
- Day of year for 2026-09-16 = 259. `category_index = (259-1) % 9 = 6` → **Category G — Game / Puzzle**.
- Calibration note in CLAUDE.md claims "every rated build has scored 4/10 or below," but the actual `builds/index.md` shows ratings up to 9/10 (Qualtrics Survey Data Inspector) and several 5s/6s — this mismatch was already caught and documented by a prior build (AgentLint, 2026-07-16). Treating the real per-build notes in `builds/index.md` as the actual soft prior, per Step 2a, rather than the stale summary line.
- Category G backlog (`builds/ideas.md`): 6 pending rows (#11, #12, #23, #32, #47, #48), all with blank ratings (R=0). `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled `python3 -c "import random; print(random.randint(1,100))"` → **55**. 55 > 25 → lottery missed, proceeding to fresh idea generation (Step 2d).
- Reviewed the 10 prior Category G builds' mechanics to avoid repeats: regex-writing (Regex Dojo), real-vs-fake trivia (Neurofact), category sorting (Synapse Sort), vignette flaw-spotting ×2 (Confound Hunter, Heuristic Hunt), Wordle-style word guessing (Lexicon), investing chart/trivia (Quarter Call), physics simulation (Fairway Physics), CSP logic-grid deduction (Zebra Lab), navigation/vector-math puzzle (True Course). None of the pending backlog rows offer a genuinely new mechanic beyond these (Circuit Six is a hand-curated graph-traversal game already flagged as weak; Pace Strategy Simulator was explicitly deferred as "too close to Fairway Physics"; Data Detective and Diagnosis Duel both sit close to the existing vignette/CSP research-methods lineage).
- Generated 3 fresh Category G candidates (full reasoning in `WhyThis.md`): a resource-allocation optimization puzzle ("Marginal Gains"), a code-debugging puzzle, and a probability-calibration arena. Selected **Marginal Gains** — a browser game where the player allocates a limited weekly hour budget across simultaneous academic/entrepreneurial projects (grant reports, manuscript R&Rs, IRB renewals, course prep, Canada List QA sprints, etc.) with realistic diminishing-returns value curves, scored against a real dynamic-programming solver's provably optimal allocation. Ties directly to PROFILE.md's named friction points ("managing many simultaneous projects," "administrative overhead," "context switching between academic and entrepreneurial roles") and introduces a genuinely new mechanic (constrained optimization, not quiz/deduction/physics/navigation) to Category G.
- Build folder created: `builds/2026-09-16-marginal-gains/`

### [08:20 UTC] PRD Written

- Goal: a browser puzzle game that teaches real resource-allocation trade-offs by scoring the player's hour-allocation decisions against a verifiably optimal dynamic-programming solution.
- Scope: DP optimal solver (with startup thresholds + diminishing returns per project), Daily Challenge (UTC-seeded) + Practice mode + a Tutorial round, per-project Canvas 2D value-curve visualization, results/comparison screen, localStorage Mastery Dashboard, optional direct-browser Claude Haiku coaching note with a deterministic fallback.
- Notable decisions: value tables are precomputed as explicit arrays (not hardcoded outcomes) from randomized-but-bounded parameters, so every puzzle instance's "optimal" is freshly computed by the same solver a brute-force test cross-checks. No ES modules, classic `<script>` tags, so the game opens directly via `file://` like the catalog's other vanilla-JS games.

### [08:22 UTC] Build Phase — Core Engine and UI

- Built `src/engine.js` (16-entry project pool across 5 categories tied to named PROFILE.md work — lab, teaching, Canada List, Kwyeter, writing, admin; a mulberry32 seeded RNG for Daily Challenge determinism; `generateValueTable` for the per-project startup-threshold + sqrt-shaped diminishing-returns curve; `solveOptimal`, a real O(projects × budget × maxHours) dynamic-programming knapsack solver with allocation reconstruction), `src/ai.js` (AI Advisor: prompt builder, deterministic fallback note computed from the real largest-gap project, and a direct-browser Anthropic fetch with a `module.exports` guard so the same file runs under both Node tests and the browser), `src/game.js` (full view controller: Home, Tutorial with a hand-drawn Canvas 2D value-curve chart, difficulty picker, Play with stepper-based allocation and a live budget bar, Results with a per-project comparison table and AI Advisor wiring, Mastery Dashboard with streak/category-performance computation, all localStorage reads/writes wrapped in try/catch), `index.html`, and `src/styles.css` (dark mode, CSS custom properties, mobile-responsive).
- A brute-force cross-check in `tests/engine.spec.js` enumerates every possible allocation for small randomized instances (2–3 projects, budget ≤ 10) and confirms `solveOptimal` always matches it exactly — this is the core correctness guarantee for the whole game, since every player's score is a percentage of this solver's reported optimum.
- Caught and fixed one real bug via the test suite before it reached the UI: an early version of the `value at hour 0` test asserted the value became positive at `h === threshold`, but the formula correctly evaluates `sqrt(threshold - threshold) = sqrt(0) = 0` — value only turns positive the hour *after* the threshold, since the threshold hour itself is pure startup cost with zero marginal return yet. Fixed the test, not the engine, after confirming the engine's behavior was the intended design (threshold hours are setup, not payoff).
- Caught and fixed a design risk in `tests/game.spec.js`'s "allocating past budget disables Lock In" test during authoring, before it ever ran flaky: the Light difficulty tier's 24h budget equals exactly 4 projects × the minimum possible per-project `maxHours` (6h), so maxing out a real random draw could theoretically land exactly at the budget rather than over it. Fixed by pinning `Math.random` to a fixed value via `page.addInitScript` for that one test and computing the same deterministic draw through the identical `engine.js` (via Node `require`) to assert the draw's total capacity exceeds budget before relying on it — makes the test fully deterministic instead of a-few-in-ten-thousand flaky.

### [08:24 UTC] Tests Run

Ran `npx playwright test` four times in a row (including immediately after every fix) to check for flakiness given several tests touch randomized practice draws and async AI-advisor flows.

Tests: 34 passed, 0 failed. (Every run, all 4 runs.)

### [08:26 UTC] Manual QA — headless Chromium

Ran a standalone Playwright script (not part of the committed test suite) to screenshot every view — Home, Tutorial (chart correctly bends, matching the diminishing-returns formula), Practice play (6 real project cards with correct flavor text/categories), Results (82% of optimal, B grade, per-project table, deterministic AI Advisor note all internally consistent), Dashboard (1 round played, 82% average, correct per-category value-capture percentages), and a 375px mobile viewport (no overflow, buttons wrap cleanly). Zero console/page errors across the whole pass. Screenshots and the standalone script were temporary QA aids, not committed.
