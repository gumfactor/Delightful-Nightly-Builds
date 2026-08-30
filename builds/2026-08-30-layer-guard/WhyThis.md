# Why This? — Layer Guard

> **Date:** 2026-08-30

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

The resynced `builds/ideas.md` (pulled from the most recent open PR branch, `claude/cool-sagan-q2pava`, since the local checkout's copy was stale from mid-June) held exactly one pending Category H row: idea #9, "GitHub Actions Performance Analyzer" (added 2026-06-17). Cross-checking `builds/index.md` showed this is a verbatim duplicate of the already-built `ci-pulse` (2026-06-28, same description). The 2026-08-12 Snipvault build had already caught and corrected this exact row to `skipped` — but since none of this repo's ~30 open nightly-build PRs have ever merged to `main`, and each night's session branches fresh from stale `main` rather than from the previous night's branch, that correction never propagated. Corrected it again in this session's local `builds/ideas.md`, which emptied the Category H pool and routed straight to fresh generation — no random roll was needed since the pool was empty, not merely lost on a lottery draw.

## The Decision

Day-of-year rotation (day 242 UTC) landed on Category H — Developer Tool. Reviewed all 8 prior Category H builds (Git Standup Reporter, dep-check, ci-pulse, Schema Sentinel, AgentLint, BugTrace, Landing Pattern, Snipvault) to avoid duplication; 7 of 9 lean on `GITHUB_TOKEN` and repo/PR metadata, so a build with a genuinely different mechanism and data source was the priority. Chose Layer Guard — a from-scratch import-graph analyzer (Tarjan's SCC for cycle detection, coupling/instability metrics, optional explicit layering-violation checking) — over two other candidates because it ties directly to two things named verbatim in PROFILE.md that no build in 77 prior nights had touched, and because its core logic (a real graph algorithm) gives it the same "verifiable, testable, not just an AI wrapper" shape that this catalog's highest-rated build (Qualtrics Survey Data Inspector, 9/10) shares.

## Connection to User Context

PROFILE.md names "Better understand scalable software architecture" as an explicit learning goal, and separately lists "Overly complex architectures" and "Systems that require constant maintenance" under things to explicitly avoid. The user also describes themselves as running an "increasingly sophisticated" personal software practice — The Canada List, Kwyeter, this very nightly-build catalog — "despite not being a full-time developer" (a named recurring friction point). A tool that surfaces real circular dependencies and architectural layering violations before they compound is a direct, practical answer to both the stated goal and the stated friction, not a generic "developer productivity" build with no specific tie.

## Why Tonight

Category H comes up once per 9-day rotation; the last Category H build (Snipvault, 2026-08-12) explicitly noted breaking from the `GITHUB_TOKEN`-heavy pattern of prior Category H builds, and this build continues that trajectory — it needs no external API or credentials at all, working purely on local source files via `ast`. It's also the first build in the catalog to analyze *this repository's own codebase's* internal architecture (Waymark and Pipeline Pulse analyzed this repo's git/PR history, but nothing before tonight has looked at import structure).

## What I Hope the User Gets From This

1. A quick, zero-setup way to sanity-check any of their Python projects (this repo, future ones, or existing scripts) for circular imports before they cause a confusing `ImportError` at the worst moment.
2. A concrete, numeric answer to "is this module doing too much / too tangled?" via the instability/coupling metrics, rather than a vague feeling that a file has grown unwieldy.
3. A lightweight way to *declare* an intended architecture (via `layers.json`) and get told immediately when new code violates it — useful as a project grows past the point where one person can hold its whole shape in their head.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|-----------------|
| Dead Code Detective — AST-based reachability analysis to flag unused Python functions/classes, with confidence tiers for dynamic-dispatch cases | H | Strong candidate and still worth building — but "find things to delete" is a narrower, more clean-up-oriented value proposition than "understand and enforce your architecture," and the latter maps to a PROFILE.md learning goal verbatim while the former doesn't map to any named friction point as directly. |
| Test Flakiness Static Scanner — rule-based scan for pytest/JS non-determinism patterns (unseeded random, real `time.sleep`, unmocked network calls, `datetime.now()`) | H | Genuinely useful and untouched by any prior build, but it's fundamentally a linter (a rule-matching pass), with less algorithmic depth than a real graph analysis — closer in shape to AgentLint (2026-07-16) than to this catalog's more mathematically substantial builds, and would have been the second "static linter over text patterns" tool in the category. |
| API Surface / SemVer Diff Checker — classify public-API changes between two git refs as breaking/additive/patch | H | Passed over deliberately: it's structurally very close to Schema Sentinel's (2026-07-07) "structural diff → breaking-change classification" shape, just applied to code instead of data schemas — too close a mechanic repeat to the same category's own recent history. |
