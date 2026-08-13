# PRD — Macro Kitchen

> **Build date:** 2026-08-13
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious Project
> **Day of week:** Thursday

---

## Goal

A Python CLI that computes real calorie/macro targets from a Mifflin-St Jeor body-stats profile (optionally adjusted by a real Garmin Connect activity export), deterministically builds a 7-day meal plan from a curated recipe bank that hits those targets, and renders a printable HTML dashboard with a per-day macro breakdown and an aggregated grocery list.

## User Story

As a distance runner and golfer who tracks training in Garmin Connect and cares about evidence-driven decisions, I want a meal plan generator that actually accounts for my real training load and body stats instead of a generic 2000-kcal template, so that I stop manually eyeballing portion sizes and get a grocery list that matches a week of food that hits my numbers.

## Scope

### In Scope
- `profile set`: store body stats (sex, age, height_cm, weight_kg, activity_level, goal: lose/maintain/gain, goal_rate_kg_per_week) in local SQLite
- Deterministic Mifflin-St Jeor BMR → TDEE → goal-adjusted daily calorie target, with a 4-macro split (protein/carbs/fat/fiber floor) derived from body weight and goal
- `import-garmin <csv>`: parse a real Garmin Connect "Activities" CSV export (Date, Activity Type, Distance, Calories columns), compute the most recent 7-day training load, and apply an activity-adjustment on top of the base TDEE (extra kcal burned, averaged and capped) — optional; the tool is fully functional on body stats alone if no CSV is supplied
- A curated, hand-written recipe bank (≥48 recipes across breakfast/lunch/dinner/snack) with per-recipe calories/protein/carbs/fat, prep minutes, dietary tags (vegetarian, vegan, gluten_free, dairy_free, high_protein, quick), and an ingredient list (name, qty, unit)
- `generate [--diet TAG] [--exclude TAG]`: deterministic constrained meal-plan builder that picks 4 meals/day for 7 days, minimizing deviation from the day's calorie/protein targets within a tolerance band, respecting dietary filters and a no-repeat-within-3-days rule per slot, persisted to SQLite as a new plan version (plans are never overwritten)
- `list` / `show <id>`: list saved plans / show one plan's full daily breakdown in the terminal
- `grocery <id>`: aggregate every ingredient across a plan's 28 meals into a single shopping list, grouped and summed by (ingredient, unit)
- `render [<id>]`: self-contained dark-mode HTML dashboard — target vs. actual macro bars per day, a 7-day calorie line (hand-drawn Canvas 2D, no library dependency), full recipe cards, and the grocery list — defaults to the most recent plan
- Optional `--ai-notes` flag on `generate`: one Claude Haiku–generated "chef's note" per day (variety/prep tip, aggregate macro numbers only, never personal body stats) with an unconditional deterministic template fallback when `ANTHROPIC_API_KEY` is unset or the call fails

### Out of Scope
- Live grocery-price lookups or ordering integration
- Barcode/nutrition-label scanning
- MyFitnessPal API integration (no credentials in PROFILE.md's Data Sources for it)
- Multi-user profiles (single local profile only)
- Automatic Garmin Connect API sync (Garmin's API is not in PROFILE.md's Data Sources; the CSV export path is the sanctioned local-file route)

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `csv`, `urllib` for the optional Anthropic call). See `requirements.txt` (empty — stdlib only).
- **Runtime requirement:** `python3 src/main.py <command> ...` — no install needed

## Data Structure

SQLite database at `builds/2026-08-13-macro-kitchen/data/macro_kitchen.db` (created on first run):

```
profile(id INTEGER PK, sex TEXT, age INTEGER, height_cm REAL, weight_kg REAL,
        activity_level TEXT, goal TEXT, goal_rate_kg_per_week REAL, updated_at TEXT)

garmin_import(id INTEGER PK, imported_at TEXT, window_start TEXT, window_end TEXT,
              total_distance_km REAL, total_duration_min REAL, total_calories REAL,
              activity_count INTEGER, daily_adjustment_kcal REAL)

plans(id INTEGER PK, created_at TEXT, target_calories REAL, target_protein_g REAL,
      target_carbs_g REAL, target_fat_g REAL, diet_filter TEXT, exclude_filter TEXT,
      used_garmin_import_id INTEGER NULL, ai_notes_used INTEGER)

plan_meals(id INTEGER PK, plan_id INTEGER FK, day_index INTEGER (0-6), slot TEXT
           (breakfast/lunch/dinner/snack), recipe_id TEXT, portion_multiplier REAL,
           day_note TEXT NULL)
```

