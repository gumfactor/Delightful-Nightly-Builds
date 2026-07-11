# Future Features — Connectome: Personal Knowledge Graph Builder

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Watch mode** — a `connectome watch --notes-dir DIR` command that polls the folder every few seconds and re-runs `index` automatically on change, so the knowledge base stays current without manually re-running the CLI.
2. **`--top` flag on `related`/`search`** — let the user control how many results come back from the CLI, rather than the hardcoded top-5 default in `related_to`.
3. **Export a note's related-notes list as Markdown** — a `connectome export <note>` command that writes a "See also" block (with shared-concept explanations) that can be pasted directly into the source note file.
4. **Phrase-level extraction** — currently concepts are single tokens; capturing simple two-word noun phrases ("stress response", "concept graph") alongside single terms would make the tag cloud and shared-concept explanations noticeably more readable.

## Medium Effort (roughly one nightly build session)

5. **PDF and DOCX ingestion** — extend `read_notes_dir` to extract text from `.pdf`/`.docx` files (via a lightweight parser), since a lot of real "notes" the user accumulates are papers and Word documents, not just Markdown.
6. ~~**Backlink-aware Markdown export**~~ — **Done (2026-07-11 follow-up).** `connectome backlinks` now writes `[[wiki-style links]]` directly into the original note files, guarded by: dry-run-by-default (`--write` required to touch anything), a `git_baseline_problem()` check that refuses to write unless `--notes-dir` is a git repo with at least one commit **and** a clean working tree (so the edit always lands as a clean, `git diff`-able, `git checkout`-revertible change — a bare `git init` with nothing committed does not satisfy this), a per-note content-hash check that skips any note edited on disk since the last `index` run instead of silently overwriting it, and a single delimited block (`<!-- connectome:links:start/end -->`) per file so re-runs replace in place rather than duplicating. `--skip-git-check` remains as an explicit, documented escape hatch. See `Manual.md` for usage and `BUILD_LOG.md` for the 2026-07-11 follow-up session log.
7. **Concept merging / aliasing** — a small `aliases.json` the user maintains (e.g. "ML" = "machine learning") so near-duplicate concepts don't fragment link scores across synonyms.
11. **Frontmatter-aware backlink insertion** — `backlinks.apply_block` currently always appends the See Also block at the very end of the file; a note with YAML frontmatter or a trailing "Related" section written by the user would benefit from a configurable insertion point instead of always-last.
12. **Rename detection for backlinked notes** — since `index` treats a renamed file as delete+add (see Known Limitations below), a note that gets renamed after `backlinks --write` has run will leave stale `[[old-filename]]` links in every note that pointed to it until the next `backlinks --write`. A `connectome backlinks --write` pass already fixes this on next run, but there's no proactive warning today.

## Ambitious Extensions (multi-session effort)

8. **Cross-tool ingestion** — pull directly from Coda docs or Google Docs (both already in the user's stack per PROFILE.md) as additional note sources alongside local files, so the knowledge graph spans tools instead of requiring everything to live in one folder first.
9. **Temporal knowledge graph** — track how a note's concepts and links change over time (each `index` run already timestamps changes) and render a "how has my thinking on X evolved" view — directly useful for revisiting an investment thesis or a research design decision months later.
10. **Semantic (embedding-based) linking as an opt-in mode** — layer in a local sentence-embedding model (no network call required, e.g. a small ONNX model) as an alternative to keyword-overlap scoring, catching conceptually related notes that don't share literal vocabulary at all.

---

## Possible Integration Points

- **Worklog (2026-07-10)** already builds a decision/event ledger from git and GitHub activity for a project. Connectome's note-linking approach could plug in as an additional evidence source — indexing a project's design notes and cross-referencing them against Worklog's commit-derived workstreams.
- The two backlog ideas deferred tonight for network reasons (CanFile — Canadian Ownership Knowledge Cards, and Course Concept Atlas, both in `builds/ideas.md`) would both benefit from Connectome's linking engine once their data source is reachable — the extraction/linking modules here are generic enough to index any corpus of short documents, not just personal notes.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Concept extraction is single-token only, so multi-word ideas ("stress response", "market cap") get split into separate, less meaningful tokens | Add simple bigram/trigram candidate extraction alongside unigrams (Future Feature #4) |
| Extraction quality depends on having enough repeated vocabulary within a note; very short or highly idiosyncratic notes may extract few useful concepts, and top_n tuning (raised from 8 to 15 during tonight's build) is still a rough heuristic rather than a principled threshold | Add a minimum-weight cutoff instead of a fixed top_n, and/or the phrase-extraction improvement above |
| `--ai` enrichment could not be exercised against the real Claude API this session (`ANTHROPIC_API_KEY` unset in this sandbox) — only the mocked success/failure paths are verified | Re-verify the live path the next time this build runs in an environment where the key is set; the fallback behavior is already tested and safe either way |
| No de-duplication across near-identical concepts (e.g. "context" vs "contexts" if pluralization varies) | Add simple stemming (e.g. strip trailing "s") before document-frequency counting |
