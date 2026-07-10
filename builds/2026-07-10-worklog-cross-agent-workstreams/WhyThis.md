# Why This? — Worklog: Cross-Agent Project Activity Workstreams

> **Date:** 2026-07-10

---

## How This Idea Was Selected

**Selection method:** Lottery draw.

Day of year 191 → `category_index = (191-1) % 9 = 1` → Category B (Productivity Utility).
Filtering `builds/ideas.md` to pending Category B ideas found two candidates with numeric
ratings: ID 4 ("Cross-Agent Project Activity Workstreams," rated 9) and ID 7 ("Morning
Briefing," rated 8). Before drawing, I checked both against `builds/index.md` for duplicates:
ID 7 is functionally identical to the already-built and already-rated 2026-06-22 "Morning
Briefing" (same combination of Git/GitHub/portfolio digest, rated 5/10 — the user's notes say
ChatGPT's scheduling feature already covers this). I marked ID 7 `built` retroactively in
`builds/ideas.md` to prevent re-shipping something already rated, rather than let it re-enter
future lotteries. I did the same for backlog ID 9 (GitHub Actions Performance Analyzer),
already realized as the 2026-06-28 "ci-pulse" build, while I was in the file.

That left a Category B pool of one: ID 4, rated 9/10 with a full linked Idea Brief
(`builds/idea-briefs/cross-agent-project-activity-workstreams.md`). With R=1 rated idea in the
filtered pool, `lottery_chance = min(75, 25 + 1*2) = 27%`. Rolled 3/100 → draw. With one
candidate in the pool, it wins outright. Pool size: 1 (after correcting the two stale
"pending" duplicates).

## The Decision

This is the highest-rated idea in the entire backlog (9/10, no rating notes needed — the user
rated it that high at creation) and it comes with a complete, considered Idea Brief that
explicitly diagnoses why two related earlier builds underperformed. Per Step 2e, I read the
brief in full before writing `PRD.md` and treated it as the durable product intent, taking the
"first useful release" vertical slice it defines rather than the full long-term vision.

## Connection to User Context

PROFILE.md names "context loss between AI coding sessions" and "managing many simultaneous
projects" as top recurring friction points, and the user explicitly works across multiple AI
coding agents (ChatGPT, Claude, Codex, Copilot) on multiple concurrent repositories (this
nightly-build repo, The Canada List, Kwyeter, lab infrastructure). "Re-establishing context
across AI sessions" is listed verbatim under things the user suspects could be automated. This
build targets that friction point directly rather than a generic dev-tool novelty.

## Why Tonight

Tonight's category rotation (day-of-year index 1) landed on B — Productivity Utility, which is
exactly this idea's category. It's also directly responsive to the calibration note in
CLAUDE.md: rated builds have consistently scored low when they duplicate functionality already
in the user's stack or require manual data entry. This idea was created specifically to fix
those two failure modes in the two Category B/C builds that came before it (AI Session Context
Bridge, Git Standup Reporter), so building it now closes a loop the backlog itself identified.

## What I Hope the User Gets From This

1. A tool they can point at any of their repos to get an honest "what happened and why" view
   without re-explaining context to a fresh agent session — the exact friction point named in
   PROFILE.md.
2. A durable, evidence-backed record of *why* a decision was made (not just what changed),
   which is valuable across all of the user's simultaneous projects, not just this one.
3. A concrete, inspectable SQLite ledger and JSON checkpoint contract they can extend
   themselves or wire into their other agents' workflows without needing to understand this
   build's internals first.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Backlog ID 7 — Morning Briefing | B | Already built and rated 2026-06-22 (5/10); reusing it would ship a near-duplicate the user already told us underperforms. Marked `built` instead of drawn. |
| Backlog ID 1 — Canada List CSV Quality Inspector | F | Wrong category for tonight's rotation (F, not B); also the user's own rating notes flag ambiguity about whether Playwright adds anything over a pure Python validator. |
| Fresh idea generation | — | Not reached — the filtered Category B pool was non-empty and the lottery roll (3 ≤ 27%) selected a draw before fresh-idea generation would have been considered. |
