# Why This? — Schema Sentinel

> **Date:** 2026-07-07

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category rotation (day of year 188, `(188-1) % 9 = 7`) landed on **H — Developer
Tool**. The backlog had exactly one `pending` H-category row (#9, "GitHub Actions
Performance Analyzer") — but that idea is a near-duplicate of the already-shipped
2026-06-28 ci-pulse build, so it carried a blank rating (`R = 0`), giving a lottery chance
of `min(75, 25 + 0*2) = 25%`. I rolled 81/100, which sent selection to fresh-idea
generation (Step 2d) rather than drawing that stale duplicate.

## The Decision

Before generating ideas, I confirmed this session's egress proxy returns HTTP 403 for
every external host tested (Open-Meteo, unauthenticated `api.github.com`), direct `curl`
from Bash is denied outright by the permission layer, and `ANTHROPIC_API_KEY` is not set
(only `ANTHROPIC_BASE_URL` is). This is the same constraint every build session since
2026-07-02 has hit and documented. Rather than write another "real API code path that
can't be exercised live tonight" build, I picked an idea whose entire core value works
with **zero network access**, so it could be fully built and tested end-to-end this
session rather than shipped on faith. GitHub-based developer tools are also the most
saturated topic in the catalog (4 of the last 10 builds), and the last H-category build
itself (ci-pulse, 06-28) was already GitHub-API-based, so a second GitHub tool back-to-back
would have been redundant on top of being untestable tonight.

## Connection to User Context

PROFILE.md names "keeping multiple data systems synchronized" and "The Canada List
ingestion and quality control pipeline" as explicit recurring friction points, and lists
"reduce friction, preserve context, automate repetitive work" as the throughline across
all of the user's projects (Canada List, Kwyeter, lab data pipelines, investment
automation). Every one of those projects involves data moving between systems — a
scraped/exported CSV feeding an ingestion pipeline, a Qualtrics export feeding an analysis
script, a JSON API response feeding a dashboard built in a prior nightly session. A quiet
field rename or type change anywhere in that chain is exactly the kind of failure that
surfaces as a confusing downstream bug days later rather than an immediate, legible error.
Schema Sentinel is the tool that would have caught that at the moment of change.

## Why Tonight

Category H (Developer Tool) explicitly lists "schema inspector" and "diff tool" as example
shapes in CLAUDE.md's rotation table — this build is literally both at once. It also
follows directly from the 2026-06-08 Quick Data Profiler verdict ("totally redundant with
`pandas.describe()`" — 1/10): that build failed because single-file descriptive statistics
duplicate a one-line pandas call. Schema Sentinel is deliberately not that — it does
**comparative, structural drift detection across versions or git history**, with explicit
breaking/risky/safe classification, which `df.describe()` has no concept of at all.

## What I Hope the User Gets From This

1. A tool to run before trusting a new export from any pipeline (Canada List ingestion,
   Qualtrics, a partner API) against the last known-good version, catching breaking
   changes before they corrupt downstream processing.
2. A `history` view that turns "when did this data file's shape change?" from an
   archaeology exercise (`git log -p`, squinting at diffs) into a structured, severity-
   ranked timeline in one command.
3. A CI-gateable exit code (`--fail-on breaking`), so this can be dropped into any
   pipeline's pre-processing step as a safety check, not just a manual tool.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Local CLI Snippet Library (as a Claude Code Skill, `/snippet save`/`/snippet get`) | H | Genuinely useful and profile-aligned ("tools I'll use daily/weekly" ranks #2), but overlaps heavily with existing tools the user likely already has (VS Code snippets, GitHub Gists) — the differentiator (Skill-native invocation) felt thinner than Schema Sentinel's structural-diff capability, which nothing in the user's stack already does. Recorded for a future night. |
| Env Var & Secrets Hygiene Scanner (scan repo(s) for hardcoded secrets, missing `.env.example` entries, inconsistent var usage) | H | Real value, but this exact niche is already well-served by mature dedicated tools (gitleaks, truffleHog, git-secrets) — same redundancy failure mode that sank the 2026-06-08 Quick Data Profiler (1/10, "trivially handled by existing tools"). |
| GitHub Commit Semantic Theme Explorer (backlog #18) | F | Interesting, but explicitly logged in `builds/ideas.md` as a 5th-GitHub-build risk on 2026-07-05 — still true tonight, and doubly so since tonight's category (H) already had a GitHub-based build two nights ago (ci-pulse). Left pending for a night with more GitHub headroom. |
