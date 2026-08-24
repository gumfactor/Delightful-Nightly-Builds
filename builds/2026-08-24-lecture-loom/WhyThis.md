# Why This? — Lecture Loom

> **Date:** 2026-08-24

---

## How This Idea Was Selected

**Selection method:** Lottery draw.

Tonight's category (day-of-year 236 → `(236-1) % 9 = 1` → Category B, Productivity Utility) had two `pending` backlog rows: idea #13 (Course Material Batch Formatter, added 2026-08-15) and idea #14 (Multi-Repo Dependency Batch Auditor, added 2026-08-15). Neither has a numeric rating, so both carry the default 5 tickets (R = 0 → `lottery_chance = 25%`). The gate roll was **2** (≤25%, draw proceeds). The weighted draw between the two 5-ticket ideas (rolled 1–10) came up **4**, landing in idea #13's 1–5 range. Idea #13 wins outright — no override was applied.

## The Decision

Idea #13's own Rating Notes (written 2026-08-15, when it lost to Provenance) flagged a specific risk rather than a factual staleness problem: it shares AI Lecture Builder's (2026-06-24, 2/10) failure mode — an AI-prose wrapper with no deterministic core of comparable weight — and explicitly said it "would need a genuinely verifiable non-AI core... to be worth building." That is a design note to act on, not a reason to re-roll the lottery (CLAUDE.md's override precedent is reserved for verbatim duplicates of already-built work, e.g. SiliconWatch/Dockside/Trading Book overriding stale duplicate draws — this isn't one of those). So the build below is deliberately designed around a load-bearing deterministic engine: a word-count-based lecture-timing budget check, objective-completeness detection, and section-density/structure-consistency checks, each independently useful and independently testable with zero API key. Claude Haiku only polishes bullet phrasing and drafts discussion questions on top of that — it never invents the structure, timing numbers, or flags.

## Connection to User Context

PROFILE.md names "Course material creation" directly under "Things you do manually that you suspect could be automated," and separately lists three courses currently taught (Stress and Coping, Social Affective Neuroscience, AI Applications for Psychologists) plus "developing new AI-focused university courses" and "updating neuroscience curriculum" as active work. No prior build addresses turning raw lecture notes into a presentation-ready, time-budgeted format — Curriculum Atlas (2026-08-16) builds a cross-course concept knowledge base from already-written syllabi, a different problem (concept overlap/objective-gap detection across courses) from this build's per-lecture format-and-timing-verification problem.

## Why Tonight

Tonight is a Category B (Productivity Utility) night by the fixed 9-day rotation, and the lottery drew this idea from the backlog rather than requiring fresh generation.

## What I Hope the User Gets From This

1. A fast way to turn rough lecture notes into a consistent, presentable outline + handout without re-formatting every file by hand.
2. An honest, computed answer to "will this lecture run long?" before walking into the room, not a guess.
3. A batch-wide view (via the HTML dashboard) of which lectures in a course are missing objectives or badly unbalanced in section length — the kind of quality check that's easy to skip when writing notes one lecture at a time.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Multi-Repo Dependency Batch Auditor (idea #14) | B | Lost the weighted lottery draw (rolled 4 of 10, needed 6–10) — not a judgment call, the dice landed on idea #13. |
| Building idea #13 exactly as originally described (AI-only reformatting pass) | B | Would repeat AI Lecture Builder's (2026-06-24, 2/10) documented failure mode almost exactly; idea #13's own Rating Notes call this out directly, so the deterministic timing/consistency engine was made the core feature instead of an afterthought. |
