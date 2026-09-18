# Why This? — Eligible Spend

> **Date:** 2026-09-18

---

## How This Idea Was Selected

**Selection method:** Lottery draw

Category I (Life Admin Helper) was tonight's rotation slot (day of year 261, `(261-1) % 9 = 8` → index 8 → Category I). The backlog held 4 pending Category I ideas, all unrated (R=0), so `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 21/100 ≤ 25 → lottery draw. All four ideas were unrated (5 tickets each, 20 total). A weighted roll of 12/20 landed in the 11–15 band → idea #51, "Tri-Agency Grant Budget Compliance Checker," added 2026-09-09 and passed over that night in favor of Headroom. Marked `built` in `builds/ideas.md`.

## The Decision

Idea #51's own rating notes (written the night it was passed over) explicitly scoped a safe build: "worth building if scoped tightly around just the publicly documented eligible-expense-category rules, explicitly out of scope for overhead-rate math." That is exactly what tonight's build does. Before writing the PRD, I ran three web searches to verify the actual current state of the Tri-Agency Guide on Financial Administration — and found the original idea's framing was slightly out of date: the guide moved from a fixed eligible/ineligible category list to a principles-based framework in 2020. The build was designed around that correction rather than the idea's original (stale) premise.

## Connection to User Context

PROFILE.md names "Grant writing" and "Research administration" verbatim under "Things you do manually that you suspect could be automated," and the user's actual job title is "Associate Professor of Psychology, Research Lab Director" — someone who personally prepares and manages Tri-Agency grant budgets, not a hypothetical persona. Category I's ambition floor requires a visual/interactive interface, satisfied with a dashboard in the same pattern as Headroom (2026-09-09), which is the catalog's only other build to touch Canadian regulatory-compliance data and scored well enough as a pattern to reuse: hand-encoded, web-search-verified public rules tables plus an optional grounded AI layer with a deterministic fallback.

## Why Tonight

This is the direct sequel to a decision made nine nights ago: on 2026-09-09, this exact idea lost the Category I slot to Headroom, with a rating note saying it was worth building once scoped correctly. Tonight's Category I rotation plus a 25% lottery draw landing on it (against 3 sibling Category I ideas) means the backlog's own stated condition — narrow scope, public rules only — could finally be met.

## What I Hope the User Gets From This

1. A pre-submission and pre-claim check that catches a Tri-Agency-ineligible line item (alcohol on a hospitality line, tuition folded into a personnel budget, general IT costs charged directly instead of coming from overhead) before it becomes a compliance finding or a clawback.
2. A concrete, principle-by-principle explanation of *why* a line item is flagged, not just a pass/fail stamp — citing the specific Tri-Agency principle or directive so it can be defended or fixed.
3. A tool that is honest about its own limits: it never claims a clean bill of Tri-Agency compliance, only that no *known* blocking rule fired, and it explicitly refuses to touch the institution-specific overhead-rate math that would require information this tool can't verify.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Cross-Domain Habit Log (#24) | I | Garmin Connect is only available as a manual CSV export, not a live API — would mostly be manual check-ins with a thin data layer, the exact pattern the preference prior scores low. |
| Recurring Chore / Checklist Tracker (#25) | I | Directly overlaps functionality already covered by Teamwork.com, which the user's own rating notes on a prior idea explicitly rejected as redundant for task tracking. |
| Faculty Merit File / Annual Report Evidence Aggregator (#52) | I | Would mostly re-assemble GitHub activity, already covered by several prior builds (Fleet Drift, Layer Guard, two repo-health dashboards); the non-GitHub half (publications, teaching evals) has no live credentialed data source in PROFILE.md. |
