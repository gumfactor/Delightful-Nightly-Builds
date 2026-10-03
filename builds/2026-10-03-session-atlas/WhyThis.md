# Why This

**Selection path:** fresh generation. Category F (day 276, index 5). Lottery pool: 2 pending F ideas (#1, #10), R=1, chance 27%. Roll 74 → fresh ideas.

**Candidates**
1. Canada List CSV Inspector — narrowly useful, close to the Jun 17 Qualtrics inspector in shape, and the data lives in the user's pipeline, not here.
2. SEC EDGAR Financial History Extractor — finance is saturated in the catalog (most of the last 10 early builds).
3. **Session Atlas (chosen)** — explorer for Claude Code logs.

**Why Session Atlas.** The PROFILE names "context loss between AI coding sessions" and "managing many simultaneous projects" as the top friction points. The Jun 6 ctxlog build was rated 3 because it needed manual entry; its own note says auto-capture of the session transcript would score higher. This build does exactly that: the data already exists on disk, no entry is needed. The explorer answers questions pandas can't answer without a parser (what did I ask last in each project, where did the tokens go), and the resume prompt gives a concrete daily use. It has a visual interface, uses real local data, and doesn't duplicate existing tools (Claude Code's `/resume` lists sessions but offers no cross-project stats, search or cost view).

**Honest limits.** Log format is undocumented and may change; the parser is tolerant and skips what it doesn't understand. Costs are estimates from an editable price table.
