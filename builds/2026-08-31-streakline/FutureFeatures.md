# Future Features — Streakline

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **CSV export of the completion history** — a `python3 main.py export --output history.csv` command that dumps the `completions` table to CSV, for anyone who wants to graph it in something else or archive it outside SQLite.
2. **`--json` on `status`** — machine-readable output alongside the terminal table, so `status` could feed a shell script or a future build without re-parsing text.
3. **Multiple export merge in one `import-garmin` call** — accept several CSV paths in one invocation instead of running the command once per file, for someone who has Garmin exports split by year.

## Medium Effort (roughly one nightly build session)

4. **A "perfect week" summary** — a weekly digest (could ship as a Claude Code Routine) that emails or posts a short summary of which days had every daily-cadence habit completed, building on the combined heatmap's data but as a periodic push rather than something you have to remember to open.
5. **Habit-pair correlation** — a simple analysis of which habits tend to co-occur or anti-correlate (e.g., "strength training days are 40% more likely to also be a writing day") using the same completion history, surfaced as a small insight panel next to the coach note.

## Ambitious Extensions (multi-session effort)

6. **Live Garmin Connect API integration** — if Garmin's developer API credentials are ever added to PROFILE.md's Data Sources, replace the CSV-import step with a scheduled pull (a Claude Code Routine), removing the manual export step entirely for the Garmin-sourced habits.
7. **A "why did this break" retrospective** — when a long streak ends, generate a short AI-assisted note (same aggregate-only privacy model as the coach note) looking at the days immediately before the break for any pattern worth naming, turning streak data into an actual behavioral tool rather than just a scoreboard.

---

## Possible Integration Points

- **Macro Kitchen (2026-08-13)** already imports Garmin Connect data for nutrition/activity-calorie context — the two tools could eventually share a single Garmin CSV import module rather than each parsing the export independently, though today they're intentionally separate (different data needs, different schemas).
- A future "Life Admin" umbrella dashboard (if one is ever built) could pull Streakline's `status` output alongside Renewal Radar's (2026-08-22) urgency buckets for one combined daily-admin view.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| UTC-day boundary doesn't match the user's Eastern local day | Add a configurable timezone offset (in `habits.json` or a CLI flag) that shifts what counts as "today" before computing streaks |
| Manual CSV export required for Garmin data | Revisit once/if a live Garmin API credential is added to PROFILE.md |
| No reminder if a streak is about to lapse | A Claude Code Hook or Routine could check `status` daily and only notify when a streak is at risk, rather than requiring the user to remember to open the dashboard |
