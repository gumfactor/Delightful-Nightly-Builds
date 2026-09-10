# Why This — Dominion Index

## Category and rotation

Day of year 253 → `category_index = (253-1) % 9 = 0` → **Category A — Dashboard / Visualizer**.

The prior Category A build was Fleet Drift (2026-09-01), 9 days ago — exactly on rotation.

## Lottery

Filtered `builds/ideas.md` (pulled from the most recent open PR branch, `claude/cool-sagan-hpwm1q` / PR #94, since `main` was 68 builds behind) to `pending` rows with `Category = A`:

| ID | Title | Rating | Tickets |
|----|-------|--------|---------|
| 3 | Lab Research Project Tracker | 4 | 4 |
| 6 | Open-Meteo Activity Planner | — | 5 |
| 26 | Research Pulse | — | 5 |
| 27 | Canada List Business Density Dashboard | — | 5 |
| 37 | Research Software Reproducibility Scorecard | — | 5 |
| 38 | Canada List Market Landscape | — | 5 |

Pool size 6, of which `R = 1` has a numeric rating. `lottery_chance = min(75, 25 + 1*2) = 27%`. Rolled **10/100** → ≤27 → **draw**. Weighted draw over 29 total tickets picked **idea #38, "Canada List Market Landscape"** (`python3 -c "import random; ..."`, unseeded). Marked `built` in `builds/ideas.md`.

## Why this idea holds up

Idea #38 was passed over once before (2026-09-01, in favor of Fleet Drift) for a documented, specific reason: the build container's egress proxy blocked live verification of the exact Wikidata SPARQL query shape, and the passed-over note explicitly flagged the correctness trap this idea's own description names — "avoiding CanFile/Provenance's already-solved 'country=Canada mischaracterizes a foreign subsidiary's local office' correctness trap." That trap is real and worth solving carefully rather than working around: a naive `P17 (country) = Canada` filter on Wikidata would count a foreign multinational's Canadian sales subsidiary as a Canadian-owned company. `PRD.md`'s "Canadian-ownership definition" section fixes this by keying off the headquarters location's country (`P159`/`P17`) combined with a `FILTER NOT EXISTS` exclusion on any recorded foreign parent organization (`P749`/`P127`) — a heuristic, not a legal determination, and documented as such.

This build is also a genuinely untouched angle for a named active project (The Canada List): every prior Canada List build (CanFile, Ingest Gate, Provenance, Maple Press) is a per-business lookup or ingestion-pipeline tool. This is the first aggregate, editorial-context dashboard — "how many Canadian-owned companies exist in industry X, and where are they" — the exact question idea #38's own description names.

A live `curl` to `query.wikidata.org` was denied outright at this session's sandbox layer (confirmed by attempting it during this session), so the SPARQL query and the 13 province/territory Wikidata QIDs are written against Wikidata's stable, documented property model from training knowledge, not live-verified — consistent with `CLAUDE.md`'s guidance that a build-container network block is never a reason to redesign around mock data, and consistent with how the Almanac (2026-09-06) and EDGAR Lens (2026-08-28) builds handled the same constraint for their own APIs. The fetch layer surfaces the endpoint's own error text verbatim on any unexpected response rather than assuming the query ran correctly, so a wrong QID or a timeout fails loudly and specifically rather than silently.

## Topic diversity check

Last 10 builds (Layer Guard→Headroom, Aug 30–Sep 9) span H, A, B, C, D, E, F, G, H, I — every category once, no repeated category and no repeated topic domain. Investment/finance (Trading Book, EDGAR Lens) last appeared Aug 23 and Aug 28, both outside the last-10 window, so no saturation concern applies here. This build's domain (Canada List / Wikidata aggregate data) has zero prior coverage in the full 87-build catalog.
