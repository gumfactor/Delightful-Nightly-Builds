# Build Log — Streakline

> **Date:** 2026-08-31
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:15 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for an incomplete build. Local `builds/` only goes up to 2026-06-18 (Regex Dojo, complete). This repo's ~30 open nightly-build PRs have never merged to `main`, so local `main` is stale; per CLAUDE.md Step 1, resynced from the most recently created open PR (#85, branch `claude/cool-sagan-tbm8u0`, 2026-08-30 "Layer Guard"). Its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed.
- Category rotation: day-of-year 243 → `(243-1) % 9 = 8` → **I — Life Admin Helper**.
- `builds/ideas.md` (resynced from the same branch) had 2 pending Category I rows, both unrated → 25% lottery chance. Rolled 24/100 → lottery draw. Weighted pick (5/5 tickets) rolled 2/10 → idea #24, **Cross-Domain Habit Log**. Marked `built` in `builds/ideas.md`.
- Decided to build: **Streakline** — cross-domain habit/streak tracker combining Garmin Connect CSV import (running/golf/strength) with manual check-in (writing).
- Build folder created: `builds/2026-08-31-streakline/`.

### [08:20 UTC] PRD Written

- Goal: local habit/streak tracker with real Garmin CSV import + manual check-in + daily/weekly streak engine + interactive HTML dashboard.
- Scope: `import-garmin`, `list-types`, `checkin`, `remove`, `status`, `render`, optional Claude Haiku coach note with deterministic fallback.
- Notable decision: two cadences (`daily`/`weekly`) rather than forcing every habit into a daily streak — golf realistically isn't a daily habit, and the idea's own scope names it explicitly.

### [08:35 UTC] Build Phase — Engine and DB

- `src/streaks.py`: pure functions, no I/O — `daily_streak()`, `weekly_streak()`, `completion_rate()`. Grace-period logic: a daily streak counts as "current" through the day after the last completion (today not yet logged doesn't reset it), but breaks once a full day has passed with nothing logged. Same grace concept ported to weekly cadence using ISO week numbers. Deliberately takes an explicit `as_of` parameter rather than calling `datetime.now()` internally, so the whole engine stays a pure, trivially testable function.
- `src/db.py`: SQLite with a `UNIQUE(habit_id, date)` constraint; `add_completion()` returns `False` (not an error) when a row for that habit/day already exists, so both idempotent Garmin re-import and an accidental duplicate manual check-in degrade gracefully.
- `src/garmin_import.py`: `csv.DictReader` over the real Garmin Connect "Activities" export headers (`Activity Type`, `Date`, `Title`). Matching is exact (case-insensitive) against each habit's configured `garmin_activity_types` list rather than substring matching, to avoid false positives like "Running" matching "Trail Running" when only one of the two was intended. Malformed rows (missing type/date, unparseable date, missing required columns, empty file) are collected into a `warnings` list and skipped rather than raising. Added `list-types` specifically because exact-match config is only usable if the user can see the real strings Garmin exports.

### [09:00 UTC] Build Phase — CLI and Dashboard

- `main.py`: argparse subcommands (`init`, `import-garmin`, `list-types`, `checkin`, `remove`, `status`, `render`), following this catalog's established root-`main.py` + `src/`-package layout (confirmed against the local 2026-06-10 Investment Research Platform build's structure and test-import pattern).
- `src/render.py`: self-contained dark-mode HTML. Data delivered as an `application/json` script tag with `</` escaped to prevent premature tag termination; DOM built via `createElement`/`textContent` only, never `innerHTML` with untrusted data. Per-habit heatmap cards plus a combined cross-habit view; a client-side 30/90/180/365-day range toggle re-slices the already-embedded JSON rather than re-fetching anything. Clicking a day cell shows a detail panel with exactly what was recorded that day, per habit.
- `src/coach.py`: optional Claude Haiku call via `urllib.request` (`claude-haiku-4-5-20251001`), sending only a list of `{name, cadence, current_streak, longest_streak, completion_rate}` per habit — never a date, note, or Garmin activity title. Unconditional deterministic-template fallback on any exception, empty response, or missing `ANTHROPIC_API_KEY`.
- Added a `--habits` override flag alongside the existing `--db` override on every subcommand, mirroring the same "mainly for tests/scripting" pattern, so the build folder's own committed `habits.json` never has to exist for manual verification against a scratch config.

### [09:35 UTC] Tests Written and Run

