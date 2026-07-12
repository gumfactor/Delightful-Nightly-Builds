# Why This? — Connectome: Personal Knowledge Graph Builder

> **Date:** 2026-07-11

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day-of-year 192, `(192-1) % 9 = 2`) is **C — Personal Knowledge Tool**. `builds/ideas.md` has zero pending entries tagged Category C (checked after resyncing the catalog from PR #35, the most recent open branch — `main` is currently 27 builds behind), so per Step 2c the lottery is skipped entirely and Step 2d (fresh generation) applies directly — no roll needed.

## The Decision

Before generating ideas, I ran live connectivity checks (Python `urllib`, the same mechanism every recent build in this catalog uses to talk to external APIs) against every free API PROFILE.md lists as available with no credentials. All of them — Wikidata, Wikipedia, Yahoo Finance, Open-Meteo, SEC EDGAR, PubMed, arXiv — returned `403 Forbidden` from this session's egress proxy. Only `api.github.com` was reachable. `ANTHROPIC_API_KEY` is also unset in this session (though `api.anthropic.com` itself connects fine). This ruled out my first two candidate ideas outright (see Alternatives below) and ruled out a GitHub-based idea on redundancy grounds — nine-plus existing catalog builds already mine GitHub activity, several explicitly criticized for overlapping with each other or with GitHub's own UI.

That left a real constraint: build something genuinely useful for Category C using only local, user-owned data. **Connectome** — a local notes indexer that extracts concepts and computes cross-note links entirely offline, with Claude enrichment wired in as an optional, gracefully-degrading layer — satisfies the category without depending on any blocked host. This also directly answers the calibration note: every prior 4-or-below build in this catalog required manual data entry or was a hollow shell; Connectome instead does substantive computation (TF-IDF-style extraction, corpus-wide link scoring) over files the user already owns.

## Connection to User Context

PROFILE.md names "context loss between AI coding sessions," "managing many simultaneous projects," and "keeping multiple data systems synchronized" as recurring friction points, and lists "Writing and knowledge management" among the domains where a personal tool would add the most value. The user explicitly says they "tend to run many projects simultaneously and benefit enormously from tools that preserve context across sessions" and describes accumulating "research papers, AI workflows, productivity systems, investment theses" as things they curate and obsess over — exactly the kind of scattered note corpus Connectome is built to reconnect.

## Why Tonight

Category C came up in tonight's fixed 9-day rotation. It also follows three prior Category C builds (Investment Thesis Journal, Paper Lens, PubMed Research Radar) that were all variations on "fetch an external feed, score it with AI, render an inbox." Connectome is deliberately a different shape — indexing the user's *own* notes rather than an external feed — so it adds real structural variety to the category rather than a fourth near-duplicate, which matters more given two of those three externally-fed ideas are now unreachable in this session anyway.

## What I Hope the User Gets From This

1. A way to rediscover connections between notes written months apart across different projects (e.g., an AI-workflow note and a lab-administration note that share an underlying idea) without manually re-reading everything.
2. A concrete, working example of the "second brain" pattern the user's own interests reference (productivity systems, knowledge organization) that they can point at a real notes folder tonight.
3. A foundation that costs nothing to keep running — no API key required for the core feature — with a clear, documented upgrade path (`ANTHROPIC_API_KEY`) for richer concept extraction later.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| CanFile — Canadian Ownership Knowledge Cards (Wikidata-backed company dossiers for The Canada List) | C | Strong concept and a real project tie-in, but `query.wikidata.org` / `www.wikidata.org` both returned 403 in this session's connectivity check — could not be built or tested at all tonight. Kept in `builds/ideas.md` for a future session where Wikidata access may be available. |
| Course Concept Atlas (Wikipedia-grounded glossary for teaching material) | C | Same blocker — `en.wikipedia.org` returned 403. Also would have leaned on the same "generate teaching content" pattern the June 24 AI Lecture Builder was criticized for being over-engineered relative to a single Claude prompt; deferred rather than forced through with a weaker data source. |
| A fourth GitHub-activity tool (e.g., a personal "lessons learned" index mined from commit/PR history) | C | `api.github.com` was reachable, but the catalog already has nine-plus GitHub-based builds, and the closest framing ("searchable decision history") duplicates the `why`/decision-search feature the July 10 Worklog build just shipped. Chose not to add a fourth overlapping GitHub tool when a genuinely distinct, network-independent idea was available. |
