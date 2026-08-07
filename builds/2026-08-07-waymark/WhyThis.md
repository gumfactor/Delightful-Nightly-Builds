# Why This? — Waymark

> **Date:** 2026-08-07

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 219 → `category_index = (219 - 1) % 9 = 2` → Category C, Personal Knowledge Tool. `builds/ideas.md` was filtered for `pending` rows with Category `C`: zero matches (all 12 backlog rows are categories A, B, F, G, H). An empty filtered pool skips the lottery entirely per Step 2c/2d — no roll was needed since there was nothing to draw from.

## The Decision

With no backlog candidates, I generated three fresh Category C ideas and scanned the last 10 builds plus the full Category C history in `builds/index.md` for topic overlap before picking one. Category C already has five prior builds: two paper-discovery feeds (PubMed Research Radar, Paper Lens), a citation/reading ledger (Citation Vault), a Canadian-ownership lookup tool (CanFile), and a personal-notes knowledge graph (Connectome). I explicitly avoided re-treading any of those. Waymark instead targets a gap flagged by name in the catalog's own feedback: the 2026-06-06 build (AI Session Context Bridge, rated 3/10) was marked down specifically because it "requires manual entry to be useful... would score higher with auto-capture of git state and Claude Code session transcript." Nobody had acted on that note since. Waymark is that fix, built as a proper knowledge base rather than a handoff-doc generator.

## Connection to User Context

PROFILE.md lists "Context loss between AI coding sessions," "Managing many simultaneous projects," and "Re-establishing context across AI sessions" as recurring friction points, and the user explicitly values "tools that preserve context across sessions" given how many projects run in parallel (lab, Canada List, Kwyeter, investing research, this nightly build system itself). Waymark reads directly from something that already exists and is never wrong — git history — rather than asking for anything to be written down.

## Why Tonight

Category C came up in tonight's 9-day rotation. This is also the first build to directly respond to a specific, named piece of prior rating feedback rather than just avoiding a topic that scored poorly — the 2026-06-06 note reads like an open request, and tonight's build closes it out.

## What I Hope the User Gets From This

1. A way to search "what did we decide and why" across every repo they work in, months after the fact, without having ever taken a note
2. A concrete example of turning a specific low rating into a targeted redesign, not just a topic swap
3. A foundation — the scorer, the cross-repo SQLite index, and the render pipeline are all reusable if a future build wants to add manual annotation, GitHub PR correlation, or semantic search on top

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Concept Atlas — cross-reference the user's own markdown notes against Wikipedia to auto-build a personal glossary | C | Too close to Connectome (2026-07-11), which already indexes the user's own note corpus into a local knowledge graph; would read as a minor variant rather than a new capability |
| Grant Boilerplate Miner — index past grant/manuscript text into a searchable library of reusable aims/significance/methods paragraphs | C | Real friction point ("Grant writing"), but requires the user to manually supply source documents with no live or automatically-captured data source, repeating the exact "requires manual entry" failure mode that sank AI Session Context Bridge |
| Course Concept Map — cross-reference lecture notes/syllabi across the user's three taught courses to flag topic overlap | C | Same manual-entry dependency as the Grant Boilerplate Miner; also more naturally a Learning Aid (Category E) than a knowledge base, so it would be a category mismatch even if built |
