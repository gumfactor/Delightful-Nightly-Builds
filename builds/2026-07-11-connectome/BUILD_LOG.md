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
