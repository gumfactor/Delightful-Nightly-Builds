# Manual — Streakline

> **Version:** 1.0 (built 2026-08-31)
> **Complexity:** Ambitious Project

---

## What This Is

Streakline is a local, cross-domain habit and streak tracker. It confirms activity-based habits — running, golf, strength training — from a real Garmin Connect CSV export instead of asking you to log them by hand, and takes a manual check-in only for habits Garmin can't see (writing, or anything else you add). It computes real daily and weekly streak/consistency statistics and renders them as an interactive local dashboard. Nothing leaves your machine unless you explicitly opt into the AI coach note.

---

## Quick Start

1. `cd` into this folder and run `python3 main.py init` — creates `habits.json` (from `habits.example.json`) and the local database.
2. Edit `habits.json` to match your own habits (see below).
3. Export your activity history from Garmin Connect (garmin.com/connect → "Activities" → the CSV export option) and run:
   `python3 main.py import-garmin /path/to/Activities.csv`
4. Check in any manual-source habits: `python3 main.py checkin writing`
5. `python3 main.py render` — writes `dashboard.html`; open it in any browser.

---

## How to Use It

### `habits.json`

Each habit needs an `id` (used everywhere else on the command line), a `name` (display label), a `cadence` (`"daily"` or `"weekly"` — use `weekly` for anything that realistically isn't a daily activity, like golf), and a `source`:

- `"source": "garmin"` habits also need `garmin_activity_types`: a list of the *exact* strings Garmin uses for that activity (case-insensitive, but otherwise exact — not a substring match, so "Running" won't accidentally also match "Trail Running" unless you list both). Run `python3 main.py list-types your-export.csv` first to see exactly what strings your own export contains.
- `"source": "manual"` habits have no `garmin_activity_types` — you log them yourself with `checkin`.

### `import-garmin`

`python3 main.py import-garmin Activities.csv` reads a real Garmin Connect Activities export, matches each row against your configured Garmin-sourced habits, and records one completion per habit per day. Multiple matching activities on the same day (two runs, say) collapse into a single completion — streaks are about *did the habit happen that day*, not volume. Re-running an import (or importing an overlapping date range in a fresh export) never creates duplicates — already-recorded days are reported, not re-inserted. Unmatched activity types are listed at the end so you can add them to `habits.json` if you want them tracked.

### `checkin` / `remove`

`python3 main.py checkin writing` records today (UTC) as done for the `writing` habit. Add `--date YYYY-MM-DD` to log a different day, or `--note "..."` for a short note. `python3 main.py remove writing --date 2026-08-21` deletes a mistaken entry.

### `status`

A quick terminal table: current streak, longest streak, and 30-day completion rate per habit.

### `render`

Writes a self-contained `dashboard.html` — open it directly in a browser, no server needed. It shows hero stats, a per-habit calendar heatmap with a 30/90/180/365-day range toggle, a combined cross-habit heatmap, and a coach note. Click any day cell to see exactly what was recorded that day. Pass `--output path.html` to write somewhere else, or `--date YYYY-MM-DD` to treat a different day as "today" (mainly useful for checking historical snapshots).

### AI Coach Note

`python3 main.py render --ai` adds `--ai`, which — only if the `ANTHROPIC_API_KEY` environment variable is set — sends a small aggregate summary (habit names, cadence, current/longest streak, completion rate; never a date, a note, or a Garmin activity title) to Claude Haiku for one paragraph of behavioral observation. Without `--ai`, without a key, or if the request fails for any reason, the dashboard still gets a real, useful note — a deterministic template built from the same numbers. The tool never requires network access to be useful.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `habits.json` | created by `init` | Habit definitions — edit this to add/remove habits |
| `data/streakline.db` | created automatically | SQLite completion history — back this up if you care about the history |
| `--db PATH` | (unset) | Override the database path (mainly for scripting/testing) |
| `--habits PATH` | (unset) | Override the `habits.json` path (mainly for scripting/testing) |
| `ANTHROPIC_API_KEY` (env var) | unset | Only read when `render --ai` is passed |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "habits.json not found" | You haven't run `init` yet | `python3 main.py init` |
| A Garmin activity never gets matched | The `garmin_activity_types` string doesn't exactly match what Garmin exported | Run `list-types` on your export and copy the exact string |
| `import-garmin` reports 0 rows read | Wrong file, or Garmin changed its export header names | Open the CSV and confirm it has `Activity Type` and `Date` columns |
| A streak looks wrong right after midnight | `render`/`status` default to the current UTC date, which may not match your local "today" yet | Pass `--date` explicitly, or wait until UTC rolls over |

---

## Known Limitations

- **UTC-day convention.** "Today" for streak purposes is the current UTC calendar day, not your local (Eastern) day — the same convention this catalog's other date-based builds use. Near midnight Eastern, `status`/`render` without `--date` can be a few hours ahead of your local day. Pass `--date` explicitly if that matters for a specific check.
- **No live Garmin API.** This relies on a manual CSV export (Garmin's public API requires a separate paid developer agreement not listed in PROFILE.md's credentialed Data Sources). You'll need to re-export and re-import periodically to keep Garmin-sourced habits current.
- **Exact activity-type matching.** If Garmin renames or adds a new activity type your `habits.json` doesn't list, it shows up as "unmatched" rather than being silently guessed at — intentional, but it does mean occasional config upkeep.
