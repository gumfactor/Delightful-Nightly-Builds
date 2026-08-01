# Why This? — ItemScope

> **Date:** 2026-08-01

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Category F (Data Explorer) had 2 pending backlog rows: #1 "The Canada List CSV Quality Inspector" (rating 7) and #10 "SEC EDGAR Financial History Extractor" (rating —, unrated). Only one had a numeric rating, so R = 1 and `lottery_chance = min(75, 25 + 1*2) = 27%`. A random roll of 54 (out of 1–100) came in above that threshold, so no lottery draw happened and the night went to fresh idea generation instead.

## The Decision

Category F's history in this catalog is short but has the single highest-rated build ever recorded: Qualtrics Survey Data Inspector (2026-06-17, 9/10) — a CSV-in, deterministic-statistics-out, HTML-report-plus-cleaned-CSV research QC tool. TrialScope (2026-07-05) followed the same shape for behavioral/RT data. The pattern that works for this user in this category is clear: real research data, verifiable statistics computed live (not templated), and an actionable report. ItemScope applies that exact pattern to a friction point PROFILE.md names directly — "Student evaluation workflows" — and one no prior build in the 50-entry catalog has touched.

## Connection to User Context

PROFILE.md lists "Student evaluation workflows" under "Things you do manually that you suspect could be automated," and separately names teaching undergraduate and graduate courses (including "AI Applications for Psychologists") as a core day-to-day responsibility. Every exam or quiz a professor gives produces exactly the kind of item-level response matrix ItemScope analyzes, and classical test theory (item difficulty, discrimination, distractor quality, reliability) is standard psychometric practice this user would recognize from research methods training but likely doesn't have tooling to apply routinely to their own course assessments.

## Why Tonight

Day-of-year rotation (213 → Category F) landed on Data Explorer. The backlog lottery came up empty (roll 54 > 27% chance), which is exactly the branch CLAUDE.md anticipates for generating something new rather than forcing a marginal backlog idea. This also directly follows up on the 06-17 Qualtrics build's proven formula, applied to a genuinely different data domain (exam items vs. survey responses) rather than repeating it.

## What I Hope the User Gets From This

1. A tool they can run every time they give an exam or quiz — immediate, standing utility rather than a one-off novelty (ranks #1–2 on their stated value list: "save real time," "tools I'll actually use weekly").
2. A concrete answer to "which items on this exam were bad?" backed by real statistics (point-biserial discrimination, KR-20 reliability) instead of gut feel — something that would be tedious to compute by hand in a spreadsheet every time.
3. A flagged-item list with the specific reason (too easy, too hard, poor/negative discrimination, non-functioning distractor) that turns into a direct action: drop it, revise the wording, or keep it as a "gimme."

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| SEC EDGAR Multi-Year Financial Trend Explorer | F | Investment/finance is already the most-repeated domain in the catalog's all-time history (Investment Portfolio Snapshot, Investment Research Platform, Investment Watchlist Dashboard, Investment Thesis Journal, SiliconWatch); a 6th finance build would need a much stronger differentiator than "more tickers, more metrics" to be worth building over a genuinely untouched domain. |
| Neuroimaging Motion/QC Explorer (fMRIPrep confounds) | F | Strong on-profile fit, but depends on a narrow, format-specific input (fMRIPrep-style confound TSVs) that only applies when the user is actively running a specific neuroimaging pipeline, versus ItemScope's much broader "any instructor with a gradebook export" applicability. Worth revisiting for a future Category F or H build. |
| The Canada List CSV Quality Inspector (backlog #1, F) | F | Not drawn in tonight's lottery (roll 54 > 27% chance); remains pending in the backlog for a future draw. |
