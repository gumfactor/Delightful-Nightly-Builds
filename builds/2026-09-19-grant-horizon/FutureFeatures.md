# Future Features — Grant Horizon

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Per-topic "new since last sync" badge** — store a snapshot timestamp per sync run (like Dominion Index and Rotation Radar's `localStorage`/SQLite "since last run" delta pattern) and surface newly-appeared projects at the top of each topic panel, so a re-sync before a new submission cycle immediately surfaces what's changed.
2. **`--min-award` / `--max-award` CLI filters** on `report`, so a very broad topic (e.g. "stress") can be narrowed to R01-scale awards without re-syncing.
3. **A "copy landscape paragraph" button** on each topic panel that copies the AI briefing (or deterministic summary) text to the clipboard, ready to paste into a grant's own literature-gap section.

## Medium Effort (roughly one nightly build session)

4. **Co-funding / overlap detection** — flag PIs or institutions that appear across *multiple* of the lab's tracked topics, surfacing potential collaborators or competitors working at the intersection of, say, "psychopathy" and "affective neuroscience" specifically.
5. **A Claude Code Routine wrapper** (per PROFILE.md's stated preference for pull tools over push tools) that re-runs `sync` + `report` automatically on a monthly cadence and only notifies the user when a tracked topic's funding total or top-institution ranking has materially changed since the last run — turning this from a manual pre-submission check into a standing radar.

## Ambitious Extensions (multi-session effort)

6. **Cross-reference with Throughline (2026-09-12)** — Throughline already tracks this lab's own publication record via Semantic Scholar. A combined view could show "your publication output vs. the broader funded landscape" per topic, directly answering "is our output proportionate to how competitive this space is."
7. **A real per-PI budget model** — replace the current "full award credited to every co-PI" simplification with NIH's separately-published (but not RePORTER-search-indexed) subproject/budget-component data where available, for a more defensible PI-level funding comparison.
8. **Canadian funder integration once available** — if CIHR, NSERC, or SSHRC ever publish a comparable free, documented, machine-readable award-search API, add it as a second data source alongside NIH RePORTER for a genuinely binational funding-landscape view.

---

## Possible Integration Points

- **Throughline (2026-09-12)** — same "own research output, tracked over time" shape; a natural sibling dashboard. See Ambitious Extension #6.
- **Eligible Spend (2026-09-18)** — covers *after*-award budget compliance for Tri-Agency grants; Grant Horizon covers the *before*-award competitive landscape for NIH grants. Together they bracket the grant lifecycle, though for different funders — worth noting in any future "grant lifecycle suite" framing.
- **Preprint Pulse (2026-09-13)** — same fact-grounded-AI-briefing pattern (never inventing a statistic, deterministic fallback with zero network calls) applied to a different live data source; a useful reference pair for any future research-admin build.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No non-US funder coverage | Add a second data source once a suitable free Canadian funder API exists (see Ambitious Extension #8) |
| Multi-PI award-amount double-counting in the "Top PIs" ranking | Documented as a simplification in `src/aggregate.py`; a real fix needs per-PI budget data NIH doesn't expose via this API |
| No historical trend across sync runs beyond RePORTER's own fiscal-year data | Add the "new since last sync" snapshot tracking described in Quick Win #1 |
| Manual re-sync only | Wrap as a Routine (Medium Effort #5) so the landscape check happens automatically ahead of submission deadlines |
