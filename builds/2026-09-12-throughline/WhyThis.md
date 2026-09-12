# Why This — Throughline

## Category & date

2026-09-12, day-of-year 255, `(255-1) % 9 = 2` → Category **C — Personal Knowledge Tool**.

## Lottery

Read `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-hrldlh`, PR #96, 2026-09-11 "GradeLine") rather than the local `main`-based copy, per CLAUDE.md Step 1 — the local checkout was 89 - 5 = 84 builds behind (last local build folder: 2026-06-18; catalog's actual last build: 2026-09-11, total 89 builds).

Filtered `builds/ideas.md` to pending rows with Category `C`: 5 matches (#15 Lab Method/SOP Knowledge Base, #16 AI Workflow & Prompt Cookbook, #28 Highlight Vault, #29 Supervision Notebook, #41 Canadian Open-Data Consumer Knowledge Base). None have a numeric `Your Rating` (`R = 0`), so `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled `91` (1–100) — above the 25% gate, so no draw. Proceeded to fresh idea generation (Step 2d) instead of drawing from the backlog.

## Topic diversity check

Scanned the last 10 builds (2026-09-02 through 2026-09-11: CiteForge, Promptbook, CaseForge, Mediation & Moderation Analysis Lab, Almanac, True Course, Secrets Sentinel, Headroom, Dominion Index, GradeLine) — no domain repeats more than twice; investment/finance does not appear at all in this window, so no saturation flag applies.

Category C specifically already has 10 prior builds, however, all of which needed to be checked for overlap before picking a fresh idea: Investment Thesis Journal (ticker notes), Paper Lens (arXiv relevance feed), PubMed Research Radar (PubMed relevance feed), Connectome (personal notes graph), CanFile (Canadian company ownership verdicts), Citation Vault (personal reading/citation tracker), Waymark (git commit decision log), Curriculum Atlas (course concept mapping), Grant Vault (grant-language reuse mining), Promptbook (Claude Code prompt-history mining).

## Fresh ideas considered

1. **Throughline (chosen)** — pulls the user's own publication record and live citation counts from the free, no-auth Semantic Scholar Graph API, deterministically clusters papers into themes (stdlib TF-IDF + Jaccard overlap, no ML libraries), tracks citation growth across sync runs, and produces a grant/CV-ready "research narrative" per theme (deterministic template, optional Claude Haiku synthesis). Chosen because: (a) it targets a source of data — the researcher's *own* body of work — that no prior Category C build touches (existing builds index other people's papers to read, not the user's own publication record), (b) it directly answers two friction points PROFILE.md names explicitly under "Things you do manually that you suspect could be automated" — "Grant writing" and, implicitly, reconstructing a research narrative for manuscripts — with zero manual data entry (the calibration note in `builds/index.md` is explicit that manual-entry-dependent builds score ≤4/10; this build's only manual step is a one-time author disambiguation, never repeated per-paper entry), and (c) it uses a real, live, free public API rather than mock/static data, consistent with the highest-rated builds in this catalog (Qualtrics Survey Data Inspector, 9/10).
2. **StatCan Research Context Library** (logged as idea #55) — a searchable local knowledge base over Statistics Canada / Health Canada open dataset metadata relevant to a saved list of research topics, with AI-generated "why this matters for your research" notes. Rejected for tonight: it reads closer to a dataset *browser* than a personal knowledge tool about the user's own work or notes, and largely overlaps existing idea #41. Logged to `builds/ideas.md` for a future night (Category C or F).
3. **GitHub Stars Knowledge Library** (logged as idea #56) — indexes the user's starred GitHub repos (via `GITHUB_TOKEN`, real personal signal, zero manual entry) into a searchable, AI-tagged "why I starred this / what it's for" personal tool library. Rejected for tonight in favor of Throughline because it serves a narrower, lower-stakes friction point (browsing old stars) versus Throughline's direct hit on named grant/manuscript writing friction, but it is a genuinely novel, zero-manual-entry angle worth building. Logged to `builds/ideas.md`.

## Idea Brief

No backlog row was drawn, so there is no linked Idea Brief to consult (Step 2e skipped).

## Deviations from a fresh backlog row

None — this is a freshly generated idea, so per CLAUDE.md Step 2d it is not appended to `builds/ideas.md` as a winner; only the two non-winning ideas above are appended as new pending rows.
