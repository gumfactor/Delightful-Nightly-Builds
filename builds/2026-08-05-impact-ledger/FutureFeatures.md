# Future Features — Impact Ledger

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Export citation trend as CSV** — Add an `export --author-id ID --out trend.csv` command that dumps the `citation_trend()` and `latest_snapshot()` tables to CSV, useful for pasting straight into a grant progress report or annual review document.
2. **`--top N` flag on `render`** — Let the paper table default to showing only the top N most-cited papers, with a "show all" toggle client-side, so a CV-length author with 200+ works gets a usable first screen instead of one giant table.
3. **Colorblind-safe rising indicator** — The rising-paper delta text currently relies on a green accent color alone; add a `▲` glyph prefix so the signal doesn't depend on color perception.

## Medium Effort (roughly one nightly build session)

4. **Routine wrapper for scheduled syncs** — Package `sync` as a Claude Code Routine that runs weekly or monthly and appends to `history`, turning this from a push tool (must remember to run it) into a pull tool that silently builds up real trend history in the background, and only notifies the user when a paper's citation velocity crosses a threshold worth mentioning.
5. **Multi-author / co-author comparison view** — Track two or more OpenAlex author IDs (e.g., the user plus a frequent collaborator or lab member) side-by-side in one dashboard, useful for annual lab reports covering the whole team's output.
6. **Grant-ready impact paragraph generator** — A `brief --author-id ID` command that feeds the current stats (h-index, total citations, top 3 rising papers) to Claude Haiku to draft a one-paragraph "research impact" statement formatted for a grant progress report, with a deterministic template fallback matching the pattern used elsewhere in this build.

## Ambitious Extensions (multi-session effort)

7. **Co-citation / co-author network graph** — A hand-drawn Canvas 2D or SVG graph (following the pattern established by Connectome, 2026-07-11) showing which of the author's papers are frequently co-cited together, and which collaborators appear across the most works — surfacing research clusters the author may not consciously track.
8. **Cross-reference with GrantScope** — Since GrantScope (2026-07-14) already tracks NIH RePORTER funding landscapes for related topics, a future build could link a rising paper's concepts to active funding opportunities in the same space, turning "this paper is gaining traction" into "and here's a relevant grant call to cite it in."

---

## Possible Integration Points

- **GrantScope (2026-07-14)** — shares the "funding/impact for grant writing" theme; a shared SQLite schema or cross-linking by research concept/topic would let a future build connect citation momentum to funding opportunities.
- **Citation Vault (2026-07-29)** — Citation Vault tracks *reading* other people's papers; Impact Ledger tracks citations *of the user's own* papers. A future build could let Citation Vault's BibTeX export include impact stats pulled from this build's SQLite database when a tracked paper happens to be one of the user's own.
- A future **Routine** packaging (see #4 above) would let this build's `sync` step run automatically, removing the last manual step in an otherwise fully automated pipeline.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Author disambiguation depends entirely on `search-author`'s candidate list; a very common name with a sparse OpenAlex institution record may still be ambiguous | Add a `--orcid` flag to `search-author`/`sync` so an ORCID iD (a stable, user-supplied, unambiguous identifier) can resolve directly to an OpenAlex author record via OpenAlex's ORCID filter |
| Citation trend and rising-paper detection require at least two real `sync` runs on different UTC days before they show anything meaningful | Document this clearly in Manual.md (done) and consider the Routine wrapper (#4) so meaningful history accumulates without the user needing to remember to re-run it |
| The AI note for a rising paper is generated fresh on every `render --ai` call rather than cached, so re-rendering the same day re-spends API calls for unchanged data | Cache AI notes in the SQLite `work_snapshots` row itself, keyed by `(work_id, sync_date)`, and only regenerate when the underlying snapshot changes |
| OpenAlex occasionally lists multiple author IDs for the same real person (un-merged duplicate profiles) | Support syncing multiple author IDs into one logical "identity" and merging their works/citations, rather than assuming one OpenAlex ID = one person |
