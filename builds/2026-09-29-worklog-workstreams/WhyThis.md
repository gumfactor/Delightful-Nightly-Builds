# Why This Build

**Selection path:** lottery. Day-of-year 272 → category index 1 → **B — Productivity Utility**. Pool: 2 pending B ideas (#4, #7), 2 rated → R=2, lottery chance 29%. Roll: 28 → draw. Weighted tickets: #4 (rating 9) vs #7 (rating 8); drew **#4 Cross-Agent Project Activity Workstreams**.

**Idea brief:** `builds/idea-briefs/cross-agent-project-activity-workstreams.md`, read in full before the PRD. The PRD has a traceability table. Deviations: no optional LLM synthesis; only Claude Code has an automatic capture path; no MCP/skill packaging yet.

**Why it earns a place:** the profile lists "context loss between AI coding sessions", "managing many simultaneous projects" and "re-establishing context across AI sessions" as recurring friction. Earlier related builds (Session Context Bridge, Standup Reporter, Morning Briefing) were single-source summaries. This one keeps a durable ledger and answers the questions they can't: which commits, PR, CI runs and agent sessions belong to the same objective, why a decision was made, and whether an agent's last checkpoint is still true.

**Calibration against past ratings (all ≤6):** low scores came from overlap with existing tools and from lacking a differentiating layer. Native session resume and handoff skills cover one provider's conversation; nothing covers cross-provider correlation with evidence and staleness checks. It reads real data (git, GitHub via `GITHUB_TOKEN`) and needs no manual diary. Honest risk: it is a CLI (category B permits it), and its value depends on checkpoints being captured — hence the working hook.

## Overlap with the 2026-07-10 "Worklog" build (found mid-session)

`builds/index.md` on `main` is months stale; the lottery ran against that stale copy. After the build was written I synced the index from the newest open PR branch and found idea #4 was already built on 2026-07-10 (on an unmerged branch). I did not import or read that build's code. Rather than discard a finished, tested build, this ships as a second-generation implementation that closes gaps against the brief's own requirements, which the July row's description shows it left open:

- **Automatic capture** (brief: "at least one automatic capture path must work end to end"): the July build lists checkpoints as "manually-ingested". This build adds a working Claude Code Stop/SessionEnd hook.
- GitHub reviews and CI check runs as events; failing CI / changes-requested drive `blocked`.
- Weak signals never silently merge: >=0.75 merge labelled `[inferred]`, 0.4-0.75 only suggestions; user merge/split/rename/resolve overrides.
- Secret redaction before persistence; `purge`; config exclusions; per-view provenance labels.

If the July build is already what you want, this one can be discarded; the two should not both be kept.
