# Why This? — AI Session Context Bridge (ctxlog)

> **Date:** 2026-06-06

---

## The Decision

Tonight is Saturday, which calls for an Ambitious Project. This is the first build in this repo, so all categories are open. Category B (Productivity Utility) was chosen because the user's profile lists "context loss between AI coding sessions" as their top recurring friction point — a problem that is specific, concrete, and addressable tonight with a standalone Python CLI. The tool needed enough logic to justify Ambitious scope: a storage layer, a journal API, a search engine, a handoff generator, and a full CLI — eight source files of real substance.

## Connection to User Context

This connects directly to how the user works every day. They use multiple AI coding assistants (Claude, ChatGPT, Codex, Copilot) across many simultaneous projects — The Canada List, Kwyeter, their neuroscience lab, investment research, and course development. Each new session starts cold. The handoff problem is real, recurring, and apparently unsolved for them. This tool gives them a lightweight way to end every session with a 30-second `ctxlog add`, then start the next with `ctxlog handoff --project canada-list | pbcopy` to instantly prime the new AI context.

## Why Tonight

No previous builds to sequence from, so anything is fair game. The productivity friction point was the strongest signal — it's mentioned explicitly in PROFILE.md as both a recurring friction and something they suspect could be automated. There's also a satisfying fit between the *tool itself* and *the system that generates it*: a nightly build session is exactly the kind of context that gets lost overnight.

## What I Hope the User Gets From This

1. **Immediate daily use** — they can start using `ctxlog add` at the end of every AI session tonight and have a 3-session history within days.
2. **A handoff template that actually works** — the generated markdown is structured specifically to prime an AI assistant's context: current state, next steps, active files, and recent history in that order.
3. **A foundation to extend** — the storage format is simple JSON, the search is plain text, and every module is under 100 lines. It can be extended with tags, priorities, or export formats easily.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| The Canada List CSV Quality Inspector | F — Data Explorer | Very relevant to active project, but requires Playwright browser testing which adds setup complexity. Saving for a future Solid Feature build dedicated to that specific pipeline. |
| Personal Investment Research Notebook | A — Dashboard/Visualizer | User's investing interest is strong, but a browser dashboard without live data is mostly a UI exercise. More value when paired with real data ingestion. |
| Lab Research Project Tracker | A — Dashboard/Visualizer | Useful for the lab, but less daily-use than context bridging; also overlaps with existing tools the user likely has (Teamwork, Coda). |