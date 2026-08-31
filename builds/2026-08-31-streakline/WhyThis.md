# Why This? — Streakline

> **Date:** 2026-08-31

---

## How This Idea Was Selected

**Selection method:** Lottery draw

Tonight's category (day-of-year 243, `(243-1) % 9 = 8` → index 8 = **I — Life Admin Helper**) had two `pending` rows in `builds/ideas.md`, both added 2026-08-22 with no user rating (blank = 5 tickets each, R=0 rated entries → `lottery_chance = min(75, 25 + 0*2) = 25%`). Rolled 24/100 → ≤25, so the lottery drew from the pool instead of generating fresh. Weighted pick across 10 tickets (5/5 split) rolled 2 → idea #24, **Cross-Domain Habit Log**. Marked `built` in `builds/ideas.md`.

## The Decision

Idea #24's own Rating Notes (written 2026-08-22, when it was passed over in favor of Renewal Radar) flagged a real weakness: Garmin Connect has no live API in PROFILE.md's Data Sources, only a manual CSV export, so a naive implementation "would read as mostly manual check-ins with a thin Garmin layer bolted on." That critique is fair for a design that treats the CSV as decoration. Tonight's implementation treats it as the load-bearing data source instead: `import-garmin` does real parsing and matching against Garmin's actual `Activity Type` export column, is idempotent across re-imports, and the streak engine's daily/weekly cadence logic is real testable computation, not a thin wrapper. Manual check-in is scoped only to the one habit (writing) that has no plausible external signal at all — not used as a crutch for the activity-based habits.

## Connection to User Context

PROFILE.md lists Garmin Connect and MyFitnessPal under "Tools and environments you use daily" and names running, golf, and strength/core training explicitly under "Physical activities" — plus "Building software products" and writing under Creative pursuits. No prior build (Macro Kitchen was the only other Garmin-adjacent build, and it imports Garmin data for nutrition/activity-calorie context, not for habit/streak tracking) has unified these into one cross-domain consistency view. The optional AI coach layer also connects to the user's own professional background — an Associate Professor of Psychology whose lab studies stress, motivation, and behavior — by generating a behavioral observation about their own streak data rather than a generic congratulatory message.

## Why Tonight

Category I hadn't run since Renewal Radar on 2026-08-22; day-of-year rotation put it back in play tonight. The lottery is specifically designed to occasionally force a build past a prior session's "passed over" judgment when a stronger implementation of the same idea is possible — that's what happened here.

## What I Hope the User Gets From This

1. One place to see whether running, golf, strength training, and writing are actually happening together, using data pulled from an export they already generate rather than a new manual-entry burden.
2. A genuinely tested streak/consistency engine (weekly cadence for golf is deliberately not forced into a daily model) they can trust the numbers from, not just a pretty calendar.
3. A small, honest example of turning a personal data export into a real local analysis tool — the same pattern useful for The Canada List's own data pipelines.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Recurring Chore / Checklist Tracker (idea #25, same lottery pool) | I | Not drawn (ticket 2 of 10 landed on idea #24). Also directly overlaps Teamwork.com/Coda, which the catalog's own idea #3 rating notes already rejected for task tracking. |
| Fresh generation | — | Not reached — the 24/100 roll fell within the 25% lottery-draw threshold, so the pool was used instead of generating new ideas. |
