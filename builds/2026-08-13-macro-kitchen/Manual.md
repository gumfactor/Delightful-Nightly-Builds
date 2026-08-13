# Manual — Macro Kitchen

> **Version:** 1.0 (built 2026-08-13)
> **Complexity:** Ambitious Project

---

## What This Is

Macro Kitchen turns your real body stats — and, optionally, a real week of Garmin
training data — into a 7-day meal plan and grocery list that actually hits a
calorie and macro target, instead of eyeballing portions against a generic
"2000 kcal" template. Set your profile once, optionally import a Garmin Connect
activity export, and run `generate` to get a full week of meals from a curated
54-recipe bank, sized to your numbers via portion scaling. `render` turns any
saved plan into a self-contained HTML dashboard you can open in a browser.

---

## Quick Start

1. `cd builds/2026-08-13-macro-kitchen`
2. Set your profile:
   ```
   python3 src/main.py profile set --sex male --age 38 --height-cm 178 \
     --weight-kg 76 --activity-level moderate --goal maintain --goal-rate 0
   ```
3. (Optional) Import a real Garmin Connect Activities CSV export — or try the bundled sample:
   ```
   python3 src/main.py import-garmin sample_data/sample_garmin_activities.csv
   ```
4. Generate a plan:
   ```
   python3 src/main.py generate
   ```
5. Render the dashboard and open it in a browser:
   ```
   python3 src/main.py render
   open data/dashboard.html   # or double-click it in a file browser
   ```

---

## How to Use It

### Setting your profile

```
python3 src/main.py profile set \
  --sex male|female \
  --age <years> \
  --height-cm <height> \
  --weight-kg <weight> \
  --activity-level sedentary|light|moderate|active|very_active \
  --goal lose|maintain|gain \
  --goal-rate <kg/week, only matters for lose/gain>
```

This computes your BMR (Mifflin-St Jeor formula) and TDEE, then applies your
goal's calorie deficit/surplus (capped so it never drops below a safe floor
just above your BMR). Re-running `profile set` overwrites the single stored
profile — there's no multi-user support.

### Importing real training data

```
python3 src/main.py import-garmin <path-to-garmin-activities.csv>
```

Export your data from Garmin Connect: go to your Activities list on
connect.garmin.com, select the activities you want (or use the bulk export),
and choose "Export CSV." The parser reads the `Date` and `Calories` columns
(required) and `Distance`/`Time` if present, and computes the most recent
7-day window relative to the latest activity date in the file — not
"today," so a CSV export from last month still works correctly.

Half of your logged calorie burn over that week becomes an extra daily
eating budget (Garmin's "Calories" already reflects your baseline metabolism
during the activity, which your TDEE already covers — so only the *net
additional* burn should raise your target). The adjustment is capped at 900
kcal/day so one huge outlier activity can't produce an unrealistic target.

If the CSV is missing required columns or can't be found, `import-garmin`
prints a warning and records a zero adjustment — it never crashes.

### Generating a plan

```
python3 src/main.py generate [--diet TAG] [--exclude TAG] [--ai-notes] [--no-garmin]
```

- `--diet TAG`: only use recipes with this tag (`vegetarian`, `vegan`, `gluten_free`, `dairy_free`, `high_protein`, `quick`)
- `--exclude TAG`: only use recipes *without* this tag
- `--ai-notes`: adds a one-sentence "chef's note" per day. Uses Claude Haiku if `ANTHROPIC_API_KEY` is set in your environment; otherwise a deterministic template runs instead — either way, no body stats are ever sent, only the day's aggregate macro numbers
- `--no-garmin`: ignore any imported Garmin data for this run, using only your profile's base target

Every `generate` call creates a new plan (never overwrites a previous one), so
your plan history is preserved. If a filter combination leaves too few
recipes to fill a slot (e.g. `--diet vegan --exclude dairy_free`, which
excludes every vegan recipe since they're all also dairy-free), you'll get a
clear error instead of a broken or infinite-loop plan.

Recipes are single realistic servings; if your calorie target is higher than
one serving of everything in a day provides, the planner scales up the
portion size (0.75x-2.0x) on the recipes it picks — shown in `show` and the
dashboard as e.g. "(1.5x portion)."

### Viewing and using a plan

```
python3 src/main.py list                 # all saved plans, newest first
python3 src/main.py show <plan_id>       # full day-by-day breakdown in the terminal
python3 src/main.py grocery <plan_id>    # aggregated shopping list
python3 src/main.py render [<plan_id>]   # self-contained HTML dashboard (defaults to latest)
```

`render` writes to `data/dashboard.html` by default; pass `--out <path>` to
write elsewhere.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ANTHROPIC_API_KEY` (env var) | unset | Enables real Claude Haiku chef's notes with `--ai-notes`; falls back to a deterministic template when unset |
| `--out` (render) | `data/dashboard.html` | Where the HTML dashboard is written |
| Database location | `data/macro_kitchen.db` | Created automatically on first run; not committed to git |

No configuration file — everything is a CLI flag or stored in the local SQLite database.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: no profile set. Run 'profile set' first.` | `generate` was run before `profile set` | Run `profile set` with your stats first |
| `Error: Not enough recipes for slot 'X' after filtering` | Your `--diet`/`--exclude` combination leaves fewer than 2 recipes for some meal slot | Loosen the filter, or check `src/recipes.py` for what's actually tagged that way |
| `Warning: CSV is missing required column(s) ['Calories']` | Your Garmin export doesn't include a `Calories` column | Re-export from Garmin Connect with default columns, or manually add a `Calories` column |
| Dashboard shows unexpected high/low targets after `import-garmin` | The activity window is relative to the *latest date in your CSV*, not today | Re-export a fresh CSV if your last export is stale |

---

## Known Limitations

- Garmin CSV distance is assumed to be in kilometers (Garmin's export format depends on your account's unit settings) — see FutureFeatures.md for a planned `--units` flag.
- The grocery list doesn't merge the same ingredient across different units (e.g. "milk / ml" and a hypothetical "milk / cup" stay separate line items) — this is intentional (no unit-conversion guessing) but means you should scan the whole list for an ingredient, not just one entry.
- The 54-recipe bank is hand-curated, not sourced from a live nutrition database — treat the macro figures as reasonable estimates, not lab-verified values.
- Single-profile only; there's no support for planning for more than one person in the same household.
