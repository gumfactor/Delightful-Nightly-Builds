# Why This? — Citation Vault

> **Date:** 2026-07-29

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category rotation (day of year 210, `(210-1) % 9 = 2`) is **C — Personal Knowledge Tool**. The backlog (`builds/ideas.md`) had zero `pending` rows tagged Category C, so per Step 2c the lottery was skipped entirely and Step 2d (fresh idea generation) ran directly — no roll was needed.

## The Decision

Category C already has five prior builds: Investment Thesis Journal (ticker notes), PubMed Research Radar (topic-scoped PubMed scanning), Paper Lens (topic-scoped arXiv scanning), Connectome (personal markdown-notes indexer/graph), and CanFile (Canadian company ownership cards). The two existing literature tools are both *discovery feeds* — they pull new papers matching a small set of saved topics and score them for relevance. Neither manages the researcher's actual reading workflow: papers encountered from any source, their status (to-read/reading/read), personal notes on them, and — critically — exporting a clean bibliography when a manuscript or grant needs one. That gap is what Citation Vault fills. It is architecturally distinct from Connectome (which indexes files the user already wrote, not external citations) and from the two topic-feed tools (which discover, not track).

## Connection to User Context

PROFILE.md names "Literature reviews" as a manual task the user suspects could be automated, and lists "write grants and manuscripts" as a core weekly activity — both require assembling and citing a working set of papers, which today means re-finding and re-formatting references by hand every time. PROFILE.md also separately lists a personal quantitative-investing research thread and consumer-advocacy work (The Canada List), neither of which needs a citation manager, so this build is scoped specifically at the academic/research side of the user's dual role.

## Why Tonight

Category C's rotation slot and an empty backlog for that category made tonight the first open opportunity to build a citation/reading tracker since PubMed Research Radar (2026-07-02) and Paper Lens (2026-06-23) shipped — both of which this build is designed to complement, not replace: a user can drop a DOI surfaced by either of those feeds straight into Citation Vault to start tracking it through to a cited manuscript.

## What I Hope the User Gets From This

1. A single place to track every paper touched across projects — not just the ones caught by a saved-topic feed — from "to-read" through to "cited in manuscript."
2. A one-command BibTeX export scoped by tag or status, removing the manual reference-list assembly step from writing.
3. A lightweight "resurface" nudge that surfaces previously-read papers sharing tags with the current to-read queue, encouraging cross-project reuse of prior reading instead of re-discovering the same literature.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Teaching Material Archive — index lecture/discussion/quiz materials across courses, tagged by concept, growing each term | C | Architecturally near-identical to the already-built Connectome (generic folder-of-notes indexer with concept extraction and a note graph) — a user could already point Connectome at a folder of teaching notes. Not enough differentiation to justify a dedicated build tonight; appended to the backlog for a night when a genuinely distinct teaching-specific mechanic (e.g. syllabus/term structure) is worked out. |
| Grant Boilerplate & Progress Report Library — reusable grant-writing sections (specific aims, significance, broader impacts) indexed by mechanism/topic with approved-boilerplate reuse | C | Nearly identical architecture to the already-built Protocol Forge (compliance rule engine + approved-boilerplate reuse + 3-tier AI/template fallback), just swapping IRB protocol sections for grant sections. Same redundancy risk that cost the 2026-06-21/2026-07-27 GitHub scorecard duplicate points on rating. Appended to the backlog for revisiting with a more differentiated angle. |
| Citation/Reference Batch Formatter (backlog idea #20, already logged 2026-07-28) — CLI that reformats a folder of existing citation strings/DOIs to a consistent style and emits BibTeX | B/F | This is a real feature, folded directly into Citation Vault's `export bibtex` command rather than built as a standalone formatter — a bare formatter with no reading-status or notes layer would be, per the existing note on that backlog row, "mechanically thinner" than a full reading tracker. |
