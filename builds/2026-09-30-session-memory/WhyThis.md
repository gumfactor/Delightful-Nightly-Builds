# Why This

**Selection path:** fresh generation. Date 2026-09-30, day of year 273, (273-1) % 9 = 2, so category C (Personal Knowledge Tool). The backlog held no pending category C rows, so no lottery roll happened (pool size 0).

**Candidates considered**
1. Session Memory (chosen): automatic index and resume briefs over AI transcripts already on disk.
2. Reading-list triage from a Zotero/BibTeX export with AI relevance notes: overlaps Paper Lens (06-23).
3. Wikipedia/Wikidata concept-map builder for course topics: interesting, but no real personal data behind it.

**Why this one:** PROFILE.md names "context loss between AI coding sessions" and "re-establishing context across AI sessions" as recurring friction, and the user runs many parallel projects. The 06-06 ctxlog build scored 3 because it needed manual entry; this one reads the transcripts Claude Code already writes to `~/.claude/projects`, plus Claude.ai and ChatGPT exports, so there is nothing to type. It has a visual interface (per the calibration note), uses real local data (no mocks or localStorage), and works fully offline, with Claude as an optional upgrade layer rather than a requirement.

**Topic diversity:** recent builds lean toward investing and GitHub/dev tooling; this is neither. It overlaps ctxlog (context handoff) in purpose but replaces manual capture with automatic ingestion.

**Honest limits:** heuristic summaries are keyword-based and will miss decisions phrased unusually; AI summaries fix that but need a key and send transcript text to Anthropic, so they are opt-in per click/flag.
