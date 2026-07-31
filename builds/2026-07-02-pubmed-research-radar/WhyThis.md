# WhyThis.md

## Category & Rotation
Day of year 2026-07-02 = 183. `(183 - 1) % 9 = 2` → Category **C — Personal Knowledge Tool**.

## Lottery
Filtered `builds/ideas.md` backlog to `pending` rows with Category `C`: **zero matches** (the only category-C entry ever recorded, Paper Lens, was already built on 2026-06-23 and isn't in the backlog as a pending row). Lottery skipped per the rules — pool empty means go straight to fresh-idea generation (Step 2d). No roll was made.

## Topic Diversity Check (last 10 builds)
Scanned 2026-06-22 through 2026-07-01 (the last 10 rows in the synced `builds/index.md`): Morning Briefing, Paper Lens, AI Lecture Builder, Stats Coach, GitHub Developer Activity Explorer, Neurofact, ci-pulse, Project Pulse, GitHub Developer Analytics Dashboard, BIDS Dataset Organizer.

Heavily saturated domain: **GitHub developer/repo analytics** (4 of the last 6 builds — Developer Activity Explorer, ci-pulse, Project Pulse, Developer Analytics Dashboard all mine commit/CI/repo metadata via `GITHUB_TOKEN`). None of tonight's candidate ideas touch that domain. Investment/finance has not appeared in the last 10 and isn't relevant to category C tonight anyway. Category C itself has exactly one prior entry (Paper Lens), so there's no saturation risk within the category itself — the constraint that mattered was not re-treading Paper Lens's specific mechanism (arXiv-only paper feed).

## Fresh Ideas Considered

1. **PubMed Research Radar** (winner) — A saved-topic literature triage tool sourced from PubMed E-utilities (free, no auth), with optional Claude Haiku relevance scoring/summarization and a graceful keyword-overlap fallback when no API key is present. Directly answers the Rating Note left on Paper Lens (2026-06-23, scored 6/10): *"Limited by arXiv-only sourcing; a neuroscience researcher needs PubMed and Google Scholar at minimum. Worth extending rather than discarding — the core pipeline is sound."* This is architecturally a new build (no code is imported from the Paper Lens folder — a hard rule), but it is a direct, intentional answer to explicit user feedback, sourced from the literature database that actually matches the user's day job (forensic/affective neuroscience), not a general-purpose preprint server. Also answers the manual pain point listed in PROFILE.md under "Things you do manually that you suspect could be automated": *"Literature reviews."*

2. **Personal Manuscript/Grant Knowledge Base** — Ingest the user's own manuscript/grant drafts and build a searchable, AI-extracted concept index (claims, methods, defined terms) across their own writing. Rejected for tonight: this is fundamentally a manual-entry tool (the user has to supply their own files with no bundled real content to seed it), which is the exact failure pattern the calibration note flags — Rating Notes on the 2026-06-06 AI Session Context Bridge build (scored 3/10) said almost this: *"value depends entirely on what you write into it."* Logged to the backlog for later — it's a legitimate idea, but not the strongest candidate when a live-data alternative (#1) exists in the same category.

3. **Canada List Classification Precedent Log** — A searchable local database of prior "is this business Canadian-owned" classification decisions with AI-assisted rationale extraction, meant to speed up editorial QC for The Canada List. Rejected for tonight: no real classification data exists yet to seed or test against (would need to fabricate plausible-looking company records, which reads as mock data), and the "Data Explorer" / "F" category is a better long-term home for a Canada List data build once real export files exist. Logged to the backlog.

Idea #1 was picked because it is the only one of the three built on a live, free, no-auth public API (PubMed E-utilities) rather than requiring the user to supply content by hand — matching the calibration note's core finding that mock/manual-entry/localStorage-only patterns score lowest, and live-API patterns score highest, within this exact category.

## Idea Brief
No linked Idea Brief — this was a freshly generated idea, not drawn from a backlog row with a brief attached.

## A Note on Tonight's Network Environment
This build session's sandboxed network policy blocks direct outbound HTTPS to essentially every external host except `anthropic.com`/PyPI/npm (confirmed via the agent proxy's `/__agentproxy/status` endpoint, which logged an explicit `connect_rejected` / 403 for `eutils.ncbi.nlm.nih.gov`, and separately for Open-Meteo, Yahoo Finance, Wikipedia, SEC EDGAR, and even direct `api.github.com` REST calls outside the GitHub MCP channel). `ANTHROPIC_API_KEY` is also not present in this specific container's environment, despite being listed in PROFILE.md as normally available. This appears to be a deliberate, restrictive network policy for this unattended/autonomous session rather than a universal constraint — the code is written to call the real PubMed and Anthropic APIs exactly as it would need to in a normal (non-sandboxed) runtime, and every test mocks the HTTP layer so the suite is deterministic regardless of which environment it runs in. See `BUILD_LOG.md` for the full investigation and its implications for manual verification tonight.
