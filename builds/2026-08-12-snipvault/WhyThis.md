# Why This? — Snipvault

> **Date:** 2026-08-12

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day-of-year rotation: day 224 → `(224-1) % 9 = 7` → Category H — Developer Tool. The Category H backlog held exactly one `pending` row (#9, "GitHub Actions Performance Analyzer"), but it is a verbatim duplicate of the already-built 2026-06-28 `ci-pulse` build (identical scope: `GITHUB_TOKEN` workflow-run timing, failure-rate trend charts, per-job breakdown). That duplicate had already slipped through one prior lottery draw undetected (2026-08-03, Landing Pattern) — corrected tonight in `builds/ideas.md` (marked `skipped` with a note) before running the draw, which left the filtered pool empty and skipped straight to fresh generation, per Step 2c.

## The Decision

Generated three Category H candidates: Snipvault (personal code-snippet library, Skill + CLI + optional AI enrichment), a Node/npm equivalent of dep-check's dependency-freshness scan, and a per-file git-archaeology narrator. The latter two were structurally reruns of existing builds with a swapped ecosystem or narrower lens (see Alternatives Considered), so they were passed over and logged as backlog ideas #21/#22 rather than built. Snipvault is genuinely untouched ground: "snippet library" is one of CLAUDE.md's own named Category H examples, and — checking the last 10 builds plus the full H history (Git Standup Reporter, dep-check, ci-pulse, Schema Sentinel, AgentLint, BugTrace, Landing Pattern) — seven of nine prior Developer Tool builds lean on `GITHUB_TOKEN`. Snipvault deliberately breaks that pattern: it needs no GitHub API at all, working purely on code the user writes locally.

## Connection to User Context

PROFILE.md names the user as someone who "codes regularly with AI assistance... and increasingly function[s] like [a software engineer] in practice," runs "many simultaneous projects" (The Canada List, Kwyeter, the lab, this nightly-build repo), and lists "Context loss between AI coding sessions" and "Managing many simultaneous projects" as recurring friction points. A snippet the user wrote for one project (a regex, a SQL pattern, an httpx retry wrapper) is currently only findable by remembering which repo and file it lives in, or by re-deriving it or re-prompting an AI assistant for it. Snipvault targets that specific gap directly.

## Why Tonight

Category H's rotation slot landed tonight, and Step 2f's explicit guidance for productivity/developer-tool builds — "A Routine, Skill, Hook, or MCP server is usually a better fit than a standalone script" — has been present in CLAUDE.md for weeks but only loosely honored so far (AgentLint shipped a Skill wrapper as a companion, not the primary interface). Tonight's build takes that guidance seriously: the CLI is fully capable standalone, but the primary intended usage pattern is the companion Claude Code Skill invoked mid-session ("save this as a snippet," "find my snippet for X"), which turns a push tool into a pull tool exactly as PROFILE.md's Data Sources section recommends.

## What I Hope the User Gets From This

1. A reflex-speed way to capture reusable code the moment it's written, instead of it living only in one project's git history
2. A search that works by meaning ("the function that dedupes a list preserving order") rather than requiring an exact remembered title
3. A working example of a Claude Code Skill that wraps a local tool cleanly enough to copy into any other project

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Node/npm Dependency Freshness & Advisory Checker | H | Real gap (dep-check, 2026-06-19, is Python-only) but structurally a near-rerun of an existing build with the ecosystem swapped, not a new tool shape. Logged as backlog #21. |
| Git File Archaeology Narrator | H | Too close to Waymark's (2026-08-07) git-log heuristic-scoring + optional Claude-narrative shape; a per-file narrative is a smaller variation on already-covered ground. Logged as backlog #22. |
| (Backlog #9) GitHub Actions Performance Analyzer | H | Verbatim duplicate of the already-built `ci-pulse` (2026-06-28); corrected to `skipped` in `builds/ideas.md` rather than built again. |
