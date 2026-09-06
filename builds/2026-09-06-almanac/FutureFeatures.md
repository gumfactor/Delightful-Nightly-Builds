# Future Features — Almanac

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **User-configurable extreme-event thresholds** — Expose the heat-wave/cold-snap/heavy-rain/high-wind thresholds (currently fixed in `DEFAULT_THRESHOLDS`) as number inputs next to the activity preset, since a 30°C "heat wave" threshold tuned for Toronto is meaningless for Phoenix or Yellowknife.
2. **"Compare two locations" mode** — Almanac already fetches one location at a time; adding a second location fetch and overlaying its climatology band and year chart on the same axes would directly support "should I golf here or there this month" comparisons.
3. **Remember the last-viewed variable on the year chart** — Currently `yearChartVariable` resets to "avg high" on every fresh fetch; persisting it alongside `almanac.lastSettings` is a one-line addition.

## Medium Effort (roughly one nightly build session)

4. **Day-of-year climatology instead of monthly buckets** — Replace the 12-month climatology bands with a smoother 366-day rolling-window percentile band (handling Feb 29 explicitly), giving a much finer-grained "what's normal on this exact date" view — closer to what almanacs and climate-normal charts actually show.
5. **Anomaly year detection** — Add a deterministic z-score-style flag on the year table for any year that's a statistical outlier versus the multi-year climatology (e.g. "2023 was 2.1 standard deviations hotter than the fetched-period average") rather than requiring the user to eyeball the bar chart.

## Ambitious Extensions (multi-session effort)

6. **Air-quality and marine-layer data** — Open-Meteo also serves a free Air Quality API; adding PM2.5/ozone as a variable would make the Running preset genuinely evidence-based (heat and rain matter, but so does air quality), and closes the "Boating" preset's known gap around water-specific conditions once a marine data source is identified.
7. **Saved "location profiles" with named custom activity presets** — Beyond the 5-item recent-locations list, let the user name and save a full profile (location + custom thresholds + season window) — e.g. "Cottage boating season" — so repeat questions ("is this a good boating week historically") become a one-click reload instead of re-entering four numbers each time.

---

## Possible Integration Points

- **Run Planner** (2026-06-20) covers 7-day *forward* comfort scoring for the same three activities (running/golf/boating); Almanac is the natural historical-context companion — a future build could link them, e.g. Run Planner showing "this week's forecast is warmer than 90% of historical Augusts" pulled from an Almanac-style percentile calculation.
- **TripKit** (2026-07-26, Weather-Aware Trip Prep & Packing Planner) could use Almanac's historical percentile bands to set smarter packing-list defaults for a destination and travel month than a single forecast allows.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Fixed extreme-event thresholds not tuned per climate | Quick Win #1 above |
| Monthly (not daily) climatology granularity | Medium Effort #4 above |
| No marine/water-specific variables for the Boating preset | Ambitious Extension #6 above |
| No way to compare two locations side by side | Quick Win #2 above |
