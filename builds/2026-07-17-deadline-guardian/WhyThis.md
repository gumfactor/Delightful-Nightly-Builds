# Why This? — Deadline Guardian

> **Date:** 2026-07-17

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day-of-year 198, `(198-1) % 9 = 8`) is **I — Life Admin Helper**, following the 7-night rotation B→C→D→E→F→G→H observed 2026-07-10 through 2026-07-16. `builds/ideas.md` was checked for `pending` rows with `Category = I` — there were none, so per Step 2c the lottery was skipped entirely (no roll needed) and Step 2d (fresh idea generation) ran directly.

## The Decision

Generated three Category I candidates (see Alternatives below) and picked **Deadline Guardian** — a recurring administrative-deadline tracker with Claude-powered extraction from pasted text. The last-10-builds topic scan showed Category I had already covered activity/weather comfort scoring (Run Planner, 2026-06-20) and personal spending (Ledger Lens, 2026-07-08), so a third life-admin build needed a genuinely different domain to avoid feeling repetitive even though neither prior build falls inside the strict "last 10" window. Administrative deadline tracking is untouched by any prior build in the catalog.

## Connection to User Context

PROFILE.md names "Administrative overhead," "Ethics application generation," "Grant writing," "Research administration," and "Student evaluation workflows" directly under "Things you do manually that you suspect could be automated or aided by a tool." This build addresses that friction point head-on: instead of a general-purpose to-do list, it models the specific recurring cadence of academic admin (annual IRB renewals, semesterly course prep, grant progress reports) and uses AI to remove the tedious part — re-typing a due date and category every time a renewal notice or grant-portal email arrives.

## Why Tonight

Tonight is a fresh idea generation night (empty Category I backlog), following the fixed 9-day category rotation. It also directly follows AgentLint (2026-07-16), which surfaced how much of this repo's own admin (a stale calibration note in CLAUDE.md) goes unnoticed without a systematic check — the same principle applies to the user's own academic administrative deadlines.

## What I Hope the User Gets From This

1. A single place to see what administrative deadlines are overdue or imminent, instead of scattered across email and memory.
2. Meaningfully less manual data entry — paste a renewal notice or grant-report email and get a structured, dated entry back.
3. A model for recurring deadlines that doesn't lose the next occurrence when one is completed (a plain to-do list forces you to recreate the annual/semesterly entry by hand every time).

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| TripCast — weather-aware trip packing & prep planner using Open-Meteo | I | Genuinely live-data-driven and ties well to travel/golf/boating/running interests, but overlaps thematically with the existing 2026-06-20 Run Planner build (Open-Meteo activity-comfort scoring for the same three activities). Appended to the backlog for a future night with more distance from Run Planner. |
| Lab Reagent & Equipment Calibration Log | I | Reasonable fit for "managing lab computing infrastructure," but has no available live data source (purely manual entry with no AI-extraction angle) and risks the same "value depends entirely on what you write into it" critique that scored the 2026-06-06 AI Session Context Bridge a 3/10. Appended to the backlog. |
| Deadline Guardian (chosen) | I | — |
