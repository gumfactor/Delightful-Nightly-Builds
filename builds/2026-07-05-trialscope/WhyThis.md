# Why This? — TrialScope: Behavioral & Reaction-Time Data QC Explorer

> **Date:** 2026-07-05

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day of year 186, index 5) is F — Data Explorer. `builds/ideas.md` had two pending F-category ideas: "The Canada List CSV Quality Inspector" (rated 7, 1 rated idea → R=1) and "SEC EDGAR Financial History Extractor" (unrated). Lottery chance = min(75, 25 + 1×2) = 27%. Rolled 59 (via `secrets.randbelow`) — above 27, so the lottery was not drawn and fresh ideas were generated instead, per Step 2c/2d.

## The Decision

Before generating ideas, I tested actual network reachability for this session, since Step 2f and PROFILE.md's Data Sources section assume several free public APIs are available. None of them were: Yahoo Finance, Open-Meteo, PubMed E-utilities, arXiv, Wikipedia, ClinicalTrials.gov, SEC EDGAR, and NIH RePORTER all returned `403 Forbidden` from this session's egress proxy — confirmed via both direct Python HTTP calls and a real Chromium browser `fetch()` (so a client-side browser build wouldn't have worked around it either, at least for testing purposes in this session). Only `api.github.com`, `pypi.org`/`registry.npmjs.org`, and `api.anthropic.com` are reachable. GitHub is also topic-saturated: 4 of the last 10 builds (06-26, 06-28, 06-29, 06-30) already use GitHub activity/CI/commit data as their core dataset.

Given that, I looked at what's actually worked well for category F historically: the highest-rated build in the entire catalog is the Jun 17 Qualtrics Survey Data Inspector (9/10) — a pure local-file processing tool with no live API at all, built for the user's own research data. That build proves the "prefer live data" guidance is about not settling for fake/mock data when a live source exists for the domain — not a blanket requirement for network calls. There is no live API for a researcher's own trial-level behavioral data; the real data source for this domain is the researcher's own experiment output files, exactly as it was for Qualtrics survey exports.

TrialScope applies the same successful pattern to a different, complementary research-data problem: trial-level reaction-time/accuracy QC instead of survey-response QC. It is not a duplicate of the Qualtrics build (different data shape, different QC rules — guessing/attention-lapse/anticipatory-response detection instead of straight-lining/completion-time detection) and it directly serves a task the user does by hand today.

## Connection to User Context

PROFILE.md states the user runs "a forensic and affective neuroscience lab" and "conduct[s] neuroimaging and behavioral studies." Deciding which participants/trials to exclude from a reaction-time task before running analysis is a routine, recurring, and somewhat tedious part of that work — closely related to the explicitly-listed friction point "Research administration" and adjacent to "Literature reviews... Grant writing" in spirit (turning a manual judgment call into a documented, reproducible procedure). It also produces a ready-to-adapt "Participants & Data Quality" paragraph, which speaks directly to manuscript/methods-writing friction.

## Why Tonight

Tonight is an F — Data Explorer night by the fixed 9-day category rotation. The category's ambition floor requires a genuine visual/interactive interface (a script that prints to stdout does not qualify) — TrialScope's HTML report with sortable tables, hand-drawn SVG histograms, and learning-curve charts satisfies that directly, following the same Python-computes / HTML-renders architecture that scored 9/10 on Jun 17.

## What I Hope the User Gets From This

1. A faster, more consistent, better-documented participant/trial exclusion process for actual behavioral task data from the lab
2. A methods-section paragraph draft that saves the "how do I phrase the exclusion criteria" writing step
3. A concrete, reusable QC tool that can be pointed at any future trial-level export (PsychoPy, jsPsych, E-Prime, or any tool that exports one-row-per-trial CSVs) without modification

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| PyPI Dependency Ecosystem Explorer (dependency graph + maintenance-risk visualization for a Python project) | F | PyPI is genuinely reachable in this sandbox, but the analytical angle (package staleness/risk) sits too close to the existing Jun 19 `dep-check` PyPI-based tool; would read as a near-duplicate rather than a new capability. |
| GitHub Commit Semantic Theme Explorer (AI-clustered commit-message themes over time) | F | GitHub is the most topic-saturated data domain in the last 10 builds (4 of 10). A genuinely different analytical lens (semantic clustering vs. cadence/timing) would justify it eventually, but not while GitHub is this heavily represented; recorded to the backlog for a future night with more topic headroom. |
| The Canada List CSV Quality Inspector (backlog idea #1) | F | Was eligible for the lottery draw but the lottery roll (59) came in above the 27% draw threshold, so this stayed in the backlog for a future draw rather than being hand-picked outside the lottery mechanism. |