- 51 tests across `test_streaks.py` (18), `test_db.py` (9), `test_garmin_import.py` (11), `test_coach.py` (7), `test_render.py` (6).
- Build environment note: `python3 -m pytest` fails here (`No module named pytest`) because this container's pytest was installed via `uv tool install` into an isolated interpreter, not the default `python3`. Ran the suite with `/root/.local/bin/pytest tests/ -v` instead — a build-container path quirk only (same category of issue as the Playwright-chromium-path fix noted in the 2026-06-18 Regex Dojo build log), not a code or design problem. The user's own machine, with `pip install -r requirements.txt`, should run the documented `python -m pytest tests/ -v` normally.
- First run: **51 passed, 0 failed** — no fixes needed.

[09:35 UTC] Tests: 51 passed, 0 failed.

### [09:45 UTC] Manual Verification

Ran the real CLI (not just the test suite) against `fixtures/sample_garmin_activities.csv` (21 synthetic rows — running/golf/strength plus 2 unmatched "Cycling" rows) using a scratch DB and a scratch copy of `habits.example.json` outside the build folder (via the new `--db`/`--habits` overrides), so no runtime data was ever written into the committed build folder:

- `import-garmin`: "Read 21 rows, matched 19. Inserted 19 new completion(s); 0 already recorded." Unmatched type correctly reported: `Cycling`.
- Re-running the identical `import-garmin`: "Read 21 rows, matched 19. Inserted 0 new completion(s); 19 already recorded." — idempotency confirmed against a real DB file, not a mock.
- `checkin writing --date 2026-08-21` then the identical command again: second call correctly reported "already recorded" rather than erroring or duplicating.
- `status --date 2026-08-24` (the day after the fixture's last real activity row): `Running 0/4 current/longest`, `Golf 5/5`, `Strength Training 0/1`, `Writing 0/0` — hand-checked against the fixture CSV by counting consecutive dates directly; matched.
- `list-types`: correctly printed the 4 distinct activity types present in the fixture (`Cycling, Golf, Running, Strength Training`).
- `remove writing --date 2026-08-21`: correctly reported removal; a second `remove` of the same day correctly reported nothing to remove.
- **Zero-network confirmation:** ran `render --ai` with `ANTHROPIC_API_KEY` unset and `urllib.request.urlopen` monkey-patched at the real module level to raise `AssertionError` if ever invoked. The render completed successfully with no exception — the deterministic coach note was used end-to-end through the actual CLI, not a test mock.
- **Live browser QA** (checked in a hostile manual note first — `</script><script>window.__xss=true;</script>` on the `writing` habit for 2026-08-23 — then re-rendered) via the container's pre-installed headless Chromium (global npm Playwright 1.56.1, `chromium-1194`): zero page errors, zero console errors, zero dialogs; `window.__xss` stayed `undefined`; exactly 2 `<script>` tags on the page (the JSON payload + the interaction logic — no injected third tag); the 30/90/180/365 range buttons produced exactly 30/90/365 rendered day cells respectively (verified by counting DOM nodes, not just visually); clicking the exact day cell carrying the hostile note showed it in the detail panel as literal text (`Writing — manual: </script><script>window.__xss=true;</script>`) with no script execution; zero horizontal overflow at a 375px mobile viewport.

### [10:05 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions across quick wins, medium effort, and ambitious extensions.
- `Manual.md`: quick start, `habits.json` field reference, all seven CLI commands/flags, configuration table, troubleshooting table, and the UTC-day convention called out explicitly as a known limitation.

### [10:10 UTC] Verify — Step 7

Security checklist run against every created file:
- No `.env` files, no hardcoded credentials/keys/personal data (the shipped fixture CSV is synthetic, invented for this build, not a real export).
- No `eval()`/`exec()`; no `os.system()`/`subprocess` calls anywhere in this build.
- No `innerHTML` assignment with untrusted data — `render.py`'s JS builds the DOM via `createElement`/`textContent` exclusively (the only `.innerHTML = ''` calls clear a container to an empty string, never assign content); the one JSON payload is escaped against `</script>` injection, confirmed live above.
- No file paths built from anything but the user's own explicit command-line arguments (a local single-user CLI, same trust boundary as every prior CLI build in this catalog).
- All files confined to `builds/2026-08-31-streakline/`; no import from another build's folder.

Success criteria reviewed against `PRD.md`:
1. All tests pass, zero failures, 51 tests (minimum 15 required) — met.
2. `import-garmin` against the fixture correctly matched/deduped/was idempotent — met, verified live above, not just via mocks.
3. Streak engine numbers matched hand-computed values for both daily and weekly cadence — met.
4. `render` output is XSS-safe and the range toggle genuinely re-slices client-side — met, verified live in headless Chromium.
5. AI coach note sends only aggregate numbers and makes zero network calls with no API key — met, verified live with a real monkey-patched `urlopen` guard, not just a test mock.

Build complete. Success criteria reviewed. All tests passing.
