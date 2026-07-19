# Why This? — Protocol Forge

> **Date:** 2026-07-19

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day of year 200, `(200-1) % 9 = 1`) is B — Productivity Utility. The only two Category B rows in `builds/ideas.md` (#4 Cross-Agent Project Activity Workstreams, #7 Morning Briefing) are both already marked `built` — the pending pool for Category B was empty, so the lottery was skipped entirely and fresh-idea generation ran per Step 2d.

## The Decision

With no backlog to draw from, I scanned `builds/index.md` for the last 10 builds and PROFILE.md's named friction points to find a Category B idea that hasn't been touched. Category B already contains a context-capture tool that scored poorly for being pure manual note-taking (2026-06-06, 3/10), a multi-source digest criticized as redundant with existing scheduling tools (2026-06-22, 5/10), a neuroimaging dataset validator, and a cross-agent activity correlator. None of those cover "Ethics application generation," which PROFILE.md names explicitly and specifically as a friction point, and which no build in the 38-entry catalog has ever addressed. I generated three candidates and chose Protocol Forge over the other two because it has the clearest, most concrete tie to a named friction point and the strongest built-in differentiator against the "power user replicates this with one Claude prompt" critique that sank the 2026-06-24 AI Lecture Builder (2/10): a persistent, approval-gated boilerplate library that a single chat prompt cannot replicate, plus a deterministic compliance-rule engine that works with zero AI involvement.

## Connection to User Context

PROFILE.md's "Things you do manually that you suspect could be automated or aided by a tool" lists "Ethics application generation" directly, alongside "Grant writing" and "Research administration" — all reflecting the user's role as an Associate Professor and lab director who runs human-subjects neuroscience research and must repeatedly write, renew, and amend IRB protocols. This is squarely inside "reduce friction, preserve context, automate repetitive work" from the profile's opening framing, and it is a task type (structured compliance + reusable institutional boilerplate) with no existing tool in the user's stack (Teamwork.com and Coda are project/doc tools, not protocol-compliance checkers).

## Why Tonight

Category B comes up once every 9 nights in the rotation, and tonight's roll landed on it with an empty backlog — the ideal condition for introducing a genuinely new topic domain rather than repeating GitHub-analytics or investment-dashboard patterns the preference prior already warns are saturated in other categories. This is the first build in the catalog to touch human-subjects research administration specifically (distinct from GrantScope's funding-data focus and Research Question Forge's hypothesis-generation focus, both of which sit in the adjacent-but-different "grant writing" friction point).

## What I Hope the User Gets From This

1. A faster first draft the next time an IRB protocol, renewal, or amendment is due — structured input in, compliance-checked draft out, in minutes instead of starting from a blank institutional template.
2. A safety net that catches the specific regulatory gaps reviewers most often kick a protocol back for (missing debrief plan for deception, no security language for identifiable data, undocumented risks) before submission, not after a rejection.
3. A library that gets more valuable every time it's used — the first protocol takes full drafting effort, but every subsequent protocol sharing population type or data-sensitivity characteristics reuses real, previously-approved language instead of being rewritten from scratch.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| GradeFlow — batch rubric-based grading/feedback assistant (ingest a CSV rubric + folder of student submissions, produce per-criterion Claude-scored feedback and a consistency-drift check across the batch) | B | Strong second choice, ties directly to the "Student evaluation workflows" friction point. Not chosen because it requires a folder of real or realistic student submission text to test meaningfully, which risks either fabricating plausible-looking student data (a subtler version of the "personal data" concern) or testing only against thin synthetic fixtures that wouldn't demonstrate real value. Protocol Forge's structured JSON input sidesteps this by design. Worth building in a future B rotation. |
| Grant Budget Justification Builder — generates a funder-format budget narrative from structured line-item input, with a completeness checker for required budget elements | B | Reasonable idea, but the "grant writing" friction point already has two adjacent builds in the last 8 nights (GrantScope, 2026-07-14; Research Question Forge, 2026-07-12), while "Ethics application generation" has zero. Prioritized topic novelty within the category. |
| Repo Onboarding Doc Generator (auto-generate a new-contributor guide from a repo's structure/README/recent commits) | B / H overlap | Discarded early — this repo's catalog already has heavy GitHub-analytics representation (Repository Health Scorecard, ci-pulse, two Developer Analytics Dashboards, Pipeline Pulse, Worklog, AgentLint); another GitHub-data-driven build risks the exact saturation pattern the Rating Notes repeatedly flag. |
