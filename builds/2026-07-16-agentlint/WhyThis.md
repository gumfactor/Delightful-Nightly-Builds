# Why This? — AgentLint

> **Date:** 2026-07-16

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

`builds/ideas.md` had exactly one Category H row (#9, GitHub Actions Performance Analyzer) and it was already marked `built` (realized as 2026-06-28's ci-pulse). With the filtered pool empty, Step 2d applies directly and no lottery roll was needed — CLAUDE.md skips straight to fresh-idea generation when the category-filtered backlog is empty.

## The Decision

Tonight's category is H — Developer Tool (day-of-year rotation, confirmed against 2026-07-07's Schema Sentinel exactly 9 days earlier). With no backlog candidate, I generated three fresh ideas and picked the one that both fits an unaddressed gap in this repo's own developer-tool history and surfaces a real, concrete problem discovered during tonight's orientation step: `CLAUDE.md`'s calibration note is factually stale relative to `builds/index.md`. The preference-prior notes are explicit that AI processing as a differentiating layer beats mechanical data processing (per the "AI integration signal" guidance), and that duplicating an existing pattern scores poorly — three prior H builds (dep-check, ci-pulse, Schema Sentinel) already own "fetch data and diff/audit it deterministically"; AgentLint's differentiator is using Claude to catch semantic drift that no regex or diff can catch.

## Connection to User Context

PROFILE.md names "context loss between AI sessions" and "managing many simultaneous projects" as recurring friction points, and lists AI workflow management as a domain where a personal tool would add the most value. The user runs several parallel projects each with their own agent-facing instructions (this nightly-build repo's own elaborate CLAUDE.md, and presumably similar files for The Canada List, Kwyeter, and lab tooling) — files exactly like the one this tool audits. The user is also explicitly building this very nightly-build system as a long-running, self-modifying instruction file, making this build almost self-referential: it exists to keep tools like itself honest.

## Why Tonight

This isn't a follow-up to a specific prior build, but it directly grew out of Step 1 orientation tonight: resyncing `builds/index.md` from the most recent open PR branch (per CLAUDE.md's instructions) revealed that `CLAUDE.md`'s "every build has scored 4/10 or below" calibration note is now false — Qualtrics Survey Data Inspector (06-17) scored 9/10, and GitHub Repository Health Scorecard, Morning Briefing, and Paper Lens all scored above 4. That's a live, reproducible instance of exactly the failure mode AgentLint targets, and it made the idea concrete rather than abstract.

## What I Hope the User Gets From This

1. A fast way to sanity-check any CLAUDE.md/AGENTS.md-style file before trusting an agent to follow it — catching broken file references and missing sections in seconds instead of finding out mid-session.
2. A genuinely differentiated use of the Claude API: not summarization or classification of external content, but a semantic audit of the user's own agent-facing instructions against the user's own ground-truth data — something no static linter can do.
3. A reusable Skill the user can drop into any of their other repos' `.claude/skills/` directories to run the same audit on demand, extending the tool's value well past tonight.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Local Secrets/Entropy Scanner + Pre-commit Hook Generator | H | Mature open-source tools (gitleaks, trufflehog) already solve this well; would be a mechanical re-implementation of an existing category with no AI or otherwise-differentiating layer, and risks giving false confidence about secret detection quality. |
| Flaky Test Detector (via GitHub Actions run history) | H | Overlaps heavily with 2026-06-28's ci-pulse (same GITHUB_TOKEN → workflow-run-history → HTML dashboard pattern); also hard to demo meaningfully since this repo's own CI has little real flaky-test history to analyze against, risking a build that looks fine on toy fixtures but is unproven on the user's actual repos. |
| Dependency License Auditor (SPDX cross-reference) | H | Real utility but no clear tie to a friction point named anywhere in PROFILE.md, and less differentiated — mostly a lookup-and-classify task rather than one where AI reasoning adds real value. |
