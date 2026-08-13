# Build Log — Macro Kitchen

> **Date:** 2026-08-13
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for incomplete builds. Local dated folders only go up to 2026-06-18-regex-dojo; its BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed.
- Step 1: resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-hado2r`, PR #69, 2026-08-12) since local `main` was far behind (19 builds vs. 62 actually completed). Confirmed via `mcp__github__list_pull_requests`.
- Day of year 225 → category_index = (225-1) % 9 = 8 → Category I — Life Admin Helper.
- Category I backlog in `builds/ideas.md` had zero pending rows → skipped lottery, went to fresh idea generation.
- Scanned last 10 builds for topic saturation and the 6 prior Category I builds for topic coverage (see WhyThis.md). Chose a Garmin-CSV-aware meal/macro planner ("Macro Kitchen") — the one named category example (meal planner) with zero prior coverage.
- Build folder created: `builds/2026-08-13-macro-kitchen/`

### [00:20 UTC] PRD Written

- Goal: Python CLI that computes real calorie/macro targets (Mifflin-St Jeor + optional Garmin CSV activity adjustment), deterministically builds a 7-day plan from a curated recipe bank, renders an HTML dashboard + grocery list.
- Scope: profile management, Garmin CSV import, deterministic constrained meal planner, grocery aggregation, SQLite persistence, optional Claude Haiku chef's notes with deterministic fallback, self-contained HTML dashboard.
- Key decision: recipe content is curated static data (like Confound Hunter/Lexicon precedent), not a live API — the "real data" layer is the optional Garmin CSV import and the user's own body-stat profile, following the "Local-only... file-based data (CSV exports...)" data source PROFILE.md explicitly sanctions.

### [01:10 UTC] Build Phase — Core nutrition math and recipe bank

- Implemented `src/nutrition.py`: Mifflin-St Jeor BMR, activity-multiplier TDEE, goal-rate calorie adjustment with a BMR safety floor, and a macro split (protein by body weight, fat by % of calories, carbs as remainder, fiber floor).
- Implemented `src/recipes.py`: 52 curated recipes (14 breakfast, 14 lunch, 14 dinner, 10 snack) with full macro data, prep time, dietary tags, and ingredient lists.
- Implemented `src/garmin_import.py`: CSV parser for Garmin Connect's "Activities" export column layout, 7-day recency window filter, aggregation, and an activity-adjustment formula capped at a sane ceiling.

### [01:45 UTC] Build Phase — Planner, grocery, storage

- Implemented `src/planner.py`: deterministic greedy-with-backtrack meal selection per day/slot that minimizes squared deviation from remaining daily macro budget, filters by dietary tag/exclusion, and enforces a no-repeat-within-3-days rule per slot. Raises a clear `PlannerError` (not an infinite loop) when a filtered recipe pool is too small.
- Implemented `src/grocery.py`: aggregates ingredients by (name, unit) across all 28 meals in a plan.
- Implemented `src/storage.py`: SQLite schema for profile/garmin_import/plans/plan_meals with round-trip save/load; `generate` always inserts a new plan row rather than overwriting.

### [02:15 UTC] Build Phase — AI notes, render, CLI

- Implemented `src/ai_notes.py`: optional Claude Haiku call (aggregate macro numbers only, never body stats) via `urllib`, with an unconditional deterministic template fallback when `ANTHROPIC_API_KEY` is unset or the call raises.
- Implemented `src/render.py`: self-contained dark-mode HTML dashboard, plan data embedded as JSON-escaped-for-`<script>` (learned from the Manuscript Pipeline build's documented `html.escape()`-vs-JSON-in-`<script>` bug — used the correct escaping here), hand-drawn Canvas 2D 7-day calorie line, per-day macro bars, recipe cards, grocery list.
- Implemented `src/main.py`: CLI dispatch for `profile`, `import-garmin`, `generate`, `list`, `show`, `grocery`, `render`.
- Built `sample_data/sample_garmin_activities.csv` as a realistic fixture (14 running/golf activities across 3 weeks) for tests and manual trial.

### [02:40 UTC] Tests Run — first pass

Tests: 57 passed, 4 failed.

Three of the four failures were real: `test_generate_plan_respects_exclude_filter` (the snack slot had zero recipes without the `gluten_free` tag after filtering — a genuine recipe-bank diversity gap, not a test bug) and `test_daily_totals_within_reasonable_tolerance_of_target` (every day landed 25-30% under target — the recipe bank's single-serving max across 4 meals tops out around 1880 kcal, which can't reach a realistic active-adult target of 2600+ kcal). The fourth (`test_prompt_never_includes_body_stats`) and one render test were test-authoring bugs (a naive substring check on "age" matched "message"; the injection test only expected one of two `</` occurrences to be escaped).

### [03:10 UTC] Build Phase — Planner tolerance bug fix

Root-caused the calorie-tolerance failure: recipes are single realistic servings, so a target above ~1880 kcal/day was structurally unreachable no matter which recipes the planner picked. Fixed by adding a `portion_multiplier` dimension (0.75x-2.0x) to the planner's search — it now searches (recipe × multiplier) pairs per slot instead of just recipes, which is also how a real person actually hits a higher calorie target (bigger portions, not more meals). Threaded `portion_multiplier` through `plan_day_totals`, `grocery.aggregate_grocery_list` (ingredient quantities now scale with portion size), `storage` (new column), `render.py` (displays "1.5x portion" next to a scaled meal), and `main.py`'s `show` command. Added two new snack recipes (`s11` whole-grain crackers, `s12` granola bar) that aren't tagged `gluten_free`, fixing the exclude-filter diversity gap. Fixed the two flawed tests. Updated PRD.md's Data Structure and added a Scope Changes entry documenting this.

### [03:25 UTC] Tests Run — after fix

Tests: 62 passed, 0 failed.

### [03:35 UTC] Manual Verification

- Ran the full CLI flow end-to-end against the bundled sample data: `profile set` → `generate --no-garmin` (2615.6 kcal target) → `import-garmin sample_data/sample_garmin_activities.csv` (6 activities in the most recent 7-day window, +247.5 kcal/day adjustment) → `generate --ai-notes` (2863.1 kcal target, confirmed higher than the no-import run) → `list` → `show` → `grocery` → `render`.
- Confirmed the AI-notes path used the deterministic template (no `ANTHROPIC_API_KEY` set in this session) and made zero network calls, matching `test_no_api_key_makes_zero_network_calls`.
- Confirmed `import-garmin` against a deliberately malformed CSV (missing `Calories` column) degrades to a warning and a zero-adjustment result instead of crashing.
- Loaded the rendered dashboard live in headless Chromium (`/opt/pw-browsers/chromium-1194`): zero page errors, zero dialogs, 4 stat tiles / 7 day cards / 40 grocery items rendered correctly.
- Manually inserted a `</script><script>alert(1)</script>` payload as a plan's stored day-note directly via SQLite and re-rendered — confirmed via both a string check and a live headless-Chromium load (zero dialogs fired) that the payload renders as inert escaped text, never executable markup.

### [03:00 UTC] Verify — Step 7 success criteria check

1. ✓ All tests pass (62 passed, 0 failed)
2. ✓ `generate` always produces 28 meals across 7 days; verified daily calorie totals within ±10% of target on the sample profile (test + manual run)
3. ✓ `import-garmin` computes a real 7-day load from the sample CSV and measurably shifts the target vs. a no-import run (test + manual run)
4. ✓ `grocery` produces a non-empty, correctly aggregated shopping list (test + manual run)
5. ✓ `render` produces a self-contained HTML file, opens with no external dependencies, and correctly escapes embedded data (manual injection test)

Security checklist:
- No `.env` files committed
- No hardcoded credentials/personal data (sample CSV uses invented activity data, no real name/location)
- No `eval()`/`exec()` anywhere
- No `innerHTML` from user-controlled data — render.py builds the DOM via `textContent`/`createElement` and embeds data as JSON-escaped-for-`<script>`, not string-concatenated HTML
- No `subprocess`/`os.system()` calls at all
- No file paths built from unsanitized user input (CSV path comes from an explicit CLI argument, opened directly, no path traversal construction)
- All files confined to `builds/2026-08-13-macro-kitchen/`

### [03:05 UTC] Documentation

- FutureFeatures.md: 7 concrete suggestions
- Manual.md: quick start, full command reference, configuration, troubleshooting, known limitations

Build complete. Success criteria reviewed. All tests passing.
