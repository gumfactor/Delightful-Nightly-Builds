# Build Log — Connectome: Personal Knowledge Graph Builder

> **Date:** 2026-07-11
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:20 UTC] Session Start

- Checked for interrupted builds (Step 0): most recent dated folder was `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Read `PROFILE.md`, `builds/index.md`, `builds/ideas.md`, `STANDARDS.md`.
- Discovered `main` is 27 builds behind (last row: 2026-06-18) — resynced `builds/index.md` and `builds/ideas.md` from PR #35 (`claude/cool-sagan-9twrha`, the most recently created open PR, 2026-07-10) per Step 2a's instructions, before doing anything else.
- Category rotation: day-of-year 192, `(192-1) % 9 = 2` → **C — Personal Knowledge Tool**. No pending Category C ideas in the backlog → lottery skipped, fresh generation required.

### [08:30 UTC] Connectivity Checks

- Before generating ideas, tested every free-API host PROFILE.md lists (Wikidata, Wikipedia, Yahoo Finance, Open-Meteo, SEC EDGAR, PubMed E-utilities, arXiv) via direct Python `urllib` requests. All returned `403 Forbidden` from this session's egress proxy (`/root/.ccr/README.md` confirms 403 means the destination host is not allowed by the session's org policy — not to retry or route around it).
- `api.github.com` connects successfully and `GITHUB_TOKEN` authenticates (confirmed with a live `GET /user` call, 200 OK).
- `api.anthropic.com` is reachable (confirmed connection via a throwaway request returning HTTP 401/405, i.e. it reached the server), but `ANTHROPIC_API_KEY` is unset in this session's environment.
- This ruled out the two Wikidata/Wikipedia-based candidate ideas outright, and ruled out a GitHub-based idea on redundancy grounds (nine-plus existing catalog builds already mine GitHub). Redesigned tonight's build before writing any code: a local notes indexer with zero required external dependency, Claude enrichment wired as an optional, gracefully-degrading layer. Full reasoning in `WhyThis.md`.

### [08:45 UTC] PRD Written

- Goal: index a folder of the user's own notes into a searchable, cross-linked local knowledge base.
- Scope: deterministic TF-IDF-style concept extraction, optional Claude enrichment, corpus-weighted note linking, SQLite storage with incremental re-indexing, CLI (`index`/`search`/`related`/`stats`/`build`), self-contained dark-mode HTML knowledge base with search/tag-cloud/note-detail/concept-graph.
- Notable decisions: no vector embeddings (deterministic and fully offline by design); `.md`/`.txt` only; read-only indexer (no in-tool editing).

### [09:10 UTC] Build Phase — Core Extraction & Linking

- `src/extraction.py`: tokenizer with stopword removal, minimum-token-length filter, corpus-wide document-frequency computation, per-note term scoring (term frequency × inverse document frequency), top-N concept selection per note. Kept dependency-free (stdlib `re`/`collections` only) since this is the always-on path.
- `src/linking.py`: pairwise link scoring — for every note pair, sums `1/doc_freq` over shared concepts (rarer shared concepts score more than common ones), stores the top shared concepts as the human-readable explanation. Deliberately symmetric (`note_a < note_b` canonical ordering) to avoid duplicate/reversed edges.
- Wrote `tests/test_extraction.py` and `tests/test_linking.py` alongside this code, not after — caught one real bug: initial IDF formula divided by zero when a concept appeared in every note (`doc_freq == total_notes`); fixed with `math.log((total + 1) / (doc_freq + 1)) + 1` (standard smoothed IDF), added a regression test with a concept appearing in all fixture notes.

### [09:35 UTC] Build Phase — Storage & Incremental Indexing

- `src/storage.py`: SQLite schema (`notes`, `concepts`, `note_concepts`, `links`), content-hash-based change detection so re-indexing unchanged files is a no-op (`sha256` of file bytes stored per note, compared before re-extracting).
- `src/main.py`: `index` subcommand walks the notes directory, skips non-`.md`/`.txt` files, computes hashes, only re-extracts changed/new files, removes notes for deleted files, recomputes links only for notes whose concept sets changed (avoids O(n²) recompute on every run once the corpus is large).
- Found a real bug during manual testing: deleting a note file and re-running `index` left its old links pointing at a now-missing `note_id`, which crashed `related`. Fixed by cascading link deletion when a note is removed, added a regression test (`test_storage.py::test_deleted_note_removes_links`).

### [10:00 UTC] Build Phase — AI Enrichment Layer

- `extraction.py::enrich_with_claude()` — optional, called only when `ANTHROPIC_API_KEY` is set. Sends the note body (truncated to 4000 chars) to Claude Haiku via raw `urllib.request` (no SDK, matching the rest of this catalog's pattern), asking for a short JSON array of concepts and a one-sentence gist. On any exception (no key, timeout, malformed response, non-200 status) falls back to the deterministic extraction silently — the caller never sees a crash either way.
- Since `ANTHROPIC_API_KEY` is unset this session, this path could not be exercised live; it is fully covered in tests via a mocked `urllib.request.urlopen` (success path, malformed-JSON path, and simulated `URLError` path all assert the graceful-fallback behavior).

### [10:25 UTC] Build Phase — HTML Rendering

- `src/render.py` generates a single self-contained `output/index.html`: note list with client-side search/filter, a tag cloud built from top corpus concepts, a note-detail panel, and a hand-drawn Canvas 2D circular-layout graph (nodes sized by link count, edges weighted by score, click-to-highlight neighbors) — no CDN dependency at all, avoiding the CDN-blocked issue several recent builds in this catalog hit.
- All note/concept/link data is embedded via a `<script type="application/json" id="connectome-data">` block rather than interpolated into an executable `<script>` block, specifically to avoid the classic `</script>`-breakout injection risk. Verified with a test fixture note whose body is literally `<script>alert(1)</script>` plus stray backticks and quotes — confirmed the generated HTML contains the escaped/JSON-encoded form only and the string `</script>` never appears un-encoded outside its own wrapping tag.
- Note bodies rendered in the detail view go through `html.escape()` before insertion; verified via test that renders the hostile fixture note and asserts no raw `<script>` tag appears in the output HTML.

### [10:45 UTC] Sample Data

- Wrote `sample_notes/` — six short synthetic notes spanning the user's stated interests (AI agent handoffs, a forensic/affective neuroscience study note, Canada List ownership heuristics, a semiconductor investment thesis, a Stress & Coping course outline, quant screening notes) so `index`/`build` produce a populated, explorable knowledge base immediately. All content is fictional/illustrative — no real personal data, no real study data.

### [11:05 UTC] Tests Run

Tests: 48 passed, 0 failed. (`python -m pytest tests/ -v`)

Breakdown: 13 extraction tests (incl. AI-enrichment mocked success/fallback paths), 9 linking tests, 8 storage/indexing tests, 13 CLI tests, 5 render/HTML-safety tests.

Two test bugs found and fixed during this run, not app bugs: `test_extract_concepts_respects_top_n` generated candidate words as `uniqueterm0`..`uniqueterm19`, but the tokenizer (correctly) strips digits, so all 20 collapsed into a single token `uniqueterm` — fixed by generating genuinely distinct letter-only words. Second, the original fixture files' Markdown headings (`# Note A`, `# Note B`, `# Note C`) accidentally shared the literal word "note" across three of four fixtures, producing a spurious link and breaking the "isolated note has no links" test — fixed by giving fixtures distinct, topical headings instead of placeholder ones.

