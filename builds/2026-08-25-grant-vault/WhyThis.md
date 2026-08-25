# Why This? — Grant Vault

> **Date:** 2026-08-25

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category is C — Personal Knowledge Tool (day-of-year 237, `(237-1) % 9 = 2`). `builds/ideas.md` had two pending Category C entries: #15 "Lab Method / SOP Knowledge Base" and #16 "AI Workflow & Prompt Cookbook," both blank-rated (5 tickets each, R = 0 rated entries). `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 68/100 (via `secrets.randbelow`) — above the 25% threshold, so the fresh-idea path was taken instead of a draw. Pool size at roll time: 2 pending Category C ideas.

## The Decision

Category C already has eight prior builds (Investment Thesis Journal, Paper Lens, PubMed Research Radar, Connectome, CanFile, Citation Vault, Waymark, Curriculum Atlas), so the topic-diversity bar was high — the space is genuinely crowded with paper-discovery feeds, note graphs, and domain-specific card libraries. Scanning `PROFILE.md`'s explicit friction list, "Grant writing" and "Research administration" stood out as named pain points with no matching build anywhere in the catalog: GrantScope (F, 2026-07-14) discovers *external* funding opportunities via NIH RePORTER, Effort Ledger (F, 2026-08-19) audits budget *compliance*, and Protocol Forge (B, 2026-07-19) checks IRB/ethics *compliance* — none of them help with the actual writing. Grant Vault fills that specific gap: a personal library of the user's *own* proven grant prose, organized and retrievable by section.

## Connection to User Context

PROFILE.md lists "Grant writing" and "Ethics application generation" directly under "Things you do manually that you suspect could be automated or aided by a tool," and the user runs an active research lab with recurring grant cycles (career stage: "Established enough to run an independent research program... increasingly focused on expanding beyond traditional academia"). A tool that turns every past grant into reusable, section-tagged, quality-scored language directly serves the #1-ranked build outcome in PROFILE.md: "Things that save me real time."

## Why Tonight

Category C comes up on the fixed 9-day rotation; tonight was its turn. No lottery draw occurred (see above), so this is a fresh idea generated specifically to avoid duplicating the eight existing Personal Knowledge Tool builds while still serving a documented, unmet friction point.

## What I Hope the User Gets From This

1. A faster starting point for every future grant section — search "broader impacts" or "data management" and get back their own best prior language instead of a blank page
2. A concrete, deterministic reusability signal (not just a pile of old drafts) that tells them at a glance which paragraphs are safely portable across submissions versus anchored to one specific proposal
3. Zero-setup privacy by default — the tool works entirely offline against their own files; AI enrichment is opt-in and documented, never silent

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Highlight Vault — a personal database of paper highlights/quotes extracted from already-read papers, thematically clustered via AI | C | Real value, but sits close to Citation Vault (2026-07-29)'s reading-workflow tracker and Connectome (2026-07-11)'s note-graph — three tools all doing "personal library of text snippets with AI tagging" starts to blur together. Grant Vault's target text (grant prose) and its scoring dimension (reusability, not thematic relevance) are more clearly distinct from anything already built. |
| Supervision Notebook — a private per-student/RA mentorship log with AI synthesis of recurring themes across mentees | C | Genuinely useful and ties to "student evaluation workflows," but the value depends on sustained manual note entry after every meeting (the exact pattern that scored AI Session Context Bridge a 3/10: "requires manual entry to be useful"). Grant Vault instead mines documents the user already has, no new logging habit required. |
| Lab Method / SOP Knowledge Base (backlog #15) | C | Left pending rather than drawn — its own backlog note flags too much overlap with Protocol Forge's (2026-07-19) rule-engine-completeness-checking approach to be clearly distinct yet. Not revisited tonight since a stronger, cleanly-differentiated idea (Grant Vault) was available. |
