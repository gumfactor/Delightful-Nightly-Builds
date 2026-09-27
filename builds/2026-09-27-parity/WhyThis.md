# Why This? — Parity

> **Date:** 2026-09-27

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight is day-of-year 270 → `category_index = (270 - 1) % 9 = 8` → **Category I — Life Admin Helper**. `builds/ideas.md` was scanned for `pending` rows with `Category = I`: there are none (the backlog holds 12 rows total, none tagged `I`). Per Step 2c, an empty matching pool skips the lottery entirely and routes straight to Step 2d (fresh idea generation) — no roll was needed.

## The Decision

Category I now has nine prior builds (Run Planner, Project Pulse, Ledger Lens, Deadline Guardian, TripKit, Dockside, Macro Kitchen, Renewal Radar, Headroom, Eligible Spend — ten, in fact), and they've thoroughly covered CLAUDE.md's own named examples: budget tracking (Ledger Lens), meal planning (Macro Kitchen), and habit logs / generic checklists have both been explicitly rejected in prior `BUILD_LOG.md`/`WhyThis.md` reasoning (Dockside, Renewal Radar) as too weak without a live data source. Rather than force another pass at an already-exhausted CLAUDE.md example, I scanned PROFILE.md's own named friction points for one Category I hasn't touched: **"Teamwork/Coda synchronization"** appears verbatim in "Things you do manually that you suspect could be automated," and **"Keeping multiple data systems synchronized"** appears verbatim in "Recurring friction points." Neither Teamwork.com nor Coda has been used in any of the 110 prior builds (confirmed by grep across `builds/index.md` and `builds/ideas.md` — the only two hits are Renewal Radar's own reasoning citing them as reasons to *reject* a different, generic checklist idea, and idea #3's rating note). This is a real, named gap, not a manufactured one.

The last 10 builds were also checked for topic saturation per CLAUDE.md's explicit rule: Corporate Ownership Chain Explorer (F), Grant Horizon (A), and Eligible Spend (I) all sit in finance/grant-administration territory — three touches in ten builds. That rules out another investment, grant-budget, or registered-account build tonight (which would have ruled out extending Eligible Spend into overhead-rate math, one of the rejected alternatives below).

## Connection to User Context

PROFILE.md lists "Teamwork/Coda synchronization" and "The Canada List ingestion and quality control pipeline" as manual, automatable friction, and "Keeping multiple data systems synchronized" as a recurring friction point tied to running a research lab, The Canada List, and Kwyeter simultaneously ("I tend to run many projects simultaneously and benefit enormously from tools that preserve context across sessions"). Teamwork.com and Coda are both named under "Tools and environments you use daily," and both APIs are explicitly listed in PROFILE.md's Data Sources section (flagged as needing their tokens added to repo secrets before the *build agent* can call them live — the same runtime-supplied-credential pattern already established for `ANTHROPIC_API_KEY`, which the user supplies when running the tool locally).

## Why Tonight

This is the first build to touch either Teamwork.com or Coda's real APIs. It follows the established Category I pattern (Python CLI + local persistence + self-contained dark-mode HTML dashboard + optional Claude Haiku briefing with a deterministic fallback) set by Renewal Radar, Headroom, and Eligible Spend, applied to a genuinely new data domain rather than a new coat of paint on an already-solved one.

## What I Hope the User Gets From This

1. A concrete answer to "is anything falling through the cracks between my Coda plan and my Teamwork execution?" without manually cross-referencing both tools.
2. Visibility into *drift* over time (is the gap between the two systems growing or shrinking sync over sync), not just a one-time snapshot.
3. A safe, read-only, non-destructive tool — no write-back to either system — so it can be run at zero risk to real project data.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Habit Streak Mirror — auto-derive habit streaks (running, writing, coding) from Garmin Connect CSV exports + GitHub commit activity | I | Garmin Connect has no live API in PROFILE.md's Data Sources (CSV-export only, same constraint Macro Kitchen already hit), and generic habit-tracking has already been explicitly rejected once this category (Dockside's `BUILD_LOG.md`, "Momentum" idea) as too dependent on data that isn't genuinely live. Would have been a rehash of a pattern already ruled out, not a new one. |
| Grant Overhead-Rate Calculator — extend Eligible Spend (2026-09-18) into F&A/overhead-rate math | I | Eligible Spend's own `BUILD_LOG.md` explicitly scoped overhead-rate math *out* on purpose. Building it tonight would also be the third grant/finance-adjacent build in the last 10 across the whole catalog (Grant Horizon, Eligible Spend), tripping CLAUDE.md's topic-saturation rule for finance-adjacent domains. |
| Cross-Border Currency Life-Admin Planner — track USD/CAD conversion timing implications for a Canadian running a US-facing platform | I | Same topic-saturation problem — investment/finance-adjacent themes already appeared 3 times in the last 10 builds (Corporate Ownership Chain Explorer, Grant Horizon, Eligible Spend). Parity's Teamwork/Coda domain is untouched by comparison. |
