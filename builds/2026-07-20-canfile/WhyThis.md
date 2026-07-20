# Why This — CanFile

## Orientation

`builds/index.md` on `main` was stale (last entry 2026-06-24). The most recently created open PR branch was `claude/cool-sagan-n7vpur` (2026-07-19, "Protocol Forge"). Per CLAUDE.md Step 1, I fetched that branch and read `builds/index.md`/`builds/ideas.md` from it instead of the stale `main` copy — the real catalog has 39 builds through 2026-07-19, not 19 through 2026-06-24. I copied both files into my working tree before making tonight's decision so the lottery pool, ratings, and topic-diversity check all reflect current reality.

## Category

Day of year for 2026-07-20 is 201. `(201 - 1) % 9 = 2` → **Category C — Personal Knowledge Tool**.

## Lottery

Pending Category C ideas in the backlog: #13 (CanFile — Canadian Ownership Knowledge Cards, rating blank) and #14 (Course Concept Atlas, rating blank). Both blank → `R = 0` numeric ratings in the pool. `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled a random integer 1–100: **100**. `100 > 25` → fresh-idea path (Step 2d), per the roll.

## Topic diversity check (last 10 builds, 2026-07-10 → 2026-07-19)

- 07-10 Worklog (B) — cross-agent activity correlation
- 07-11 Connectome (C) — generic personal notes knowledge base
- 07-12 Research Question Forge (D) — neuroscience research-question generator
- 07-13 CircuitLab (E) — neuroanatomy trainer
- 07-14 GrantScope (F) — NIH funding landscape
- 07-15 Confound Hunter (G) — research-methods literacy game
- 07-16 AgentLint (H) — CLAUDE.md/AGENTS.md auditor
- 07-17 Deadline Guardian (I) — academic/admin deadline tracker
- 07-18 CanEcon Pulse (A) — Canadian macroeconomic indicators
- 07-19 Protocol Forge (B) — IRB/ethics protocol drafting

Five of the last ten builds (Research Question Forge, CircuitLab, GrantScope, Confound Hunter, Protocol Forge) are squarely in the neuroscience-research/academic-admin domain. That domain is saturated for tonight even though it isn't literally "investment/finance" (the domain STANDARDS.md calls out by name) — the spirit of the rule is topic diversity, and stacking a sixth research-domain build in ten nights would not surprise the user. The Canada List, one of PROFILE.md's two named non-academic active projects, has **never** had a build target it directly (the only related backlog item, #1 "CSV Quality Inspector," is unbuilt and depends on data this environment doesn't have).

## Fresh ideas considered

1. **CanFile — Canadian Ownership Knowledge Cards** (chosen — matches backlog #13). Per-company Wikidata + Wikipedia facts → deterministic ownership-verdict rule engine (optional Claude enrichment) → versioned local knowledge card → searchable HTML index. Directly serves The Canada List's actual research workflow (identifying whether a business is Canadian-owned) with real public APIs, and was previously only blocked by the build container's egress proxy returning 403 on `wikidata.org`/`wikipedia.org` — CLAUDE.md is explicit that this is a build-environment constraint, not a reason to redesign or avoid the idea. Tonight's code is written against the real Wikidata/Wikipedia REST APIs and mocks them in every test, so it will work correctly in the user's local runtime regardless of what the build container's proxy allows.
2. **Investment Ownership & Filing Knowledge Cards** (considered, rejected) — SEC EDGAR-backed shareholder/insider knowledge cards for watchlist tickers. Rejected for tonight: the investment domain already has two prior builds in this category's own history (Investment Research Platform 06-10, Investment Thesis Journal 06-14), and CanFile's Canada List tie is both fresher and more directly named in PROFILE.md's active-projects list.
3. **Personal Reading Digest KB** (considered, rejected) — a Claude-synthesized cross-paper thematic digest sitting on top of the existing Paper Lens/PubMed Research Radar feeds. Rejected: would be the fourth build in the "external research feed → local index" shape (Paper Lens, PubMed Research Radar, Connectome all already occupy this space), with no clearly differentiated angle.

Since the winning fresh idea is the same idea as backlog #13, I did not add a duplicate row. Instead `builds/ideas.md` marks #13 `built` with a note, and appends ideas 2 and 3 above as new pending rows (IDs 32–33) for future nights.

## Idea Brief

No linked Idea Brief exists for backlog #13 (the `Idea Brief` column is `—`); the row's own description and rating note (previously blocked by network access) served as the full spec, folded into this PRD.
