# Why This? — Counterpoint

> **Date:** 2026-09-20

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category is B — Productivity Utility (day of year 263, `(263-1) % 9 = 1`). Four pending Category B backlog rows matched: #39 (SubmitCheck: Manuscript Formatting Compliance Checker), #40 (Batch Release Notes Drafter), #53 (Meeting Action Item Extractor), #54 (Course Accessibility Auditor) — all with blank ratings, so R = 0 and `lottery_chance = min(75, 25 + 0*2) = 25%`. A random roll of 1–100 came back **97**, which is above the 25% threshold, so the lottery was skipped in favor of fresh idea generation. Pool size at the gate: 4 pending Category B rows.

## The Decision

I generated three fresh Category B candidates and picked the one with the strongest combination of real, named friction, a genuinely untouched niche, and a deterministic core that AI only polishes rather than drives:

1. **Counterpoint** (winner) — a "Response to Reviewers" letter generator with a deterministic completeness gate, optional AI prose-polishing layer.
2. Literature Review Batch Synthesizer — passed over: the literature/paper-ingestion domain is already heavily covered (Paper Lens, Preprint Pulse, Throughline, CaseForge all touch it), so a fourth build in that space risked reading as a mechanic repeat rather than something new.
3. Course Syllabus Policy Auditor — passed over: no live, verifiable source of "current" institutional policy language exists inside this build container, so the compliance checks would have been guesswork rather than checked against a real standard (the same reason SubmitCheck, backlog idea #39, keeps getting passed over).

I specifically checked for and ruled out an IRB/ethics-application angle — Protocol Forge (2026-07-19, also Category B) already owns that exact niche with a deterministic, AI-free compliance rule engine, and two backlog notes (#15, #34) confirm it's treated as the settled build for "ethics protocol drafting." Building a second one would have been a direct duplicate, so I moved to the next-strongest real gap instead: nothing in 97 prior builds touches the post-review-response stage of the publication pipeline, even though CiteForge (references), Voiceprint (prose style), and Panel Prep (pre-submission critique) all sit immediately adjacent to it.

## Connection to User Context

PROFILE.md names "write grants and manuscripts" as a core weekly activity and lists "Blog writing and editing" and general manuscript-adjacent admin under "Things you do manually that you suspect could be automated." A revise-and-resubmit response letter is one of the highest-stakes documents in that pipeline — reviewers and editors explicitly check that every comment was addressed, and a silently-skipped point is a common, embarrassing reason a resubmission gets bounced back for another round. This tool makes that failure mode structurally impossible: the `build` command refuses to emit a letter with a silently-missing response.

## Why Tonight

Category B is due tonight per the fixed 9-day rotation, and the last Category B build (GradeLine, 2026-09-11) handled the grading side of academic writing rather than the publication side, leaving this niche open.

## What I Hope the User Gets From This

1. A faster, lower-error path through the single most tedious part of every revise-and-resubmit: turning scattered response notes into a properly numbered, complete letter.
2. A structural guarantee (not just a reminder) that no reviewer comment is ever silently dropped from the final letter.
3. An AI layer that saves drafting time on tone/register without ever risking the AI inventing a scientific claim the author didn't actually make — a distinction I made a hard rule in `ai_polish.py`, not just a norm.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|-----------------|
| Literature Review Batch Synthesizer | C/F-adjacent, considered for B | The literature-ingestion domain (arXiv/PubMed/Semantic Scholar) already has four prior builds (Paper Lens, Preprint Pulse, Throughline, CaseForge); a fifth would read as saturation rather than a new angle. |
| Course Syllabus Policy Auditor | B | No live, verifiable "current institutional policy" data source exists in this build container — would have required guessing at rules rather than checking against a real, citable standard. |
| IRB/Ethics Application Drafter | B | Direct duplicate of the already-built Protocol Forge (2026-07-19), which owns this exact niche with a deterministic compliance engine; confirmed via two backlog notes (#15, #34) that flag it as the settled build for ethics-protocol drafting. |
