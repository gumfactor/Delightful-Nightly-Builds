# Why This? — Dockside: Cottage & Boat Season Readiness Dashboard

> **Date:** 2026-08-04

---

## How This Idea Was Selected

**Selection method:** Lottery draw, overridden to fresh generation.

Day-of-year 216 → `(216-1) % 9 = 8` → Category I (Life Admin Helper). Two pending Category I backlog ideas existed (#15 Household & Cottage Maintenance Scheduler, #16 Momentum: Cross-Domain Habit Tracker), both at the default 5-ticket weight (no numeric rating), so `R = 0` → `lottery_chance = min(75, 25 + 0) = 25%`. Rolled 17 ≤ 25 → a draw happened. Ticket draw (1–10) rolled 7 → idea #16 (Momentum) won.

Idea #16 was overridden rather than built. It already carries a documented critique from 2026-07-26 (when it was first passed over for TripKit): its only two signals are GitHub commit activity — already the backbone of seven-plus builds in this catalog (Worklog, Pipeline Pulse, ci-pulse, BugTrace, Landing Pattern, and two Developer Analytics dashboards) — and manual logging, which is the exact mock/manual-data anti-pattern CLAUDE.md's calibration note names as a cause of every build scoring 4/10 or below to date. That critique hasn't aged out; if anything the GitHub-saturation point is stronger now than it was in July. This mirrors the precedent set for the 2026-07-27 SiliconWatch build, which overrode a lottery draw that resurfaced a documented, still-valid flaw (there: a verbatim duplicate; here: an unaddressed data-source weakness) rather than rebuild something already known to be weak. Idea #16 has been marked `skipped` in `builds/ideas.md` with this reasoning recorded so it stops recurring in future Category I draws.

## The Decision

With the lottery draw discarded, three fresh Category I ideas were generated (see Alternatives Considered). Dockside won because it is the only one of the three with a genuinely new, real, no-auth live data source — the Open-Meteo Marine API (wave height, wave period, sea-surface temperature) — that no prior build in the catalog has touched, paired with a deterministic, unit-testable core (multi-constraint weather-window scoring across a 7-day forecast) rather than another prose-generation or manual-entry-only tool. It also directly answers a gap the existing Category I builds leave open: TripKit (2026-07-26) already covers "boating" and "cottage life" but only through the lens of one-off trip packing against land-forecast data; nothing in the catalog handles the recurring, season-long maintenance-scheduling problem those two hobbies actually create every spring and fall.

## Connection to User Context

PROFILE.md names "boating" and "cottage life" directly under Personal Interests and Hobbies, and "Things you do manually that you suspect could be automated" lists exactly this shape of recurring administrative friction. Cottage and boat seasonal maintenance (dock installation/removal, winterizing, engine service) is a real annual task list gated by weather that the user currently has to track and time by memory or manual calendar reminders — a friction point never directly built for before tonight.

## Why Tonight

Category rotation put tonight on Category I. The backlog held two pending ideas but both were tied at default weight and the draw's winner carried a documented, unresolved weakness (see above), so fresh generation was the right path per CLAUDE.md Step 2c/2d. This is also the first build in the catalog to use the Open-Meteo Marine API specifically (distinct from the standard Forecast API already used by Run Planner, WeatherSong, TripKit, and Signal Detection Lab's — no, TripKit only), extending the "real live weather data" pattern the catalog already trusts into a genuinely new sub-domain.

## What I Hope the User Gets From This

1. A real answer to "is this weekend actually good for pulling the dock" instead of a guess, backed by the same forecast data they'd otherwise have to cross-reference themselves across wind, rain, and water temperature
2. A season task list that doesn't reset to zero every year — completions roll forward automatically to next season with the correct target window
3. A "boating outlook" view that's just pleasant to check even with no pending task, tying directly to a named hobby with zero prior build coverage

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Momentum: Cross-Domain Habit Tracker (backlog #16, lottery winner) | I | Documented, still-valid critique on file: GitHub-signal is redundant with 7+ existing builds, and the only other signal is manual logging — the exact anti-pattern CLAUDE.md warns scores low. Overridden (see above). |
| PantryPlan: Nutrition-Aware Meal Planner (Open Food Facts API) | I | Genuine live-data source, but weaker connection to a named PROFILE.md hobby than a boating/cottage build, and risks reading as a weaker parallel to MyFitnessPal, a tool the user already uses daily for exactly this. Added to backlog as idea #33. |
| Season Kickoff: Household Utility & Insurance Renewal Radar | I | No real external data source exists for private contract/insurance renewal dates — the entire tool would be manual entry with zero live-data differentiation, the same weakness that sank idea #16 tonight. Added to backlog as idea #34. |
