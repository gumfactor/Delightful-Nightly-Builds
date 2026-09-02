# Why This? — CiteForge

> **Date:** 2026-09-02

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day of year 245, `(245-1) % 9 = 1` → **B — Productivity Utility**) had exactly one pending backlog row: idea #14, "Multi-Repo Dependency Batch Auditor." Before running the lottery, this row was checked for staleness (standard practice in this repo — see idea #9's and #5's correction history). Its own 2026-08-15 rating note said it was worth building "only if paired with something dep-check doesn't do (e.g. cross-repo shared-dependency-version drift detection)" — and that exact feature shipped last night as Fleet Drift (2026-09-01). The row was corrected to `skipped` in `builds/ideas.md` before the draw, which emptied Category B's pool and routed straight to fresh idea generation per Step 2c/2d.

## The Decision

Three fresh Category B candidates were generated (see Alternatives Considered). CiteForge — a from-scratch multi-style citation formatter — was chosen because it has a genuinely untouched academic-writing friction point, a deterministic algorithmic core deep enough to match this catalog's established bar (real style rules and a real ICMJE page-truncation algorithm, hand-cross-checked against published examples, not template-filling), and a clean, well-scoped AI role (structuring the messy minority of free-text references, never touching the deterministic formatting rules).

## Connection to User Context

PROFILE.md names "write grants and manuscripts" as a day-to-day duty and "Literature reviews" as a friction point Claude should help automate. A professor submitting the same manuscript to multiple journals — or reworking a grant's reference list to match a different sponsor's required style — currently has to hand-reformat every reference by hand. No prior build touches citation-style formatting: Citation Vault tracks a personal reading/citation workflow and exports BibTeX; Manuscript Pipeline tracks submission status and auto-detects publication via Crossref; neither reformats a reference list into a specific target style.

## Why Tonight

Category B's own single pending backlog idea turned out to be a stale duplicate of last night's Fleet Drift build (see above), which forced fresh generation rather than a lottery draw. Tonight's build directly closes a gap the two existing citation-adjacent builds (Citation Vault, Manuscript Pipeline) left open.

## What I Hope the User Gets From This

1. A genuine time save the next time a manuscript gets rejected and resubmitted to a journal with a different required citation style — no manual reference-by-reference reformatting
2. Confidence that the reformatted references are actually correct, not just plausible — the style rules were implemented from real style-guide specifications and cross-checked against hand-verified worked examples in tests, the same rigor this catalog applies to its statistical/algorithmic builds
3. A tool usable both as a one-off CLI run and, via the companion Skill, invoked mid-session ("format this reference list in AMA style") without leaving Claude Code

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| SubmitCheck: Manuscript Formatting Compliance Checker | B | Would need a hand-authored library of per-journal submission requirements (word count, reference-count ceiling, structured-abstract rules) with no live, verifiable source for those numbers inside this build container — closer to guesswork than this catalog's pattern of cross-checking against a real published standard. Logged to `builds/ideas.md` (#39) as worth building if scoped to journals the user actually submits to, sourced from those journals' own author guidelines. |
| Batch Release Notes Drafter | B | A real batch-automation shape (conventional-commit changelog drafting across every owned repo via `GITHUB_TOKEN`), but GitHub-sourced tooling is already heavily represented in this catalog (Fleet Drift, Layer Guard, Landing Pattern, ci-pulse, Worklog, Waymark, BugTrace, dep-check, Git Standup Reporter, two repo-health dashboards) — CiteForge reaches an academic-writing friction point with zero prior coverage instead. Logged to `builds/ideas.md` (#40). |
