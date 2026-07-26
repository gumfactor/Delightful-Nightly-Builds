# Future Features — TripKit

Concrete enhancements for a working, valuable tool — not things required to make tonight's build usable.

1. **Currency/exchange context for international trips.** Cut from tonight's scope to keep the core weather↔packing logic reliable. Bank of Canada Valet API (already proven in the 2026-07-18 CanEcon Pulse build) could add a "your CAD is worth roughly X" line for USD/EUR/GBP destinations.

2. **Editing an existing trip.** Right now changing a trip's dates or destination means delete + re-add. A `tripkit edit <id>` command that lets specific fields be updated (and re-triggers a weather refresh when dates or location change) would remove that friction.

3. **Multi-destination trips.** Conference travel often means one city for the conference and a side trip after. Supporting a list of destination/date-range legs per trip, each with its own weather resolution and its own packing sub-list, would match real travel patterns better than one destination per trip.

4. **Auto-refresh on dashboard generation.** Today, `dashboard` reads whatever weather snapshot is already stored; a far-future trip that has since entered the 16-day forecast window still shows its old climate-normal estimate until `refresh` is run manually. `dashboard --refresh-stale` could automatically re-fetch any trip whose stored snapshot mode no longer matches what `is_within_forecast_horizon` would return today.

5. **Packing list export.** A `--export-markdown` or `--export-pdf` flag on `show`/`dashboard` so a packing list can be printed or shared without opening the HTML dashboard — useful the morning of departure when a phone browser isn't convenient.

6. **Trip templates from history.** Once a handful of trips exist, a "similar past trips" panel (same destination or same activity tags) surfaces what was packed last time and how the actual conditions compared to the forecast/estimate, closing the loop the way Ledger Lens does for spending.
