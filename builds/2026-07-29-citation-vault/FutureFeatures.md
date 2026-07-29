# Future Features — Citation Vault

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **APA/MLA plain-text export** — add `export apa` / `export mla` alongside `export bibtex`, reusing the same filtering (`--tag`/`--status`) and citation-key infrastructure, just swapping the formatting function.
2. **`untag` command** — a dedicated `python3 main.py untag <id> <tag>` to remove a single tag without having to reissue the whole tag set via `tag`.
3. **CSV export** — a flat `export csv` for pasting a reading list into a spreadsheet or sharing with a co-author who doesn't use BibTeX.
4. **`--year-from`/`--year-to` filters on `list`** — useful once the library grows past a few dozen papers spanning many years.

## Medium Effort (roughly one nightly build session)

5. **Zotero/Mendeley/EndNote import** — a one-time `import zotero-csv <file>` (or BibTeX import) that seeds Citation Vault from an existing reference manager library, so the tool is useful on day one for someone with years of existing citations rather than starting empty.
6. **Multiple named libraries with a `switch` command** — right now `--db` supports separate libraries per project, but there's no registry of them; a `library add/list/switch` layer would make managing several concurrent projects (lab research vs. the Stress and Coping book vs. a specific grant) less error-prone than remembering file paths.
7. **Citation-graph enrichment via Crossref's `is-referenced-by-count` and reference list** — surface "papers that cite this" and "papers this cites" directly from Crossref's existing response data (no extra API needed, since it's already in the `/works/{doi}` payload but currently discarded), turning Citation Vault into a lightweight literature-mapping tool.

## Ambitious Extensions (multi-session effort)

8. **Cross-build integration with Paper Lens / PubMed Research Radar** — a shared "send to Citation Vault" export from either discovery-feed build's SQLite database, so a paper surfaced by a topic feed can be promoted into the reading-workflow tracker with one command instead of manual DOI re-entry. Would require the exporting build to write a small, documented JSON handoff file (each build's own folder remains self-contained; no cross-folder imports needed, just a shared, versioned interchange format).
9. **A Claude-Code Routine that runs `resurface --ai` weekly and appends the result to a markdown digest** — turning the pull-based `resurface` command into a standing "here's what to revisit this week" push notification, consistent with PROFILE.md's stated preference for tools that come to the user rather than ones they must remember to run.

---

## Possible Integration Points

- **Paper Lens (2026-06-23)** and **PubMed Research Radar (2026-07-02)** are natural upstream sources — both already do topic-scoped discovery and relevance scoring; Citation Vault is the natural downstream "I've decided to actually read this" tracker for papers they surface. See Ambitious Extension #8 above.
- **Protocol Forge (2026-07-19)** and **Bridgework (2026-07-21)** both write manuscript/course-facing prose that often cites literature; a future version of either could call Citation Vault's `export bibtex` programmatically once both tools share the same local-SQLite-plus-CLI-module pattern.
- **Worklog (2026-07-10)** already correlates cross-tool project activity; a Citation Vault `sync` event (paper added/status changed) would fit naturally as another event type in Worklog's ledger if the two are ever wired together.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No reference-manager import path, so an existing library (Zotero, etc.) can't be migrated in | Add a one-time BibTeX/CSV import command (Medium Effort #5 above) |
| `export bibtex` always uses `@article` regardless of actual work type | Read Crossref's `type` field (already available in the API response, currently discarded) and map to `@article`/`@incollection`/`@inproceedings` accordingly |
| The HTML dashboard is a static snapshot requiring a manual `render` re-run | Either add a `--watch` mode that regenerates on database change, or accept the snapshot model as intentional for a zero-dependency, zero-server tool and document it clearly (already done in Manual.md) |
| `resurface`'s tag-overlap matching is purely deterministic set intersection, so near-synonym tags (e.g. "cortisol" vs. "cortisol-reactivity") never match | Normalize tags at write time (lowercase, singularize) or add a small synonym-alias table the user can extend |
