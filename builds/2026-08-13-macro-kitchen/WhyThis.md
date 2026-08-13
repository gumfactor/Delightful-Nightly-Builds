# Why This? — Macro Kitchen

> **Date:** 2026-08-13

---

## How This Idea Was Selected

**Selection method:** Fresh generation

Day-of-year 225 → `category_index = (225-1) % 9 = 8` → Category I (Life Admin Helper). The Category I backlog in `builds/ideas.md` (resynced from the most recent open PR branch, `claude/cool-sagan-hado2r`, 2026-08-12) had zero pending rows — every existing idea in the backlog belongs to categories A, B, C, D, E, F, G, or H. The lottery step was skipped entirely (no pool to draw from) and generation went straight to fresh ideas.

## The Decision

Scanned the last 10 builds (2026-08-03 through 2026-08-12) for topic saturation: investing/finance appeared twice (Portfolio Lab, Quarter Call — under the "more than twice" threshold but close), academic/research administration appeared three times (Impact Ledger, Manuscript Pipeline, Panel Prep), and developer/git tooling appeared three times (Waymark, Landing Pattern, Snipvault). None of those pushed hard against Life Admin Helper's own six prior builds (Run Planner, Project Pulse, Ledger Lens, Deadline Guardian, TripKit, Dockside), but every one of those six already covers running/golf/boating weather, cross-project context, spending, academic deadlines, trip packing, and cottage/boat maintenance — leaving "meal planner," one of the category's own named examples, completely untouched. Nutrition/meal planning also connects to a real, sanctioned local data source (a Garmin Connect CSV export) rather than requiring another Open-Meteo weather-comfort build, which this category was starting to lean on (3 of 6 prior builds used Open-Meteo).

## Connection to User Context

PROFILE.md names "distance running, golf, ... boating, cottage life" as hobbies and lists Garmin Connect and MyFitnessPal among daily-use tools, but no build has ever touched nutrition or training-load-aware eating. The "physical activities" section explicitly lists "general fitness maintenance" and the friction-points list is dominated by academic/entrepreneurial admin — a meal planner is a genuinely different kind of "life admin" than anything built so far, and ties directly to a named daily habit (Garmin) rather than an invented one.

## Why Tonight

Category rotation lands on Life Admin Helper every 9 nights; today is that night. The category's four named examples in CLAUDE.md are "budget tracker, meal planner, habit log, checklist" — three of the four have functional equivalents already in the catalog (Ledger Lens covers budget/spending, Deadline Guardian and TripKit cover checklist-style planning), leaving meal planner as the one genuinely unaddressed example.

## What I Hope the User Gets From This

1. A meal plan that reflects real numbers (their actual body stats and, when they run `import-garmin`, their actual training load) instead of a generic calorie template — actionable the same day it's generated.
2. A grocery list that removes the "translate the plan into a shopping trip" step, which is normally the most tedious part of meal planning.
3. A second data point (alongside Run Planner) for what a Garmin CSV export can drive — establishing that local fitness-export files are a viable "real data" source for future Life Admin or Learning Aid builds.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Recurring bills/subscription price-tracker | I | Ledger Lens (2026-07-08) already does merchant+amount-clustering recurring-charge detection from bank CSVs — this would be a near-duplicate of an existing feature, not a new capability. |
| Home/cottage maintenance checklist (non-boat) | I | Structurally identical to Dockside's (2026-08-04) seasonal-task-vs-weather-readiness engine, just swapping the task list — not a genuinely new tool shape. |
| TFSA/RRSP contribution-room tracker (IBKR local sync) | I | Genuinely untouched IBKR TWS integration and a real Life Admin gap, but investing/finance already appeared twice in the last 10 builds (Portfolio Lab, Quarter Call); a third investing-flavored build risked topic oversaturation this soon after two others, so it was set aside in favor of the completely untouched nutrition domain. |
