# Why This Build — TripKit

## Category Determination

- Today (UTC): 2026-07-26
- Day of year: 207
- `category_index = (207 - 1) % 9 = 8` → **Category I — Life Admin Helper**

## Lottery Check (Step 2c)

Read `builds/ideas.md` (resynced from the most recent open PR branch, `claude/cool-sagan-dz70ef`, PR #51). Filtered for `pending` rows with `Category == I`: **zero matches**. The only Category I-adjacent entries in the backlog are unrelated categories (F, A, B, H, G). Per CLAUDE.md Step 2c, an empty pool skips the lottery entirely — no roll occurred. Proceeded directly to Step 2d, fresh idea generation.

## Topic Diversity Check

Scanned the last 10 catalog rows (2026-07-15 through 2026-07-25): Confound Hunter (research-methods game), AgentLint (dev-tool linter), Deadline Guardian (academic deadline tracker), CanEcon Pulse (macro-economic dashboard), Protocol Forge (IRB ethics drafting), CanFile (Canadian ownership lookup), Bridgework (analogy generator), Bayes Lab (Bayesian stats trainer), Heuristic Hunt (cognitive-bias game), BugTrace (bug-pattern miner). No topic domain repeats more than once — no saturation flag applies. Investment/finance has not appeared at all in the last 10 builds.

Within Category I specifically, two prior builds exist: **Ledger Lens** (2026-07-08, spending/subscription categorization) and **Deadline Guardian** (2026-07-17, recurring academic/admin deadlines). Neither touches travel, packing, or trip logistics — an explicit gap given PROFILE.md names "travel," "cottage life," "boating," and "golf" as active hobbies, none of which have a dedicated build.

## Candidates Considered

1. **TripKit — Weather-Aware Trip Prep & Packing Planner** (chosen). Live Open-Meteo geocoding + forecast (near-term trips) with a historical-climate-normal fallback (far-future trips beyond the 16-day forecast horizon) feeding a deterministic packing rule engine across activity types drawn straight from PROFILE.md (conference travel, cottage, boating, golf, outdoor, business, leisure), with an optional Claude Haiku trip briefing. Hits a genuinely unaddressed friction point ("Research administration," travel prep) with a real external data source and a working forecast/climate dual-mode design that's technically non-trivial, not just another CRUD-plus-dashboard build.

2. **Household & Cottage Maintenance Scheduler.** Recurring maintenance tasks (boat winterizing, engine service) timed against weather windows. Rejected: narrower audience-fit than trip prep, and the "next dry week for boat haul-out" logic is largely a subset of what TripKit's weather engine already does — would have shipped a thinner build for similar engineering effort.

3. **Momentum — Cross-Domain Habit Tracker.** Daily habit/streak log for writing and exercise, using GitHub commit activity as a proxy signal plus manual logging, with AI coaching. Rejected: no live data source beyond GitHub (already the backbone of Worklog, Pipeline Pulse, and three other builds this month), and the manual-entry-plus-streak pattern is close to what Deadline Guardian and Ledger Lens already do procedurally, without a new domain.

Non-winning candidates (2 and 3) appended to `builds/ideas.md` as new pending rows for future lottery draws.

## Deviations From Idea Brief

None — no linked Idea Brief exists for this fresh idea (Step 2e not applicable).
