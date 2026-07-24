# Build Log — Heuristic Hunt

> **Date:** 2026-07-24
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:10 UTC] Session Start

- Checked for interrupted builds: last dated folder was 2026-06-18-regex-dojo locally, and the most recent open PR (#49, branch `claude/cool-sagan-psb5dt`, 2026-07-22) has a `BUILD_LOG.md` ending in "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Read PROFILE.md, STANDARDS.md, and the current `builds/index.md` (synced from PR #49, the most recently opened open-PR branch, per Step 1's orientation instructions).
- Day of year for 2026-07-24 is 205 → `category_index = (205-1) % 9 = 6` → Category G — Game/Puzzle.
- Ran the lottery: 2 pending backlog ideas matched category G (#11, #12), both blank-rated → R=0 → lottery_chance = 25%. Rolled 89 (>25) → fresh idea generation.
- Scanned last 10 builds for topic saturation: no domain repeats more than twice; investment/finance absent from the window entirely.
- Decided to build: Heuristic Hunt — a cognitive-bias identification vignette game.
- Build folder created: builds/2026-07-24-heuristic-hunt/

### [08:25 UTC] PRD Written

- Goal: multiple-choice vignette game teaching recognition of 12 cognitive biases across 3 chapters, a daily challenge, practice mode, and a mastery dashboard.
- Scope: 30 hand-authored vignettes, chapter-gated unlocking at 70% accuracy, date-seeded Daily Challenge, per-bias Mastery Dashboard, localStorage persistence.
- Notable constraints: no ES modules (classic scripts under a single `HH` namespace so the build opens directly via `file://`), no external dependencies needed.

### [08:40 UTC] Build Phase — Data Layer

- Authored `src/data.js`: 12-bias taxonomy plus 30 vignettes (10 per chapter), each with a correct bias, 3 distractor biases chosen for plausible confusion, and a teaching explanation.
- Authored `src/storage.js`: localStorage read/write helpers with a versioned key (`heuristicHunt_v1`) and safe JSON parsing (corrupt/missing state falls back to a fresh default object rather than throwing).
- Authored `src/daily.js`: a deterministic, non-`Math.random` seeded PRNG (mulberry32) keyed off the UTC date string, used to pick 5 vignettes for the Daily Challenge so every player sees the same 5 questions on the same UTC date.

### [09:10 UTC] Build Phase — App Logic & UI

- Authored `src/app.js`: view routing (menu, chapter select, question, chapter-complete, daily challenge, daily result, practice, mastery dashboard), answer shuffling, scoring, chapter-unlock gating, and localStorage read/write wiring.
- Authored `index.html` and `src/styles.css`: dark-mode-first responsive layout, mastery bars color-coded green/yellow/red/gray, mobile breakpoint at 480px.

### [09:30 UTC] Tests Written

- Authored `tests/heuristic-hunt.spec.js` (22 tests) covering data integrity, chapter gating/unlocking and persistence, correct/incorrect answer feedback, Daily Challenge determinism and once-per-day gating (via `page.addInitScript` Date override), practice mode, mastery dashboard accuracy, reset progress, console-error-free playthrough, mobile viewport layout, and corrupt-localStorage recovery.
- Added a local `package.json` pinning `@playwright/test@1.56.1` (global `playwright` package doesn't expose the `@playwright/test` module path) and set `executablePath` in `playwright.config.js` to `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, matching the Chromium build actually installed in this container (Playwright 1.56.1 expects build 1228; same fix Regex Dojo needed on 2026-06-18).

### [09:45 UTC] Tests Run — First Pass

Tests: 20 passed, 2 failed.
- Failure 1: chapter-complete unlock message didn't include the actual accuracy score, so the "below 70%" test's assertion on the score string failed. Fixed by making the message include the computed accuracy percentage (`app.js`), which also makes the in-game copy more informative.
- Failure 2: the reset-progress test answered only 1 question in a bias-specific practice session and then waited for the practice-complete screen, but the "anchoring" bias has 3 vignettes, so the session wasn't finished yet. Fixed the test to loop through the full vignette count for that bias before expecting the complete screen.
- Also caught and fixed a copy-paste typo in the below-70%-accuracy test: the scenario answers 6/10 wrong and 4/10 right (40% accuracy), but the assertion checked for "60%" in the message. Corrected to "40%".

### [09:50 UTC] Tests Run — Second Pass

Tests: 22 passed, 0 failed.

### [09:52 UTC] Verify — Step 7

- Took Playwright screenshots of the main menu and an in-progress Chapter 1 question to visually confirm layout, contrast, and content rendering beyond what the automated assertions check. Both rendered cleanly.
- Ran the STANDARDS.md security checklist via grep across all created files: no `.env`, no hardcoded secrets, no `eval`/`exec`, no `innerHTML` from user-controlled data (all vignette/explanation text is static, author-controlled, and inserted via `textContent`), no `subprocess`/`os.system` calls, no file-path handling of any kind (pure client-side game), everything self-contained in the build folder. Clean.
- All 5 PRD success criteria checked against the working build (see PRD.md) — all met.

### [10:00 UTC] Documentation

- FutureFeatures.md: 7 concrete suggestions.
- Manual.md: usage guide, mode descriptions, bias taxonomy reference table, test command.

Build complete. Success criteria reviewed. All tests passing.
