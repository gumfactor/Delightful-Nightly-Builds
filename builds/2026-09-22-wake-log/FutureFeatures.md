# Future Features — Wake Log

> Ideas for extending this build. The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Multi-location comparison** — `forecast --lat ... --lon ...` currently handles one location per call; a `locations.json` config file listing several named spots (cottage, marina, favorite bay) would let `forecast --all` print a side-by-side best-window comparison in one command.
2. **CSV export** — `list --format csv > season.csv` would let the season's journal drop straight into a spreadsheet for a simple "days on the water" tally.
3. **`--week-ahead` shortcut** — an alias for `forecast --days 7` that also prints just the single best day across the whole week in one line, for a fast morning check.

## Medium Effort (roughly one nightly build session)

4. **NOAA/ECCC marine buoy layer** — pull real water temperature and wave-height data from a nearby buoy (where one exists) as an additional, clearly-labeled signal alongside the Open-Meteo wind/precip/temp score, rather than inferring wave conditions from wind speed alone.
5. **Season summary view** — a `render --season-summary` mode that aggregates all saved entries into month-by-month "days above 70 comfort score" and "average Beaufort" stats, turning the raw journal into a retrospective.
6. **Photo attachment** — let `generate --photo path.jpg` attach a local image path to an entry (stored as a file reference, not embedded), so the HTML journal becomes a real trip-photo log next to the weather facts.

## Ambitious Extensions (multi-session effort)

7. **Shared multi-user journal** — if this ever needs to be used by more than one person at a cottage, a lightweight shared SQLite-over-network or simple sync mechanism would let everyone's outings land in the same journal (currently intentionally single-user/local, like every other nightly build's persistence model).
8. **Route-aware scoring** — instead of scoring a single lat/lon, accept a planned route (a list of waypoints) and score the whole route's exposure, useful for a longer cottage-to-marina crossing rather than a single-point outing.

---

## Possible Integration Points

- **Run Planner** (2026-06-20) already computes a generic activity-comfort score from Open-Meteo including a boating dimension; Wake Log's Beaufort-based engine is more boating-specific and could eventually replace or feed into Run Planner's boating score if the two were unified, though they're intentionally kept separate tonight to avoid conflating two different builds' architectures.
- **Morning Briefing** (2026-06-22) already aggregates multiple daily signals into one digest; a future version could pull Wake Log's `forecast` best-window line into that digest on days a good boating window exists.

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No tide data | Integrate a tide API (e.g. NOAA CO-OPS for US coastal locations) as an additional scoring dimension where available |
| No wave-height data | Add the NOAA/ECCC buoy layer described above (item 4) |
| Novelty scoring only compares narratives for the exact same `location_name` string | Normalize location names (case-insensitive, trimmed) so "Stony Lake" and "stony lake " don't split the novelty corpus in two |
| Fixed 3-window-per-day granularity | Allow a configurable window size (e.g. 2-hour blocks) for finer-grained recommendations near sunrise/sunset |
