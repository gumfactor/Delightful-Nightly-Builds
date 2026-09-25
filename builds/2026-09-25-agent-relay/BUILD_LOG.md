# Build Log — Agent Relay

> **Date:** 2026-09-25

---

### [Orient] Step 0-1
- Checked for incomplete builds: most recent local dated folder (2026-06-18-regex-dojo) and the most recent open-PR branch's build (2026-09-24-corporate-ownership-explorer, PR #108) both end with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-wjtwim`, PR #108, 2026-09-24) per CLAUDE.md Step 1/Step 9 instructions — local `main`-derived copies were ~3 months stale (101 builds on the recent branch vs. 5 dated folders locally; this repo's builds are never merged to `main`, so every session must resync from the latest open PR).
- Read STANDARDS.md and PROFILE.md in full.

### [Decide] Step 2
- Day of year 268 → category_index 6 → **G — Game/Puzzle**.
- Category G backlog: 7 pending ideas, all unrated → 25% lottery gate. Rolled 23 (Python `random.randint(1,100)`) → gate hit. Weighted draw (all 7 tied, 5 tickets each) rolled 7/35 → idea #12, "Stock Chart Direction Quiz."
- Idea #12 turned out to be a verbatim duplicate of the already-built 2026-08-11 "Quarter Call" (same mechanic: real historical stock chart, guess Up/Down/Flat over the next quarter, Yahoo Finance data). Caught before writing any code. Corrected `builds/ideas.md` idea #12 to `skipped` with an explanatory note (same precedent as the 2026-07-27 SiliconWatch duplicate correction); flagged idea #11 (adjacent but not identical) with a deprioritization note. Overrode to fresh generation per CLAUDE.md Step 2d.
- Confirmed independently that tonight's build container's egress proxy blocks every external host tested except `api.github.com` (query1.finance.yahoo.com, stooq.com, en.wikipedia.org, api.open-meteo.com, sec.gov all returned 403 Forbidden) — consistent with prior builds' documented experience and irrelevant to tonight's final pick, which needs no external data.
- Generated 3 fresh Category G ideas: Agent Relay (resource-constrained parallel task scheduling), Bisect (git-bisect binary-search trainer), Lab Bench Triage (single-day lab resource scheduler). Selected **Agent Relay** — genuinely new mechanic for the category (no prior G build does dependency-graph scheduling), strong tie to PROFILE.md's "Master AI agent workflows and orchestration" learning goal, and no external data dependency at all (fully self-contained, sidesteps tonight's network restriction entirely). Non-winners logged to `builds/ideas.md` as ideas #71-72.
- No idea brief linked (fresh generation, no `idea-briefs/` entry).

### [Build] Step 3-5
- `src/engine.js`: scheduling simulation built on a "ready-queue" construction (a task can only ever be placed once all its dependencies are already placed), which guarantees every reachable state is valid by construction — no explicit cycle/order-violation check is ever needed. Sanity-checked by hand in Node before writing UI code: hand-computed chain/parallel/diamond DAGs all matched (`chain optimal=12`, `parallel/3lanes=5`, `parallel/1lane=12`, `diamond/2lanes=10`), then cross-verified the exact solver against independent brute-force enumeration on 30 randomized small DAGs — 0 mismatches.
- Exact solver: branch-and-bound over the same ready-queue construction, pruned by an admissible lower bound (`earliestFinishBound` — the earliest any remaining task could finish with lane contention relaxed to infinite lanes, which can only ever be ≤ the true optimum) plus lane-symmetry deduplication (skip placing onto two lanes that currently share the same free time) plus a greedy longest-remaining-critical-path initial upper bound. A node-visit cap (2,000,000) is a defensive-only safety net; every shipped level solves in ≤1 branch-and-bound node (the greedy seed already hits the lower bound) and a stress-tested harder synthetic 9-task/2-lane instance solved in 2,813 nodes / 16ms — comfortable headroom.
- `src/levels.js`: 6 hand-authored campaign levels (3-9 tasks, 2-3 lanes) plus a tutorial level, themed as a coding-agent session (clone → plan → build → test → review → ship). All 7 verified to solve without hitting the node cap before shipping.
- `src/graph.js`: layered-layout Canvas dependency-graph renderer (layer = 1 + max(dep layers)), verified layer assignment by hand on a 7-task/4-layer fixture.
- `src/ai.js`: optional "Mission Debrief" panel, adapted from the 2026-09-16 Marginal Gains build's proven `ai.js` pattern (direct-browser Claude Haiku call, injectable `fetchImpl` for testing, unconditional deterministic fallback, zero network calls without a key).
- `src/game.js`: UI state machine — click-to-select-then-click-to-place interaction (no native HTML5 drag-and-drop, for testability and touch-friendliness), 5 screens (Home, Level Select, Play, Result, Dashboard), `localStorage` persistence for campaign best scores and Daily Challenge streak/history.
- Caught and fixed one real bug during test-writing: the Playwright test helper's `[data-testid^="ready-"]` selector was also matching the `ready-tray` container div itself (its testid happens to start with "ready-" too), causing the greedy-placement test helper to click the tray container forever and never converge. Fixed by scoping the test selector to `#ready-tray [data-testid^="ready-"]` — a test-only fix, no product code changed.