### [11:15 UTC] Manual Verification — Real Data, Then Real Browser

- Ran `python3 src/main.py index --notes-dir sample_notes`: 6 notes indexed. First pass with the default `top_n=8` produced **zero cross-note links** — diagnosed by dumping each note's extracted concept list directly: with many singleton (tf=1) words in short prose notes, the intended thematic overlap words ("workflow", "context", "confidence") were getting crowded out of the top 8 by equally-weighted rare words, and one intended link relied on a hyphenated phrase ("ownership-confidence") that tokenized as a single compound token distinct from "confidence" elsewhere. Fixed by raising the default `top_n` to 15 in `extraction.py` and lightly revising three sample notes to state the shared ideas plainly (removing an accidental hyphen, and adding one clarifying sentence each to `ai-agent-handoffs.md` and `quant-screening-notes.md`) rather than tuning the algorithm to fit throwaway wording. Re-indexed: 3 links now found, all substantively meaningful (e.g. "AI Agent Session Handoffs" ↔ "Quant Screening Workflow Notes" share `workflow, context` — a real cross-domain connection, which is the whole point of the tool).
- Confirmed incremental indexing against the real corpus, not just fixtures: re-ran `index` with no changes → "0 new/changed, skipped 6"; after editing 3 files → "3 new/changed, skipped 3" — hash-based change detection works against real file edits, not only the pytest-mocked path.
- Installed Playwright (`pip install playwright`; Chromium was already pre-provisioned at `/opt/pw-browsers`) and drove the actual generated `output/index.html` in headless Chromium rather than just asserting on the HTML string: confirmed the note list renders (6 items), the search box live-filters (typing "workflow" narrows to 2 items), a tag-cloud click filters the list, clicking a note populates the detail panel and related-notes list, the concept graph canvas is present and its click handler runs without error, and — critically — a note containing `<script>window.__pwned=true</script><img src=x onerror="...">` renders as inert visible text with zero `pageerror`/console errors and `window.__pwned` never becomes true. This is real proof the XSS mitigation works, not just a substring assertion on the HTML source.
- Ran `stats` and `related` against the real indexed corpus; output matches the computed links above.
- Cleaned up session-generated `connectome.db`, `output/`, and `__pycache__` before committing (added a build-folder `.gitignore` for them — they're runtime artifacts, not source).

### [11:25 UTC] Security Checklist

- No `.env` files, no hardcoded credentials/API keys/personal data.
- No `eval()`/`exec()`, no `os.system()`/`subprocess` with user-controlled input.
- Note-derived content only ever reaches the page via `html.escape()` (detail view) or a `<script type="application/json">` block parsed with `JSON.parse` (search/graph data) — never raw `innerHTML` string interpolation.
- All file I/O is scoped to the build folder and the user-supplied `--notes-dir` path (read-only) — no path traversal beyond what the user explicitly points the tool at, and no writes outside `connectome.db`/`output/`.
- Optional Claude call sends only note body text (something the user already owns and chose to index) — no other personal data collected or transmitted.

Build complete. Success criteria reviewed. All tests passing.

---

## Follow-up Session — 2026-07-11 (same day, user-requested)

### [12:50 UTC] Scope

User reviewed `FutureFeatures.md` item #6 ("Backlink-aware Markdown export") and asked for it to be built, with explicit guardrails since it's the first Connectome feature that writes to files it didn't create itself. Implementing as an addition to tonight's build rather than a separate build folder, since it's a direct extension of the same tool.

### [13:05 UTC] Design

New `src/backlinks.py` module: `format_block()`/`find_block()`/`apply_block()` handle a single idempotent delimited block (`<!-- connectome:links:start -->` … `:end -->`) per note, inserted/replaced/removed via string offsets — no note content outside the block is ever touched. Link targets use the note's filename stem (`[[note-a|Display Title]]`), matching how Obsidian actually resolves `[[links]]`.

New `backlinks` CLI subcommand in `main.py`: dry-run by default (prints a unified diff, writes nothing); `--write` required to touch disk.

### [13:15 UTC] Guardrail: git baseline required for `--write`

First pass gated `--write` on `is_git_repo()` (bare `git rev-parse --is-inside-work-tree`). Manual verification caught a real gap: a freshly `git init`'d directory with nothing committed passes that check but gives no actual undo path — `git diff` has nothing to compare against. Replaced the gate with `git_baseline_problem()`, which additionally requires a commit to exist (`git rev-parse --verify HEAD`) and a clean working tree (`git status --porcelain` empty), with a distinct, specific refusal message for each failure mode (not a repo / no commits yet / uncommitted changes present). `--skip-git-check` remains as an explicit, named escape hatch. Re-verified manually: `backlinks --write` against a directory with committed sample notes now produces a `git diff` that cleanly shows exactly the inserted blocks, revertible with `git checkout -- .`.

### [13:20 UTC] Guardrail: don't overwrite un-indexed edits

`write_plans()` re-reads each file from disk immediately before writing and compares its content hash to the body that was actually indexed; if they differ (the user edited the note after `index` but before `backlinks --write`), that note is skipped with a named warning instead of silently clobbering the edit.

### [13:25 UTC] Bug found during manual smoke test: DB left stale after writing

Manual run against real `sample_notes/` (indexed, then `backlinks --write`, then `backlinks --write` again) showed the second run reporting notes as "skipped (changed on disk)" instead of "already up to date" — because writing to disk updated the files but not the `notes` table, so the next run's staleness check compared the DB's pre-write body against the now-updated disk content and (correctly, but confusingly) flagged a mismatch. Fixed by having `cmd_backlinks` call `storage.upsert_note()` for each successfully written note immediately after writing, keeping the DB's body/content_hash in sync with what's now on disk. Added `test_backlinks_write_syncs_db_so_next_index_run_skips_written_notes` as a regression test.

### [13:35 UTC] Tests

Added `tests/test_backlinks.py` (21 tests: block formatting, find/insert/replace/remove, idempotency, `git_baseline_problem()` across all four states, `write_plans()` staleness handling) and 8 new CLI-level tests in `tests/test_cli.py` (dry-run leaves files untouched; `--write` refused for no-git / no-commit / dirty-tree; `--skip-git-check` bypasses the guard; a full write-then-reindex round trip; stale-note skip at the CLI level).

Tests: 80 passed, 0 failed (`python -m pytest tests/ -v`) — up from 48.

### [13:45 UTC] Manual verification

Ran the full flow against a real, git-committed copy of `sample_notes/` (not just pytest fixtures): `index` → `backlinks` (dry run, confirmed correct diffs for all 6 notes) → `backlinks --write` (confirmed `git diff --stat` shows exactly the 6 files with clean, additive hunks) → `backlinks --write` again (confirmed "already up to date", not a duplicate block). Separately confirmed `--write` against an uncommitted `git init`-only directory refuses with the "no commits yet" message, and against a directory with local uncommitted changes refuses with the "uncommitted changes" message — both leaving the target files byte-for-byte unchanged.

### [13:50 UTC] Documentation

Updated `PRD.md` (moved this capability from Out of Scope into In Scope with the guardrail description, updated Folder Structure and Testing Strategy), `Manual.md` (new command section, config table rows, troubleshooting rows, known-limitations rows), and `FutureFeatures.md` (marked item #6 done with a summary of what shipped, added two new follow-on ideas: frontmatter-aware insertion point, and a proactive rename warning).

Follow-up session complete. All tests passing (80/80). Guardrails manually verified against real git states, not just mocked ones.

---

## Follow-up Session 2 — 2026-07-11 (same day, user-requested)

### [14:05 UTC] Scope

User asked for `FutureFeatures.md` item #4 ("Phrase-level extraction") next: capture simple two-word phrases alongside single-token concepts.

### [14:10 UTC] Design

Added `extraction.extract_bigrams()`: joins literally-adjacent word pairs in the raw (pre-stopword-filter) token stream, requiring *both* words to individually pass the same content-word filter `tokenize()` uses (not a stopword, `len >= MIN_TOKEN_LEN`). This means a stopword sitting between two content words ("stress and coping") correctly blocks the join, rather than skipping over it. `compute_document_frequencies()` and `extract_concepts()` were extended to fold bigram phrases into the same term/score space as unigrams — a phrase only wins a top_n slot on its own TF-IDF score, not a reserved quota, per the FutureFeatures wording ("alongside single terms").

### [14:20 UTC] Tests

Added 6 new tests to `tests/test_extraction.py`: bigram formation across adjacent content words, exclusion when a stopword sits between the words, exclusion when either word is below `MIN_TOKEN_LEN`, empty/single-word input produces no bigrams, `compute_document_frequencies` counts a phrase across notes (not occurrences within one), and `extract_concepts` includes a bigram in its ranked output ahead of a lower-scoring single word.

Tests: 86 passed, 0 failed (`python -m pytest tests/ -v`) — up from 80.

### [14:25 UTC] Manual verification

Re-indexed the real `sample_notes/` corpus (not just fixtures) and inspected the stored per-note concepts directly: phrases like "canada list", "semiconductor capex", "screening workflow", and "affective empathy" now appear as top-ranked concepts for their respective notes — exactly the kind of two-word idea that was previously split into two separate, less meaningful single-word tokens. Rendered `output/index.html` and confirmed phrase terms are present in the embedded tag-cloud JSON (a small number make the top-40 tag cloud specifically, since a phrase's document frequency across only 6 notes is usually 1, competing against single words with the same rarity — expected given the corpus size, not a bug). `related`/link output for this corpus is unchanged (3 links, same pairs) since the specific note pairs in `sample_notes/` happen to share single words, not identical phrases — the phrase-sharing case is covered by the new unit test instead.

### [14:30 UTC] Documentation

Updated `PRD.md` (Scope and Testing Strategy), `Manual.md` (Known Limitations — replaced "single-word only" with the new two-word capability and its remaining three-word-phrase gap), and `FutureFeatures.md` (marked item #4 done with a verification summary; updated the corresponding Known Limitations table row, replacing the fixed limitation and adding the residual overlapping-bigram gap as a new suggested fix).

Follow-up session 2 complete. All tests passing (86/86). Verified against the real sample_notes corpus, not just fixtures.

---

## Follow-up Session 3 — 2026-07-11 (same day, user-requested)

### [15:00 UTC] Scope

User asked, after a discussion about semantic (embedding-based) linking (FutureFeatures #10 — investigated and explicitly deferred this session; see that entry for the PyPI-reachable/HuggingFace-blocked findings), whether Connectome could span more than notes — notes, academic papers, news articles — with filterable categories, plus a "subcategory" layer derived from the existing keyword extraction. Explicit user framing: "ingesting isn't the feature, displaying the connectome is" — so real Papers/News data sources were deliberately out of scope; synthetic sample data was used instead, confirmed with the user before starting (Recommended option in an AskUserQuestion). Subcategory mechanism was also confirmed with the user: hybrid — deterministic clustering by default, optional AI relabeling as polish (matching the existing `--ai` graceful-fallback pattern used elsewhere in this build).

### [15:10 UTC] Schema

Added `category TEXT NOT NULL DEFAULT 'Notes'` and `subcategory TEXT` to `notes`; uniqueness moved from `UNIQUE(path)` to `UNIQUE(category, path)` so the same relative filename can exist independently in two categories. `storage._migrate_schema()` adds both columns via `ALTER TABLE` to a pre-existing table (checked via `PRAGMA table_info`) — a migrated table keeps its old single-column unique constraint since SQLite can't alter table constraints in place; documented as a known limitation rather than silently worked around. `storage.upsert_note`/`get_note_by_path` now take a `category` argument; added `find_note_by_path_any_category` (category-agnostic, for CLI convenience lookups like `related`), `all_notes(category=...)`, `get_categories`, `set_subcategory`, and a `category`-scoped `search_notes`.

### [15:25 UTC] Subcategory clustering (new `clustering.py`)

Deterministic subcategory assignment reuses the note-to-note links `linking.py` already computes — no separate concept graph needed. Union-find groups notes whose link score is at or above the corpus's median link score (a rough heuristic, consistent with this build's other tuning constants like `top_n`); an isolated note becomes its own singleton cluster. Each cluster is named from its own aggregate top concepts (e.g. "Session / Context / Agent"). An optional batched Claude call (`relabel_with_claude`, one API call for the whole corpus's clusters, not one per cluster) proposes cleaner names; any cluster missing from the response, or the whole call on total failure (no key/network error/bad status/malformed JSON), falls back to the deterministic name — proven per-cluster, not all-or-nothing, via a dedicated test.

### [15:35 UTC] Wiring into `main.py`

`index` gained `--category` (default `"Notes"`). Critical correctness point caught during design, not by accident: "removed" (file-no-longer-on-disk) detection had to be scoped to the *current* category's existing notes only — the original single-category code compared the whole `notes` table against `seen_paths`, which would have made indexing a second category (e.g. `sample_papers/`) look like every `Notes`-category file had been deleted, since none of them are in the papers folder. Fixed by scoping `existing_notes` to `storage.all_notes(conn, category=category)`. Links, doc frequencies, and subcategories are still recomputed over `storage.all_notes(conn)` (unscoped) after any category's index run, so cross-category connections form. `search`/`stats` gained an optional `--category` filter (`stats` without one now also prints a per-category breakdown). `backlinks` gained `--category`; `plan_backlinks` in `backlinks.py` gained an optional `lookup_notes` parameter so a category-scoped write can still correctly resolve a related item's title/path when that item lives in a *different* category (otherwise it would render as a broken `[[|?]]` link) — backward compatible, defaults to the old single-list behavior when omitted.

### [15:50 UTC] Rendering

`render.build_data` now includes `category`/`subcategory` per note and a top-level `categories` list. The HTML template gained a category filter panel (single-select, same interaction pattern as the existing tag cloud, for consistency), category badges on note-list items and the note-detail header, a subcategory label, and category-colored concept-graph nodes (a small fixed 6-color palette cycled by category index) with a legend shown whenever more than one category is indexed.

### [16:00 UTC] Sample data

Added `sample_papers/` (3 fictional paper abstracts) and `sample_news/` (3 fictional news articles) alongside the existing `sample_notes/`. Content was deliberately written, not generic filler, to share vocabulary with three specific existing sample notes so the demo graph is populated immediately: AI agent session handoffs ↔ an agent-context-continuity paper ↔ a coding-agent-tooling news article; the semiconductor capex thesis note ↔ a capex-cycle paper ↔ a hyperscaler capex-guidance news article; the Canada List ownership note ↔ a foreign-ownership-classification news article. All content is fictional/illustrative, matching the existing sample data's disclosed-synthetic pattern.

### [16:10 UTC] Tests

Added `tests/test_clustering.py` (19 tests: union-find grouping/threshold/transitivity, cluster naming, AI relabeling success/partial-fallback/total-fallback, end-to-end `assign_subcategories`). Extended `tests/test_storage.py` (+11: cross-category same-path uniqueness, category-scoped vs. unscoped lookups, `get_categories`, `set_subcategory`, category-scoped search, and a dedicated migration test that hand-builds a pre-2026-07-11 `notes` table and confirms `storage.connect()` upgrades it in place). Extended `tests/test_cli.py` (+8: a second category's `index` run doesn't remove the first category's notes, a real cross-category link forms from deliberately overlapping fixture vocabulary, every note gets a non-null subcategory, `search --category` and `stats --category` scope correctly, `related` surfaces and labels a cross-category match, and an `--ai` end-to-end test proving both the per-note enrichment call *and* the batched subcategory-relabeling call fire). Extended `tests/test_render.py` (+3: category/subcategory in the JSON payload, the `categories` list, category text present in the rendered detail div).

One real bug caught by the `--ai` end-to-end test's design, not by inspection: `extraction.py` and `clustering.py` both `import urllib.request`, which is the same cached module object in both — patching `extraction.urllib.request.urlopen` and `clustering.urllib.request.urlopen` as two separate mocks in the same test silently made the second patch clobber the first, so the "extraction" mock never actually intercepted anything. Fixed by using a single shared mock and asserting on total call count (4 per-note enrichment calls + 1 batched cluster-relabel call = 5) instead of two independently-asserted mocks.

Tests: 125 passed, 0 failed (`python -m pytest tests/ -v`) — up from 86.

### [16:25 UTC] Manual verification

Indexed all three real sample folders into one database (`index --category Notes`, `--category "Academic Papers"`, `--category "News Articles"`) — 12 items total, 15 links, all three deliberately-seeded topic clusters confirmed linking across all three categories via `related` (e.g. "AI Agent Session Handoffs" → a paper and a news article, both correctly labeled by category, sharing concepts including the bigram phrase "power cooling" from the earlier phrase-extraction follow-up). `stats` showed the correct per-category breakdown (Notes: 6, Academic Papers: 3, News Articles: 3). Rendered `output/index.html` and drove it in real headless Chromium via Playwright (installed fresh this session; the Chromium binary was already pre-provisioned): confirmed 12 note items render, clicking the "Academic Papers" category chip narrows the list to exactly 3 items, the legend shows 3 category dots, clicking a note shows its category and subcategory in the detail header and a correctly cross-category-labeled related list — zero console or page errors throughout.

### [16:35 UTC] Documentation

Updated `PRD.md` (Goal/User Story extended, two new In Scope bullets, four new Out of Scope bullets including the embedding-model investigation findings, schema/folder-structure/testing-strategy updates, two new Success Criteria), `Manual.md` (version bump, "What This Is" and Quick Start extended, new "Categories and subcategories" section, category flags threaded through Searching/Related/Stats/Backlinks/Build, Configuration table rows, Troubleshooting rows, five new Known Limitations covering single-select filtering, cross-category path-lookup ambiguity, deferred real ingestion, and the embedding-model findings), and `FutureFeatures.md` (item #10 marked investigated-not-built with findings; item #8 annotated with what the new category system does and doesn't provide; new item #13 marking tonight's work done with a full summary; two new items, #14 real ingestion and #15 multi-select filtering, as the natural next steps).

Follow-up session 3 complete. All tests passing (125/125). Verified against real seeded cross-category data in both the CLI and a real browser, not mocked.