`portion_multiplier` (added mid-build — see BUILD_LOG.md): recipes are written as
single realistic servings, so the planner scales the chosen recipe's serving size
(0.75x-2.0x) to close the gap between what a single serving provides and a higher
calorie target, the same way a person would eat a bigger portion rather than add a
5th meal slot.

Recipe bank is a static Python data module (`src/recipes.py`), not a DB table — it's curated content, not user data.

## Folder Structure

```
builds/2026-08-13-macro-kitchen/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── data/                     (created at runtime, gitignored via .gitkeep note in Manual.md)
├── src/
│   ├── main.py                (CLI entry point / argument parsing / command dispatch)
│   ├── nutrition.py            (BMR/TDEE/macro-target math — pure functions)
│   ├── garmin_import.py        (CSV parsing + activity-load aggregation)
│   ├── recipes.py               (curated recipe bank, 48+ entries)
│   ├── planner.py               (deterministic constrained meal-plan builder)
│   ├── grocery.py               (ingredient aggregation)
│   ├── storage.py               (SQLite schema + CRUD)
│   ├── ai_notes.py              (optional Claude Haiku chef's-note call + deterministic fallback)
│   └── render.py                (self-contained HTML dashboard renderer)
├── sample_data/
│   └── sample_garmin_activities.csv   (fixture used by tests and available for manual trial)
└── tests/
    ├── test_nutrition.py
    ├── test_garmin_import.py
    ├── test_planner.py
    ├── test_grocery.py
    ├── test_storage.py
    ├── test_ai_notes.py
    └── test_render.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Mifflin-St Jeor BMR formula against hand-verified reference values (male and female)
  - TDEE activity-multiplier lookup and goal-rate calorie adjustment (deficit/surplus math, including the safety floor that refuses to drop below BMR)
  - Macro split math sums back to the target calorie figure (kcal-from-macros round-trip within rounding tolerance)
  - Garmin CSV parsing: correct row filtering to the most recent 7-day window, correct aggregation, and a malformed/missing-column CSV that degrades gracefully (skips the file with a warning, never crashes)
  - Activity-adjustment capping (adjustment never pushes the target absurdly high)
  - Recipe bank integrity: every recipe has all required fields and non-negative macro values (data-quality guard, not just logic)
  - Deterministic planner: generated plan always has exactly 28 meals (7 days × 4 slots), respects a dietary-tag filter (zero non-matching recipes in output), respects the no-repeat-within-3-days rule, and raises a clear error rather than an infinite loop when a filter leaves too few recipes to fill the week
  - Planner determinism: same inputs (profile + filters + fixed recipe bank) produce the same plan — no hidden randomness
  - Grocery aggregation: two meals using the same ingredient in the same unit sum correctly; different units for the same ingredient are kept as separate line items (documented limitation, not silently wrong)
  - SQLite storage round-trip: save a plan, reload it, fields match; multiple `generate` calls create new plan versions rather than overwriting
  - AI notes: mocked Anthropic call returns expected note text; missing `ANTHROPIC_API_KEY` makes zero network calls and produces the deterministic template instead (verified via a patched `urlopen` call-count assertion)
  - HTML render: output is valid self-contained HTML, embeds plan data as escaped JSON, and a script-injection payload placed in a manually-added custom recipe name (edge case injected directly into storage) renders as inert text, not executed markup

## Success Criteria

1. All tests pass (zero failures)
2. `generate` on a stored profile always produces a complete, valid 7-day/28-meal plan whose daily calorie total falls within ±10% of the computed target on every day
3. `import-garmin` correctly computes a 7-day activity load from the bundled sample CSV and demonstrably shifts the calorie target compared to a run with no import
4. `grocery` produces a correctly aggregated, non-empty shopping list for any generated plan
5. `render` produces a self-contained HTML file that opens directly in a browser with zero external dependencies required and correctly escapes all embedded data

---

## Scope Changes

Added a `portion_multiplier` dimension to the planner mid-build (see BUILD_LOG.md,
"Build Phase — Planner tolerance bug"): the original single-serving-only design
couldn't reach realistic higher-calorie targets (an active adult easily needs
2800-3200 kcal/day, but the recipe bank's single-serving max across 4 meals tops
out around 1880 kcal). This wasn't a reduction in scope — it made the tool
correctly handle the exact target range PROFILE.md's fitness-focused user would
actually need.
