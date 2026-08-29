# Build Log — Zebra Lab

> **Date:** 2026-08-29
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:10 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for incomplete builds. Most recent local dated folder (`2026-06-18-regex-dojo`) has a completed `BUILD_LOG.md` ending in "Build complete. Success criteria reviewed. All tests passing." — no resume needed.
- Resynced `builds/index.md` and `builds/ideas.md` from the most recently created open PR branch (`claude/cool-sagan-vzvosz`, PR #83, 2026-08-28). Local `main`/working branch was over two months behind — 76 builds exist upstream that aren't yet reflected locally. Noted for end-of-session: 30 open PRs (spanning 2026-07-28 to 2026-08-28) and several older closed-but-unmerged PRs currently sit off `main`; this is a pre-existing backlog unrelated to tonight's build and out of scope to fix (would require modifying files outside the build folder).
- Day of year 241 → `category_index = (241-1) % 9 = 6` → Category G (Game/Puzzle).
- Category G backlog (synced `ideas.md`): 4 pending matching rows (11, 12, 22, 23), all blank ratings → R=0 → lottery_chance=25%. Rolled 50/100 → above gate → fresh idea generation.
- Generated 3 fresh candidates, selected "Zebra Lab" — a procedurally generated logic-grid deduction game over a research-methods taxonomy, solved by a from-scratch CSP backtracking solver with a minimality-pruned clue generator. Full reasoning in `WhyThis.md`.
- Build folder created: `builds/2026-08-29-zebra-lab/`

### [08:25 UTC] PRD Written

- Goal: procedurally generated, solver-verified-unique logic-grid deduction game over a real research-methods taxonomy.
- Scope: 3-chapter difficulty gate, 4 clue types (`eq`/`neq`/`adjacent`/`less`), Daily Challenge with deterministic UTC-date seeding, Practice mode, persistent localStorage stats, optional AI explainer panel (Claude Haiku, deterministic fallback).
- Notable decision: cut a secondary "pencil marks" elimination grid from scope to keep the core loop (clues → answer-grid selects → check) tight and fully testable in one session (logged in PRD's Scope Changes and in FutureFeatures.md).

### [08:30 UTC] Build Phase — Core Logic

Built `src/data.js` (category/chapter taxonomy: Population, Study Design, Confound Control, Threat to Validity, Sample Size) and an initial `src/logic.js` with a naive position-major backtracking solver.

A direct Node sanity check (loading `data.js`/`logic.js` into a `vm` context, generating 20 puzzles per chapter with a full minimality-removal verification) caught a real performance bug before any UI was built: Chapter 1 (4x3) solved in ~1.7s for 20 trials, but Chapter 2/3 (5x4) hung indefinitely. Profiling isolated it to the puzzle generator's incremental "add clues until unique" loop — some `zlCountSolutions` calls on partially-built clue sets returned `count=0` with the solver's node-cap safety hit, meaning the search was exploring hundreds of thousands of dead branches without finding even the one solution known to exist.

Root cause: the original solver only validated clues at position boundaries with no real constraint propagation, so branching stayed at its full unconstrained factorial size (up to (5!)^4 ≈ 207M leaf paths) for a 5x5x4 puzzle. Rewrote the solver as a proper constraint-propagation + backtracking CSP solver (domain-filtering per (category, position) cell, standard "all-different" hidden-single/naked-single propagation within each category, and generic AC-3-style arc-consistency propagation for each of the 4 clue relation types) with MRV branch-cell selection — the same technique real Sudoku/zebra-puzzle solvers use, since naive backtracking is not viable at this puzzle size.

First rewrite still hung on Chapter 2/3. A second profiling pass found the actual bug: the all-different propagation's two elimination loops were transposed (each was eliminating a value/position combination that was already trivially false by the very condition that triggered it — a no-op) — meaning that propagation pass wasn't functioning at all and the solver was relying solely on the weaker per-clue arc-consistency checks. Fixed the two loops to eliminate the correct cells (a confirmed-position value clears other values from that position; a confirmed-value position clears that value from other positions). Re-ran the Node sanity sweep: Chapter 1 in 276ms, Chapter 2 in 1.6s, Chapter 3 in 2.5s for 20 full trials each (generation + uniqueness proof + full per-clue minimality-removal verification + solution-match check) — all passing, all minimal.

### [09:05 UTC] Build Phase — UI

Built `index.html`, `src/app.js` (screens, answer-grid rendering, localStorage-backed progress/stats/daily-gate), `src/styles.css` (CSS custom properties, dark/light via `prefers-color-scheme`, mobile-responsive with a scrollable answer-grid container), and `src/ai.js` (deterministic fallback explanation composed from two small factually-reviewed snippet tables in `data.js`, with an optional direct-browser Claude Haiku call gated on a user-supplied, session-only API key).

Manual smoke test via a headless-Chromium script (not part of the automated suite) confirmed: home screen renders with no console/page errors, starting a Chapter 2 practice puzzle renders a full clue list and 5x4 answer grid, filling in the actual solution and checking transitions to the result screen with the deterministic AI-explainer text, and dark-mode + 375px-wide mobile layouts both render without breaking.

### [09:20 UTC] Tests Written and Run

Wrote 35 Playwright tests across 6 spec files: `solver.spec.js` (6, CSP correctness/uniqueness/contradiction), `generator.spec.js` (6, minimality + determinism + seed sweep), `clues.spec.js` (5, clue-text matches the underlying relation for all 4 clue types), `ui-grid.spec.js` (5, grid rendering/check/hint/navigation), `ui-progress.spec.js` (8, chapter gating/daily gate/stats persistence/streak logic/share-string privacy), `ai.spec.js` (5, no-key fallback with zero network calls, mocked success, mocked failure, API-key session-only storage).

First run: 34 passed, 1 failed (`clues.spec.js`, a "less" clue text assertion expecting the word "before" that only applies to the position-involved phrasing variant, not the cross-attribute phrasing "has a lower study number than" — a test-expectation bug, not a code bug). Fixed the assertion to accept both valid phrasings.

Tests: 35 passed, 0 failed.

### [09:30 UTC] Verify — Step 7

Success criteria review:
1. All tests pass (35/35) — met.
2. Solver-verified unique + minimal solution across all 3 chapters, 20+ seeds each in tests plus the earlier Node sanity sweep — met.
3. Daily Challenge deterministic per UTC date (tested), one-completion-per-day gate enforced via `zebralab_daily` localStorage check (tested) — met.
4. Chapter unlock gating and stats survive a reload — tested directly by writing localStorage then reloading the page — met.
5. AI panel works with both a mocked live call and no key present, and the network payload is limited to the puzzle's own category labels (the prompt sent to Anthropic only ever names a Confound-Control-Method/Threat-to-Validity pair and the deterministic fallback sentence being rephrased — no personal or user-entered data) — met.

Security checklist: no `.env` files, no hardcoded credentials/keys, no `eval()`/`exec()`, no `innerHTML` from user-controlled data (all DOM text set via `textContent`/`option.textContent`), no `subprocess`/`os.system`-equivalent calls, no file-path traversal, nothing reads outside the build folder. Confirmed by inspection of `src/*.js`.

### [09:35 UTC] Docs

- `FutureFeatures.md`: 8 concrete suggestions (pencil-marks notes grid was the scope cut noted in the PRD).
- `Manual.md`: quick start, full feature walkthrough, configuration (API key), troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
