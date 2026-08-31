# PRD — Streakline

> **Build date:** 2026-08-31
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious Project
> **Day of week:** Monday → every build is ambitious per CLAUDE.md calibration note

---

## Goal

A local, cross-domain habit/streak tracker that auto-confirms activity-based habits (running, golf, strength training) from a real Garmin Connect CSV export while accepting manual check-ins for habits with no external data source (writing), computing genuine daily/weekly streak and consistency statistics, and rendering an interactive HTML dashboard.

## User Story

As a mid-career researcher and founder who runs, plays golf, strength-trains, and writes but tracks none of it in one place, I want a single tool that pulls real activity confirmation from the Garmin Connect data I already export and lets me log the habits Garmin can't see, so that I can see genuine cross-domain consistency (and where it's slipping) without opening four different apps or maintaining a spreadsheet by hand.

## Scope

### In Scope
- `habits.json` config: user declares habits with `id`, `name`, `cadence` (`daily` or `weekly`), `source` (`garmin` or `manual`), and for Garmin-sourced habits, a list of exact Garmin `Activity Type` strings to match.
- `import-garmin <csv>`: parses a real Garmin Connect "Activities" CSV export, matches each row's `Activity Type` against configured habits, and writes one completion record per habit per matched day into local SQLite. Idempotent — re-importing the same or an overlapping export never creates duplicate completions.
- `list-types <csv>`: prints the distinct `Activity Type` values found in a Garmin export, so the user can copy exact strings into `habits.json` instead of guessing.
- `checkin <habit_id> [--date] [--note]`: manual completion for habits with no external source (or to backfill a day Garmin missed).
- `remove <habit_id> --date`: deletes a mistaken completion.
- Streak engine (`src/streaks.py`, pure functions, no I/O): current streak, longest streak, and completion rate over a date range, for both daily-cadence habits (consecutive calendar days, with a same-day grace period before the streak breaks) and weekly-cadence habits (consecutive ISO weeks with at least one completion).
- `status`: terminal summary table — per-habit current streak, longest streak, 30-day completion rate.
- `render [--output] [--ai]`: self-contained dark-mode HTML dashboard — hero stats, per-habit calendar-heatmap cards with a client-side 30/90/180/365-day range toggle, a combined cross-habit heatmap, and a coach-note panel (AI or deterministic).
- Optional Claude Haiku "coach note": one paragraph of behavioral observation built strictly from aggregate per-habit streak/rate numbers (never dates, notes, or raw activity titles), with an unconditional deterministic-template fallback that makes zero network calls when `ANTHROPIC_API_KEY` is unset or the call fails.
- `habits.example.json` and `fixtures/sample_garmin_activities.csv` (synthetic, not real personal data) shipped for onboarding and manual verification.

### Out of Scope
- Live Garmin Connect API integration (Garmin's API requires a paid developer agreement; PROFILE.md lists Garmin Connect only as a tool the user uses, not a credentialed API — CSV export is the only available real-data path tonight).
- Habit "reminders" or push notifications (this is a local CLI/report tool, not a running service).
- Editing `habits.json` from the dashboard (config stays file-based; the dashboard is read-only reporting).
- Syncing across devices (single local SQLite file, by design — matches every prior build's local-persistence pattern).

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None
- **Dependencies:** stdlib only at runtime (`csv`, `sqlite3`, `argparse`, `json`, `datetime`, `urllib.request`). Dev dependency: `pytest`.
- **Runtime requirement:** `python3 main.py <command>` — no install step required for core functionality.

## Data Structure

**`habits.json`** (user-edited config, root of build folder):
```json
{
  "habits": [
    {"id": "running", "name": "Running", "cadence": "daily", "source": "garmin",
     "garmin_activity_types": ["Running", "Treadmill Running", "Trail Running"]},
    {"id": "golf", "name": "Golf", "cadence": "weekly", "source": "garmin",
     "garmin_activity_types": ["Golf"]},
    {"id": "strength", "name": "Strength Training", "cadence": "daily", "source": "garmin",
     "garmin_activity_types": ["Strength Training"]},
    {"id": "writing", "name": "Writing", "cadence": "daily", "source": "manual"}
  ]
}
```

**SQLite (`data/streakline.db`, created at runtime — not committed with data):**
```sql
CREATE TABLE completions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  habit_id TEXT NOT NULL,
  date TEXT NOT NULL,          -- ISO YYYY-MM-DD
  source TEXT NOT NULL,        -- 'garmin' or 'manual'
  detail TEXT,                 -- Garmin activity title, or manual note
  created_at TEXT NOT NULL,    -- ISO timestamp
  UNIQUE(habit_id, date)
);
```
One row per habit per calendar day regardless of how many matching Garmin activities occurred that day. `date` is always a naive calendar date (no time-of-day, no timezone) — see Known Limitations in Manual.md for the UTC-day convention this shares with the rest of the catalog.

## Folder Structure

```
builds/2026-08-31-streakline/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── main.py
├── requirements.txt
├── habits.example.json
├── fixtures/
│   └── sample_garmin_activities.csv
├── src/
│   ├── __init__.py
│   ├── db.py
│   ├── garmin_import.py
│   ├── streaks.py
│   ├── coach.py
│   └── render.py
└── tests/
    ├── __init__.py
    ├── test_db.py
    ├── test_garmin_import.py
    ├── test_streaks.py
    ├── test_coach.py
    └── test_render.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (run from the build folder)
- **What will be tested:**
  - Streak engine: empty history, single-day, active streak with today logged, active streak using the "yesterday done, today not yet" grace period, a streak broken more than one day ago, longest-streak-is-in-the-past-not-current, a leap-year Feb 29 → Mar 1 daily boundary, weekly-cadence streaks across ISO week boundaries, completion rate over a date range including a zero-completion range (no divide-by-zero).
  - Garmin CSV import: exact activity-type matching (case-insensitive), multiple activities on the same day collapsing to one completion, malformed rows (missing columns, bad date) skipped with a warning instead of crashing, unmatched activity types reported but not inserted, re-import idempotency (no duplicate rows).
  - DB layer: insert/idempotent-insert/remove/query round-trips against a temp SQLite file per test.
  - Coach note: deterministic fallback with no API key, mocked Anthropic call returning AI text, and mocked call failure falling back to the deterministic template (zero real network calls in any test).
  - HTML render: output contains expected habit names/streak numbers, a hostile activity note (`</script><script>` payload) is escaped and never appears as an executable script tag, valid JSON payload embedded in the page.

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests, covering the edge cases listed above.
2. `import-garmin` against the shipped synthetic fixture correctly matches configured habits, dedupes same-day activities, and is idempotent on a second run (verified manually, not just via mocks).
3. The streak engine's current/longest streak and completion-rate numbers for both daily and weekly cadence match hand-computed values for the fixture data.
4. `render` produces a self-contained HTML dashboard that opens directly (`file://`), is free of XSS (a hostile string in a manual check-in note renders as inert text), and its range-toggle buttons genuinely re-slice the heatmap client-side (verified live in headless Chromium).
5. The optional AI coach note sends only aggregate streak numbers (never dates or notes) and the tool makes zero network calls end-to-end when `ANTHROPIC_API_KEY` is unset (verified with `urllib.request.urlopen` monkey-patched to raise if called).

---

## Scope Changes

None — full scope as planned above was completed as designed.