### [Test] Step 6
- [21:00 UTC] Tests: 48 passed, 0 failed. (`npx playwright test`)
  - `tests/engine.spec.js` (28 tests): scheduling simulation, exact-solver correctness (including brute-force cross-verification and a "every shipped level solves without hitting the safety cap" check), grading boundaries, Daily Challenge generator determinism/acyclicity/non-degeneracy, AI debrief prompt/fallback/network-call behavior, graph layout math.
  - `tests/game.spec.js` (16 tests): tutorial walkthrough and guidance banner, optimal-play Gold grade, suboptimal-play exact-makespan Bronze grade, placement/selection/reset/submit-gating UI behavior, campaign level unlocking, Dashboard best-score persistence across replays, Daily Challenge one-per-day gating and share text, mobile viewport layout, AI panel (mocked network) behavior, a full zero-console-error playthrough.
  - `tests/security.spec.js` (4 tests): hostile task-name payload rendered inert everywhere it appears (result screen + lane recap), hostile mocked AI response rendered inert, zero `innerHTML` in shipped source (grep-verified), zero outbound network requests without an explicit user action.
  - `tests/smoke.spec.js` (1 test): home screen loads with zero console/page errors — legacy from initial page-load verification before the full suite existed; kept as a fast baseline check.

### [Verify] Step 7 — manual QA beyond the automated suite
- Ran a standalone Playwright script (not part of the shipped `tests/`) to screenshot a full playthrough: home (dark), level select, level in progress (task selected), completed placement, Gold result, AI fallback debrief, Dashboard (best score correctly shown as 9m), a 390px mobile tutorial view, and a 1280px light-mode tutorial view. Zero console/page errors across all of it. Visually confirmed: dependency graph arrows point the right direction and layers read left-to-right, lane blocks are proportional to duration and show correct start-finish times, Gold badge renders correctly, Dashboard reflects the actual best score. One cosmetic-only observation logged to `FutureFeatures.md`: the dependency-graph canvas uses a fixed palette rather than reading CSS theme variables, so it looks slightly dark-leaning even in light mode (still fully legible, not a bug).
- Security checklist (STANDARDS.md), grep-verified against `src/` and `index.html`:
  - No `.env` files anywhere in the build folder.
  - No `password`/`api_key`/`secret`/`private_key` with a real value assigned (the only match is the `<input type="password">` field's own type attribute and placeholder text for the user's own key — never a hardcoded credential).
  - No `eval()`, `exec()`, or `new Function()` anywhere in this build.
  - No `innerHTML` assignment anywhere (the only match for the string is a comment stating the DOM is built via `createElement`/`textContent` instead) — confirmed by grep and by the two hostile-payload rendering tests in `security.spec.js`.
  - No `os.system()`/`subprocess` calls (pure client-side JS, no Python in this build).
  - No file paths constructed from user input.
  - All files live under this build folder; only `builds/index.md` and `builds/ideas.md` are touched outside it.
  - `node_modules/`, `test-results/`, and `playwright-report/` are excluded via a build-folder `.gitignore`.
- Success criteria (PRD.md) checked:
  1. ✓ All tests pass, 48 (≥15 required), via `npx playwright test`.
  2. ✓ Solver matches brute force on every randomized cross-check fixture (`engine.spec.js`, 0 mismatches across 40 trials).
  3. ✓ A full campaign playthrough with a deterministic known-optimal sequence reaches the result screen with the correct Gold grade and exact makespan number (`game.spec.js`).
  4. ✓ Daily Challenge is deterministic per UTC date and gates to one attempt/day via `localStorage` (`engine.spec.js` determinism tests + `game.spec.js` gating test).
  5. ✓ Zero `innerHTML` usage (grep-verified) and hostile-payload tests pass with zero dialogs/page errors/injected DOM nodes.

### [Docs] Step 8 — Documentation complete
- `FutureFeatures.md`: 7 concrete suggestions.
- `Manual.md`: how to play, all 4 modes explained, the AI panel's data handling explicitly stated, test run instructions.

Build complete. Success criteria reviewed. All tests passing.
