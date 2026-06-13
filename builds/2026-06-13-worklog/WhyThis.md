# Why This? — worklog: Cross-Agent Project Activity Workstreams

> **Date:** 2026-06-13

---

## How This Idea Was Selected

**Selection method:** Lottery draw from `builds/ideas.md`

Tonight's category was B (Productivity Utility), rotation index 1 from day-of-year 164. Complexity target was Ambitious Project (Saturday). The filtered backlog pool contained two pending Category B ideas: ID 4 (ambitious, rated 9) and ID 5 (focused, rated 8). With R=2 rated ideas, lottery chance = 29%. Rolled 17 ≤ 29 → lottery fires. Weighted draw: ID 4 holds 9 tickets, ID 5 holds 8 tickets (17 total). Ticket 7 drawn → **ID 4 wins: Cross-Agent Project Activity Workstreams**.

## The Decision

This idea has a detailed Idea Brief (rated 9, the highest-rated item in the backlog) and is exactly the right complexity for a Saturday Ambitious build. The brief was read in full before the PRD was written. The core design — correlating Git, GitHub, and agent activity into evidence-backed workstreams — directly addresses the user's most persistent operational friction: having to manually reconstruct project state every time a new AI session begins.

The two prior rated builds both scored low for opposite reasons: one (3/10) automated the wrong layer and required manual discipline; the other (1/10) duplicated existing tools. This build does neither — it captures evidence that doesn't exist anywhere else (decisions, rationale, cross-agent context) and requires zero manual note-taking to deliver value.

## Connection to User Context

From PROFILE.md: "I tend to run many projects simultaneously and benefit enormously from tools that preserve context across sessions." Context loss between AI coding sessions is listed explicitly as a recurring friction point. The user works across VS Code, Claude, Codex, GitHub Copilot, and Git — precisely the surfaces this tool correlates.

The Idea Brief explicitly absorbs lessons from the first nightly build (AI Session Context Bridge, rated 3/10): that build required manual entry and automated the wrong layer. `worklog` corrects both problems by collecting from Git and GitHub automatically and using checkpoints only for facts that cannot be observed (decisions, intent, blockers).

## Why Tonight

Saturday Ambitious build; the backlog item was added nine days ago and has been waiting for an Ambitious slot. The brief is detailed and ready — no design uncertainty remains. Category B (Productivity Utility) is appropriate: this is a developer workflow tool with immediate daily-use value.

## What I Hope the User Gets From This

1. **Zero-manual-entry project memory** — running `worklog sync` after a work session captures commits, PRs, and issues without writing anything down.
2. **Fresh-agent onboarding in seconds** — `worklog resume` gives any new Claude/Codex session the current objective, decisions made, blockers, and next actions with source evidence rather than a freeform text summary.
3. **A foundation to extend** — the SQLite ledger and YAML checkpoint format are designed for longevity; the MCP server and hook integrations described in the brief can be built on top of this exact storage layer.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Morning Briefing (ID 5) | B | Focused complexity on an Ambitious night — undershoots the target. Also references "Investment Portfolio Snapshot" and "GitHub Repository Health Dashboard" that haven't been built, making it incomplete as described. |
| Fresh idea: Investment Research Dashboard (A/ambitious) | A | Tonight's category is B, not A. Category rotation is fixed. |
| Fresh idea: Lab Research Project Tracker (A/ambitious) | A | Same category mismatch. Also rated 4/10 in backlog — user already uses Teamwork.com for this. |
