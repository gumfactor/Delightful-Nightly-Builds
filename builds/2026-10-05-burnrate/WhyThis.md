# Why This? — Burnrate

> **Date:** 2026-10-05

## How This Idea Was Selected

**Selection method:** Fresh generation, after a lottery draw that fell through.

Day-of-year 278 gives index 7, category H. The pending H pool had one row (#9, GitHub Actions Performance Analyzer, no rating). R = 0, so lottery chance was 25%. The roll was 11, which is a draw. But #9 was already built on 2026-06-28 as ci-pulse (the backlog row was never marked `built`), so it fails the novelty requirement. I treated the draw as void and generated fresh ideas. I did not edit `builds/ideas.md` because tonight's task limits writes to the build folder and `builds/index.md`; the stale row #9 should be marked `built` by hand.

## The Decision

Burnrate analyzes the user's own Claude Code transcripts for cost, cache efficiency and wasted effort. Promptbook (09-03) mined transcripts for prompts and Worklog/ctxlog cover handoffs, but nothing in the catalog answers "where do my tokens and dollars go, and which sessions burned effort for nothing". The Claude UI shows neither per-project cost nor Read-thrash and retry-loop detection.

## Connection to User Context

PROFILE.md lists AI workflow management, agentic systems, many simultaneous projects and context loss between AI sessions as core friction. This gives a measured view of that workflow across The Canada List, Kwyeter and lab projects. It is fully local and uses real data on the user's machine.

## Why Tonight

Developer Tool slot. Recent H builds were changelogs (Shiplog), secret scanning, import graphs. This one targets the AI-assisted part of development itself.

## What I Hope the User Gets From This

1. A weekly look at cost per project and model, and dollars saved by caching.
2. Specific, actionable findings (a file read 24 times, a command that failed 16 times, a 160k-token context).
3. A parser and pricing table that other agent formats can plug into.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| GitHub Actions Performance Analyzer (#9, lottery draw) | H | Already built as ci-pulse on 2026-06-28. |
| Flaky-test detector from CI history | H | Overlaps ci-pulse failure-rate analysis. |
| MCP server exposing repo conventions | H | Overlaps AgentLint/Worklog; weaker data story. |
