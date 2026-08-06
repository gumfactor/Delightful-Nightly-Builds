# Why This? — Manuscript Pipeline

> **Date:** 2026-08-06

---

## How This Idea Was Selected

**Selection method:** Fresh generation (lottery pool was empty).

Day of year 218 → `category_index = (218-1) % 9 = 1` → Category B (Productivity Utility).

Before running the lottery, `builds/ideas.md` was resynced from the most recent open PR branch (`claude/cool-sagan-2525au`, PR #62). Two Category B rows were marked `pending`: #4 "Cross-Agent Project Activity Workstreams" (rating 9) and #7 "Morning Briefing" (rating 8). Cross-checking `builds/index.md` showed both had already been built — #4 as "Worklog: Cross-Agent Project Activity Workstreams" (2026-07-10) and #7 as "Morning Briefing" (2026-06-22) — but neither row was ever flipped to `built`. Left uncorrected, tonight's lottery would have drawn from a pool that was 100% stale duplicates (17 combined tickets, 0 buildable ideas). Both rows were corrected to `built` with a note before proceeding. With the pool empty after correction, the lottery is skipped per `builds/ideas.md`'s own rule ("If no pending ideas exist in the backlog, the lottery is skipped and Claude always generates fresh ideas") — no dice roll needed.

## The Decision

Three fresh Category B candidates were generated (see Alternatives below). Manuscript Pipeline was chosen because it targets a real, named, and so-far-unaddressed friction point (tracking papers through submission → review → revision → publication), has a genuine live-data differentiator (auto-detecting publication via Crossref rather than relying purely on manual updates), and reuses a proven API (Crossref, already validated by Citation Vault, 2026-07-29) rather than requiring a new integration risk.

## Connection to User Context

PROFILE.md names "write grants and manuscripts" under day-to-day work and lists "Research administration" under recurring friction points and things done manually that could be automated. The catalog has built tools for *reading* literature (Paper Lens, PubMed Research Radar), *citing* literature already read (Citation Vault), and *tracking citation impact* of already-published work (Impact Ledger) — but nothing tracks the researcher's own manuscripts while they are still moving through the submission pipeline, which is the stage with the most administrative friction (remembering which journal has which paper, how long a "revise & resubmit" deadline gives you, and whether a "still under review" one has quietly gone live).

## Why Tonight

Category B's own backlog turned out to be entirely stale duplicates once corrected (see above), so a fresh idea was required. Category B's history so far (AI Session Context Bridge 3/10, Morning Briefing 5/10, Worklog 9/10, Protocol Forge unrated, Voiceprint unrated) shows the pattern that scores well is a tool solving one specific, previously-unautomated piece of research administration with a real (not mock) data layer — Worklog's 9/10 is the strongest evidence for that. Manuscript Pipeline follows the same shape: one specific recurring task, a local durable record, and a live API call doing real verification work instead of decorative data.

## What I Hope the User Gets From This

1. One place to see every manuscript in flight and how long it's been sitting in its current stage, instead of remembering it across email threads and journal portals.
2. Automatic detection when a manuscript quietly goes live (a real DOI appears in Crossref) — the kind of status change that's easy to miss until a coauthor mentions it.
3. A faster way to log a decision email (accept / reject / revise-and-resubmit) without retyping journal name, date, and deadline by hand.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Grant Budget & Compliance Tracker — tracks multiple active grants against a manually-logged expense ledger, flags under/overspend pace against the award period, drafts progress-report summary text | B | Real friction point ("Grant writing", "Research administration") but the core signal (spend pace vs. award period) is purely user-entered arithmetic with no live external verification layer — weaker differentiation than Manuscript Pipeline's Crossref auto-detection. Appended to `builds/ideas.md` for a future night. |
| Response-to-Reviewers Letter Builder — paste reviewer comments, AI-assisted point-by-point response drafting with per-comment resolution tracking, exports a formatted letter | B | Genuinely useful but single-session in nature (used once per revision, not something the researcher returns to daily/weekly like PROFILE.md's ranked build-value criteria call for). Better as a `capture`/`update` sub-feature of a manuscript tracker than a standalone build. Appended to `builds/ideas.md`. |
| AI Model Release Radar (backlog #13, already logged 2026-08-05) | A | Wrong category for tonight (Category A, not B) — not considered further tonight beyond noting it remains in the backlog. |
