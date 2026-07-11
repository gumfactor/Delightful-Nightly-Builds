# Why This? — Pipeline Pulse

> **Date:** 2026-07-09

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day-of-year 190, `(190-1) % 9 = 0`) is **A — Dashboard / Visualizer**. `builds/ideas.md` had 3 pending Category-A ideas (IDs 3, 5, 6); only ID 3 had a numeric rating (4), so `R = 1` and `lottery_chance = min(75, 25 + 1*2) = 27%`. A cryptographically random roll (`secrets.randbelow(100) + 1`) came up **73**, which is above the 27% threshold, so the lottery was skipped in favor of fresh ideas per the documented process.

## The Decision

Idea 5 in the pending pool ("GitHub Repository Health Scorecard: pull all repos via `GITHUB_TOKEN`, generate an HTML health scorecard") is effectively a duplicate of the already-built 2026-06-21 build of the same name — it just never got marked `built`. That, combined with the fresh-idea roll, ruled out drawing from the existing pool even before generating new ideas.

While orienting for tonight, I ran connectivity checks against this session's actual network policy (see PRD.md "Scope Changes") and discovered two things that shaped everything else: (1) direct GitHub REST API calls with `GITHUB_TOKEN` return `403 GitHub access is not enabled for this session` — the env var here is a proxy placeholder, not a real PAT — and Open-Meteo/Yahoo Finance/Wikipedia/SEC EDGAR/PubMed are all blocked at the proxy too; and (2) `main` on this very repo is stuck at the 2026-06-18 build while the catalog on the most recent open PR branch lists 32 completed builds through 2026-07-08 — meaning roughly three weeks of nightly output, across ~14 separate branches, has never been merged.

That second fact is exactly the kind of thing a Dashboard/Visualizer build should surface, and it's derivable entirely from local `git` plumbing (branch ancestry, `git diff --name-only`) with zero dependency on the APIs that were unreachable tonight. I generated three fresh candidates and picked the one that turned tonight's own constraint-discovery into the build itself.

## Connection to User Context

PROFILE.md explicitly lists "managing many simultaneous projects" and "context loss between AI sessions" as recurring friction points, and this build is a direct instrument for the first one — applied to the nightly-build system itself. It also fits the stated preference for "tools that preserve context across sessions" and the operator's own described mode of "running many projects simultaneously."

## Why Tonight

Category A came up in the fixed rotation. The build folder discovery in Step 0/1 (checking for interrupted builds, resyncing `builds/index.md` from the most recent open PR) is what surfaced the backlog fact in the first place — this build turns a routine orientation step into the night's dashboard.

## What I Hope the User Gets From This

1. A clear, current picture of how much AI-generated nightly output is sitting unreviewed, and which build has been waiting longest — actionable via a direct compare/PR link.
2. Visibility into rating coverage (only 36% of builds have ever been rated as of tonight), which is a lever the user directly controls to sharpen future lottery-weighted picks.
3. A reusable tool: rerun any night to check pipeline health, with zero setup and zero external credentials required.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Canadian Economic Pulse Dashboard (Statistics Canada WDS API indicators + AI narrative) | A | `www150.statcan.gc.ca` returned a `403` at this session's proxy — could not verify the core data path would work, and PROFILE.md's "Canadian government open data" claim did not hold in this sandbox. |
| Idea Backlog Visualizer (parse `builds/ideas.md` into an interactive lottery-weight/status dashboard) | A | Real and buildable, but narrower value than reconciling the actual merge backlog; kept as a fresh idea in `builds/ideas.md` for a future night. |
| PyPI Dependency/Trend Explorer (`pypi.org` JSON API, confirmed reachable) | A | No download-stats data without `pypistats.org` (unconfirmed reachable) and unclear daily value to this specific user; kept in `builds/ideas.md`. |
