# Future Features — Outdoor Ops

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Configurable second location** — add a `--location2`/`--lat2`/`--lon2` flag so a user who splits time between two cities (e.g. Toronto and a cottage) can sync and compare both in one dashboard render.
2. **CSV export of the score table** — a `--csv path.csv` flag on `render` that writes the same 7-day table (date, factors, scores) to CSV for spreadsheet use.
3. **`--activities` flag** — let the user restrict scoring/rendering to just `run` or just `golf` instead of always computing both.

## Medium Effort (roughly one nightly build session)

4. **Forecast-accuracy trend view** — the schema already stores every sync's snapshot per forecast date, so a given date accumulates multiple predictions as it approaches (e.g. what was predicted for Oct 2 as of Sept 28 vs. Sept 30 vs. Oct 1). A "how much did the forecast move" chart would show real forecast drift/confidence, which the current dashboard doesn't surface at all — it only ever shows the latest snapshot.
5. **Boating suitability as a third activity** — reuse Wake Log's Beaufort-scale approach as a third scoring profile alongside running and golf, so Outdoor Ops becomes the single daily-conditions dashboard instead of two separate tools.
6. **Cron-friendly `sync --quiet` + a Claude Code Routine wrapper** — package `sync` + `render` as a scheduled Routine (per PROFILE.md's stated preference for pull tools over push tools) so the dashboard is always fresh without the user remembering to run it.

## Ambitious Extensions (multi-session effort)

7. **Per-hour scoring for a single day** — right now everything is daily-aggregate. A "best hour to run today" view using Open-Meteo's hourly (not just daily) variables would support same-day, not just same-week, planning.
8. **Personal calibration** — let the user rate how a day actually felt after the fact (too hot / just right / too windy) and slowly adjust the ideal-range and weight constants per activity using their own feedback instead of the fixed defaults in `scoring.py`.

---

## Possible Integration Points

- **Wake Log (2026-09-22)** — same Open-Meteo forecast data source; a natural merge target if boating is ever added as a third Outdoor Ops activity (see #5 above) rather than staying a separate tool.
- **Morning Briefing (2026-06-22)** — if Morning Briefing is ever revisited, Outdoor Ops's `render` output (or a one-line "best day this week" summary) would be a natural section to fold in alongside its existing commit/portfolio/repo-health sections.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Scoring weights and ideal ranges are fixed constants, not personalized | See "Personal calibration" (#8) above |
| Only one location per sync; no in-dashboard location switcher | See "Configurable second location" (#1) above |
| No hourly resolution — "today's score" uses the daily max/aggregate even if conditions vary a lot within the day | See "Per-hour scoring" (#7) above |
| Chart.js is loaded from a CDN, so the dashboard's charts (not the data or score table) are unavailable fully offline or on a restricted network — the dashboard degrades to a text fallback with a note, it does not fail silently or crash | Vendor a local copy of Chart.js into the build folder as a non-CDN fallback |
