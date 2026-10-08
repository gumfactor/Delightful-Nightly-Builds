# Why This? — Lookalike

> **Date:** 2026-10-08

## How This Idea Was Selected

**Selection method:** Fresh generation (lottery rolled 1 of 100 against a chance of 29 → draw, but both pending Category B rows were stale: #4 was built 2026-07-10 as Worklog and #7 on 2026-06-22 as Morning Briefing, so the pool was effectively empty). The checked-out `main` copy of `builds/index.md` and `ideas.md` was months behind; the latest catalog was read from the open PR #112 branch. An initial draft of idea #4 was discarded before commit once the duplicate was discovered.

## The Decision

Day-of-year 281 → index 1 → Category B (Productivity Utility). The recent B builds covered academic writing/grading/citations (CiteForge, GradeLine, Counterpoint), ownership lookups (Provenance), and IRB drafts. Nothing yet addresses the Canada List's core ingestion pain: the same business arriving several times under different spellings, suffixes, and URLs. Ingest Gate (08-10) validates CSV shape, not identity.

## Connection to User Context

PROFILE.md lists "The Canada List ingestion and quality control pipeline" among tasks done manually that could be automated and "keeping multiple data systems synchronized" as a friction point. The tool is deterministic first (reliability beats cleverness), with optional Claude adjudication for the ambiguous remainder (the AI-integration signal), and it treats multi-location chains as distinct, which is what a directory needs.

## Why Tonight

Topic diversity: no investment/finance, no academic-writing repeat; a data-hygiene tool for the user's own product.
