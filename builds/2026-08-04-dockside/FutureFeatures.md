# Future Features — Dockside: Cottage & Boat Season Readiness Dashboard

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Multi-site dashboard index** — a `render-all` command that generates one HTML file per site plus a landing page linking them, instead of rendering one site at a time.
2. **`--days` override on `sync`/`render`** — Open-Meteo supports up to 16 forecast days; exposing this as a flag (currently hardcoded to 7) would let a task with a long dry-day requirement look further ahead.
3. **CSV export of task history** — a `history TASK_ID` command dumping every recorded completion (season year, date) for a task, useful for noticing drift in when a chore actually gets done year to year.
4. **`--json` output mode on `sync`/`list-tasks`** — machine-readable output for piping into another tool or a cron-triggered notification script.

## Medium Effort (roughly one nightly build session)

5. **Overdue support for wrapping windows** — the current version deliberately punts on computing `overdue` for a task whose window crosses the calendar year boundary (e.g. Nov–Feb winterizing). A correct implementation needs to track which "season instance" of a wrapping window is current, which is a real design problem worth its own session rather than a rushed fix.
6. **A `--notify` flag that emails or writes a plain digest file** when a task flips to `ready_now`, so the tool can be wired into a Claude Code Routine or a cron job instead of requiring a manual `sync` + check every time.
7. **Historical trend charts** — right now `render` only shows the current 7-day window. Since `observations` already accumulates every synced day (deduped, never overwritten... actually currently overwritten on resync — this would need a small schema change to append rather than upsert, or a separate `observation_history` table), a multi-week/multi-season trend view of comfort scores and constraint pass rates would show real seasonal patterns.

## Ambitious Extensions (multi-session effort)

8. **Multi-year task calendar view** — a dashboard tab showing every task's actual completion date across all recorded seasons, so drift (e.g. "dock removal keeps happening two weeks later each year") becomes visible at a glance instead of requiring manual comparison.
9. **Tide-aware scheduling for coastal sites** — Open-Meteo's marine API doesn't include tide predictions, but combining it with a tide-table data source (e.g. NOAA CO-OPS for US coastal sites) would let dock-height-sensitive tasks factor in tide windows, not just wave/wind/temperature.

---

## Possible Integration Points

- **TripKit** (2026-07-26) already handles one-off trip weather/packing for the same "boating"/"cottage life" hobby domain; Dockside's `weather_client.py` (forecast + geocoding) could be factored into a small shared reference pattern for future builds targeting the same hobbies, though STANDARDS.md's "no importing across build folders" rule means any actual sharing would need to happen through a genuinely separate, reusable module outside `builds/`, not a direct import.
- **Worklog** (2026-07-10) already models "recurring task with a completion/next-occurrence lifecycle" for a different domain (project activity); a future life-admin build tracking a different recurring-task category (e.g. home maintenance more broadly) could reuse Dockside's constraint-evaluation approach (pass/fail/unknown scoring against live data) rather than falling back to manual-entry-only, the anti-pattern this build was specifically chosen to avoid.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No `overdue` classification for wrapping (year-boundary) task windows | Track season instances explicitly rather than deriving overdue purely from today's month; see Ambitious Extensions #5 above |
| `observations` table only ever holds the latest sync's 7-day window per site (upsert overwrites, doesn't append) | Add a separate append-only history table if trend charts (Medium Effort #7) are pursued |
| Marine coverage is all-or-nothing per site | If Open-Meteo adds partial coverage (wave but not sea-surface-temperature, or vice versa) this would need per-constraint (not per-site) availability tracking |
