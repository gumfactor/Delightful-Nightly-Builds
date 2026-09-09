# Why This? — Headroom: RRSP/TFSA Contribution Room & Deadline Tracker

> **Date:** 2026-09-09

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day of year 252) is I — Life Admin Helper. Two pending backlog ideas matched Category I (#24 Cross-Domain Habit Log, #25 Recurring Chore/Checklist Tracker), both unrated (R=0), giving a 25% lottery draw chance. A random roll of 43 exceeded that threshold, so fresh ideas were generated instead. This lines up with both backlog rows' own rating notes, which had already flagged real weaknesses in each (Habit Log depends on a Garmin CSV that's manual-export-only, not a live pull; Chore Tracker duplicates Teamwork.com/Coda, which idea #3's notes already rejected for task tracking).

## The Decision

Scanned all 8 prior Category I builds (Run Planner, Project Pulse, Ledger Lens, Deadline Guardian, TripKit, Dockside, Macro Kitchen, Renewal Radar) — running/weather, multi-project tracking, bank-CSV budgeting, academic deadlines, trip prep, boat maintenance, meal macros, and domain/subscription renewals are all claimed. Nothing in the catalog (grepped for "RRSP", "TFSA", "contribution room" — zero hits) touches Canadian registered-account tax administration, despite PROFILE.md naming "Canadian economic policy" as a specific interest and IBKR as a daily tool. Verified the core reference data live via web search against multiple independent sources before committing to the idea, since a tax-admin tool is only as good as its numbers being right.

## Connection to User Context

PROFILE.md names "Canadian economic policy" as a specific rabbit-hole interest and lists Interactive Brokers as a daily-use tool and a credentialed data source, alongside "quantitative investing" and "quantitative investing research and automation" as an active project. Contribution-room tracking sits exactly at the intersection PROFILE.md describes as the goal for every project: "reduce friction, preserve context, automate repetitive work" — specifically the repetitive, error-prone mental math of tracking two accounts' worth of shifting annual limits, carryforward, and penalty exposure across 18 years of changing CRA rules.

## Why Tonight

Category I comes up once per 9-day rotation; this is only the 9th night it's been active. No prior Category I build has touched personal tax administration at all — every one so far has been operational/logistical (deadlines, trips, meals, renewals) rather than financial-compliance-shaped. This is a genuinely new sub-domain within the category, not a rebuild of anything.

## What I Hope the User Gets From This

1. A single place to check "how much room do I actually have left" instead of reconstructing 18 years of changing limits, carryforward, and withdrawal timing rules by hand or trusting a Notice of Assessment that's a year stale.
2. Real overcontribution-penalty protection — the 1%-per-month CRA tax is easy to trigger by accident (especially the TFSA withdrawal-and-recontribute-same-year trap) and expensive to discover after the fact.
3. A concrete deadline countdown (RRSP's 60-day post-year-end window) that turns a date buried in a CRA webpage into something that shows up on a dashboard the user actually opens.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Tri-Agency (NSERC/CIHR/SSHRC) Grant Budget Compliance Checker | I | Real friction point ("grant writing," "research administration" are both named in PROFILE.md), but the negotiated institutional overhead/indirect-cost rate that matters most for compliance isn't public data this build could verify or hardcode reliably — the eligible-expense-category rules alone would make a thinner, less accurate tool than Headroom's fully-public, cross-verified CRA limit tables. |
| Faculty Merit File / Annual Report Evidence Aggregator | I | Would mostly re-assemble GitHub commit/PR activity, which this catalog already covers heavily (Fleet Drift, Layer Guard, Worklog, Waymark, ci-pulse, two Repository Health/Analytics dashboards, per backlog idea #40's own note on GitHub-source saturation) — the "life admin" value-add on top of that is thin, and the non-GitHub half (publications, teaching evaluations) has no live, credentialed data source in PROFILE.md, pushing it toward the same "requires manual entry to be useful" pattern that scored AI Session Context Bridge a 3/10. |
| Cross-Domain Habit Log (backlog #24) | I | Passed over by the lottery roll (43 > 25% chance) before fresh ideas were even considered; its own prior rating notes already flag that Garmin Connect is manual-CSV-export-only in this build's runtime, not a live pull — the same "real automated signal" gap the calibration note warns against. |
