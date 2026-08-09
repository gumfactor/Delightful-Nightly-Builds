# Why This? — Portfolio Lab

> **Date:** 2026-08-09

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

The Category E (Learning Aid) backlog in `builds/ideas.md` held zero pending rows — all 18 entries are categories A, B, C, D, F, G, H — so per Step 2c the lottery was skipped entirely and Step 2d (fresh generation) ran directly. No roll was needed since the filtered pool was empty, not merely below threshold.

## The Decision

Day-of-year rotation (day 221 of 2026) landed on Category E — Learning Aid. The four existing Learning Aid builds (Power Lab, CircuitLab, Bayes Lab, Signal Detection Lab) are all neuroscience/statistics trainers — a strong, proven shape, but a fifth entry in that exact vein would be topic-redundant regardless of category-rotation timing. PROFILE.md names "Continue learning quantitative investing and algorithmic trading" as an explicit learning goal and "quantitative investing" as a named interest/hobby, and — checked against the full 58-build catalog — no Learning Aid has ever touched investing; the topic has only appeared as data dashboards (Investment Research Platform, SiliconWatch), never as something the user is taught. That gap, combined with Yahoo Finance being a genuinely free, no-credential data source named in PROFILE.md's Data Sources, made this the strongest fresh candidate.

## Connection to User Context

Directly targets PROFILE.md's Learning Goals: "Continue learning quantitative investing and algorithmic trading," and the named interest/rabbit-hole topic "Quantitative investing and market structure." The user already runs several investing-adjacent tools (SiliconWatch, Investment Research Platform) but none of them explain the underlying math — Portfolio Lab is the first build that teaches *why* diversification works using the user's own real market data, rather than just reporting numbers.

## Why Tonight

Category E's day-of-year slot came up tonight (day 221 → index 4). Nothing carries over from a previous build — this is the first Learning Aid to use real external market data (all four prior Category E builds were pure client-side math with no data source, which is fine per PROFILE.md's guidance that localStorage-only tools are acceptable for Learning Aids, but a live-data option is strictly better when one exists for free).

## What I Hope the User Gets From This

1. An intuitive, hands-on feel for *why* diversification reduces risk — dragging a two-asset weight slider and watching the real historical risk/return curve bend is a different kind of understanding than reading the formula.
2. A genuine tool for the "quantitative investing" learning goal: the efficient frontier, Sharpe ratio, and correlation matrix are computed from the user's own refreshed real data, not a canned textbook example.
3. A quiz mode that keeps testing intuition ("which of these two portfolios has the better risk-adjusted return?") with answers always derived live from the real covariance matrix — never hardcoded, so it stays honest as the data refreshes.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Git Internals Playground — clickable commit-DAG visualizer teaching branch/merge/rebase/detached-HEAD | E | Solid fit for the "Improve Git/GitHub proficiency" learning goal and genuinely untouched by any Learning Aid, but every input is synthetic/illustrative by nature (a teaching git repo has no "real data" to connect to) and the mechanic (build a fake commit graph, click through it) is less differentiated from what a git tutorial website already does well. Recorded in `builds/ideas.md` for a future night when a real-data angle isn't available. |
| Agent Orchestration Sandbox — visual explainer of pipeline vs. parallel multi-agent execution patterns (workflow DAGs, timing gains) | E | Ties directly to the named "Master AI agent workflows and orchestration" learning goal and is genuinely novel, but it would be entirely synthetic (there is no real external data source for "how agent orchestration works" — it's a concept explainer, not a data-driven trainer) and risks reading as self-referential/meta rather than broadly useful. Recorded in `builds/ideas.md` for a future Category E or H night. |
| A fifth neuroscience/statistics trainer (e.g., mixed-effects models, ROC beyond SDT) | E | Would be the fifth build in an identical shape (from-scratch stats math + Canvas 2D quiz) within the same category — the topic-diversity principle behind CLAUDE.md's Step 2d applies just as much within a category's own history as across categories, even though it isn't spelled out as a formal check the way the cross-category one is. |
