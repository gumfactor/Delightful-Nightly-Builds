# Build Log — Confound Hunter

### [00:05 UTC] Step 0 — Incomplete build check
Checked `builds/` for an unfinished dated folder. Most recent (`2026-06-18-regex-dojo`) ends with
"Build complete. Success criteria reviewed." — no resume needed. Also confirmed via the open-PR list
that every night from 2026-06-19 through 2026-07-14 has an existing build (unmerged PRs still open on
`main`, but each has a completed BUILD_LOG on its own branch) — nothing to resume.

### [00:07 UTC] Step 1 — Orient
Read PROFILE.md, STANDARDS.md, and `builds/index.md` from the most recent open PR branch
(`claude/cool-sagan-jiwy54`, PR #41, 2026-07-14 GrantScope) rather than the possibly-stale `main` copy.
34 builds total, last build 2026-07-14 (F — GrantScope).

### [00:08 UTC] Step 2 — Decide
Day of year = 196. `(196-1) % 9 = 6` → Category G (Game/Puzzle).
Checked `builds/ideas.md` for pending G-category rows: #11 (Market Cap Higher/Lower) and
#12 (Stock Chart Direction Quiz), both blank rating (5 tickets each), R=0 rated → lottery_chance = 25%.
Rolled random 1-100 → 35 (via `python3 -c "import random; print(random.randint(1,100))"`) → 35 > 25 →
fresh-idea path.

Topic diversity check on last 10 builds (2026-07-05 to 2026-07-14): TrialScope, Synapse Sort, Schema
Sentinel, Ledger Lens, Pipeline Pulse, Worklog, Connectome, Research Question Forge, CircuitLab,
GrantScope. No single topic domain repeated more than twice; investment/finance appears once
(Ledger Lens, personal budgeting, not investing specifically) — not saturated.

Prior G builds: Regex Dojo (regex/coding), Neurofact (real-vs-fake neuroscience trivia), Synapse Sort
(Connections-style category grouping). Generated 3 fresh candidates, all G/ambitious, avoiding those
three mechanics and avoiding another investment quiz (weak historical domain — investment builds have
scored 3-6/10 range):

1. **Confound Hunter** — short fictional research-study vignettes; player identifies the single
   biggest methodological flaw (confound, selection bias, no control group, demand characteristics,
   ceiling effect, regression to the mean, correlation/causation, underpowered sample, no blinding,
   WEIRD-sample overgeneralization) from 4 options. Ties directly to PROFILE.md's actual job
   (teaches research methods courses, runs a lab, supervises students on study design).
2. **P-Hack Detective** — decide which of a list of post-hoc analytic choices constitutes a
   questionable research practice. Overlaps thematically with idea 1 (research integrity); weaker
   mechanic (binary yes/no per item vs. multi-choice diagnosis).
3. **Grant Triage** — timed ranking of fictional grant-pitch summaries against an expert fundability
   rubric. Reasonable, but landed one day after GrantScope (F, 2026-07-14) — same subject matter
   two nights running risks feeling repetitive even in a different category/mechanic.

Picked **Confound Hunter**: most novel mechanic among the three, most directly tied to the user's
actual daily expertise (research methods pedagogy), fully self-contained (no external API needed for
the core game — hand-authored vignettes are the right call here, since these are pedagogical training
scenarios, not real data, and fabricating "real" study data would be worse than curated fiction).
Appended ideas 2 and 3 to `builds/ideas.md` as new pending rows. No Idea Brief linked — fresh
generation, not a backlog draw.

### [00:10 UTC] Step 2f — Stack and deployment
Browser game → vanilla HTML/CSS/JS (classic scripts, no ES modules, so it opens directly via `file://`,
matching the pattern used by Synapse Sort / Power Lab / CircuitLab). Playwright for tests. No external
API calls — the entire dataset is hand-authored pedagogical content, evaluated with pure client-side
logic. Deployment model: standalone browser game, no Routine/Skill/Hook fit (not recurring, not an
editor-integrated capability).

### [00:15 UTC] Step 4 — PRD
Wrote `PRD.md` covering goal, user story, in/out of scope, tech stack, data structure (flaw taxonomy +
30-vignette schema + 3 localStorage keys), folder structure, testing strategy, and 5 success criteria.

### [00:16-00:22 UTC] Step 5 — Build
Authored `src/data.js` (10-item flaw taxonomy, 30 hand-written vignettes across 3 chapters of
increasing subtlety, each with 4 curated options and an explanation), `src/app.js` (game engine:
chapter practice with 70%-gated unlock, date-seeded Daily Challenge via a mulberry32 PRNG, per-flaw
Mastery Dashboard, localStorage persistence, reset control), `index.html`, and `src/styles.css`
(dark-mode-first with a light-mode media query, mobile-responsive).

### [00:24 UTC] Build — 28 Playwright tests written
`tests/game.spec.js` — data integrity, menu/navigation, practice question flow, chapter completion and
unlock gating, mastery dashboard, daily challenge (including determinism and one-per-day gating),
persistence/reset, grading logic, and an XSS-safety check on vignette rendering.

### [00:26-00:35 UTC] Step 6 — Test run and debugging
First run: **9 passed, 19 failed**. Root cause: the four menu nav buttons (`nav-practice`,
`nav-daily`, `nav-mastery`, `nav-reset`) in `index.html` carried only `data-testid`, not a matching
`id` — but `app.js`'s `qs()` helper uses `document.getElementById`. The very first `qs('nav-practice')`
call at script load returned `null`, so `.addEventListener` threw and aborted the rest of the
synchronous event-wiring code below it, silently breaking every other button on the page. Fixed by
adding `id` attributes to those four buttons.

Second run: **26 passed, 2 failed**.
- `each chapter (1-3) contains exactly 10 vignettes...` — test bug, not an app bug: the test referenced
  `FLAW_ORDER` directly in the Node.js test body instead of inside `page.evaluate()`, where browser
  globals aren't defined. Fixed by returning `FLAW_ORDER` from the evaluated function alongside the result.
- `answering a question updates the mastery dashboard...` — test bug: it tried to click a
  `back-to-menu-1` button that only exists inside the (currently hidden) chapters screen, not on the
  play screen, causing a 15s actionability timeout. Fixed by reloading the page (mastery is written to
  localStorage synchronously on answer) and navigating to the dashboard from the fresh menu screen.
- Also found and fixed a related bug in the same investigation: `test.beforeEach` used
  `page.addInitScript(() => localStorage.clear())`, which Playwright re-fires on every subsequent
  navigation in a test — including `page.reload()`. This silently wiped state in the one test
  (`progress persists across a page reload`) that specifically reloads mid-test to check persistence,
  making it impossible for that test to ever see saved data. Fixed by clearing storage once via
  `page.evaluate()` immediately after the initial `page.goto()` instead.

Third/fourth runs: **28 passed, 0 failed.**

[08:29 UTC] Tests: 28 passed, 0 failed.

### [08:30 UTC] Step 7 — Verify
Checked each PRD success criterion:
1. ✓ All 3 chapters playable end-to-end with correct/incorrect feedback and accurate grading; chapter
   2/3 unlock gating verified by tests 6, 13, 14, 15.
2. ✓ Daily Challenge is deterministic per UTC date (test 19), blocks replay on the same date (test 22),
   and produces a correct share string (tests 21, 23).
3. ✓ Mastery Dashboard reflects per-flaw accuracy across practice and daily play, persisted across
   reload (test 17, 24).
4. ✓ Vignette/explanation rendering uses `textContent` exclusively — confirmed no script execution via
   a live injected-payload test (test 28). All 28 tests pass with zero failures.
5. ✓ Reset control fully clears all three localStorage keys back to a fresh-install state (test 25).

Security checklist:
- No `.env` files
- No hardcoded credentials or personal data
- No `eval()`/`exec()` anywhere
- No `innerHTML` assignment from any dynamic/user-facing string — all dynamic text uses
  `textContent`/`.style.width`; DOM nodes built via `createElement`/`appendChild`
- No `subprocess`/`os.system` (no Python in this build)
- No file paths derived from user input
- All code self-contained in this build folder; no imports from other builds

### [08:31 UTC] Step 8 — Documentation
- `FutureFeatures.md`: 7 concrete enhancements
- `Manual.md`: how to run, how to play, data/privacy note

Build complete. Success criteria reviewed. All tests passing.
