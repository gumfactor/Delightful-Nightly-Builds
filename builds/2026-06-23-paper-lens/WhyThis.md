# WhyThis — Paper Lens

## Category & Date

Category C — Personal Knowledge Tool. 2026-06-23 (day 174, category_index = (174-1) % 9 = 2).

## Lottery Result

No Category C ideas in `builds/ideas.md` backlog → lottery skipped, fresh ideas generated (Step 2d).

## Topic Diversity Check

Last 10 builds by topic domain:
- Developer/GitHub tools: 4× (Morning Briefing, GitHub Repository Health Scorecard, dep-check, worklog)
- Investment/finance: 3× (Investment Thesis Journal, Investment Watchlist Dashboard, Investment Research Platform) → **saturated — no finance builds**
- Academic/research tools: 1× (Qualtrics Survey Data Inspector)
- Fitness: 1× (Run Planner)
- Games/learning: 2× (Regex Dojo, Spaced Repetition Flashcards)

## Fresh Ideas Generated

Three candidates in Category C:

1. **Paper Lens** *(selected)* — arXiv research paper inbox: fetches papers across the user's research areas daily, uses Anthropic API to score relevance and generate plain-English summaries, stores in SQLite, renders a searchable dark-mode HTML viewer. Solves "literature reviews" — explicitly listed in PROFILE.md as a manual task to automate. Uses real data (arXiv API, free/no-auth) and AI in the differentiating layer.

2. **Lab Project Context Vault** — SQLite-backed knowledge store for keeping structured context on all active research projects; Anthropic API generates current-state briefs from recent log entries. Added to `builds/ideas.md` (ID 13).

3. **Grant Evidence Collector** — per-grant citation organizer: add DOIs, auto-populate from CrossRef API, tag to specific aims, Anthropic API synthesizes what papers in each section collectively show. Added to `builds/ideas.md` (ID 14).

## Why Paper Lens Won

- **Real data, not manual entry.** The previous Category C build (Investment Thesis Journal, 4/10) required manual entry. Paper Lens auto-populates from the arXiv API — no entry required beyond setting up topics once.
- **AI is the differentiating layer.** Without relevance scoring, a list of papers is noise. With it, the 2 papers that matter each day surface to the top automatically. This is exactly the "AI processing as differentiating layer" signal from CLAUDE.md.
- **Solves a real daily friction.** "Literature reviews" is item #1 on the PROFILE.md "things you do manually that could be automated" list. The researcher checks arXiv manually; this replaces that.
- **Visual interface.** The 4/10 rating on the previous C build explicitly noted "bare CLI with no view layer; half-realized." Paper Lens ships a full HTML viewer.
- **Novel.** No prior build in this catalog touches paper/literature workflows. Finance was covered 3×; developer tools 4×; this opens a new domain.
- **Scope is right.** One session can fully deliver: fetch + AI analysis + persistent store + HTML viewer + CLI + 25 tests.

## Deviations from Default

None. No idea brief linked (backlog draw was skipped). Build proceeds directly from this rationale.
