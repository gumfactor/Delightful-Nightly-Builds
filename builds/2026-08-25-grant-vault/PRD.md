# PRD — Grant Vault

> **Build date:** 2026-08-25
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious Project
> **Day of week:** Tuesday → Solid/Ambitious target (nightly builds are ambitious by default per CLAUDE.md calibration note)

---

## Goal

A local knowledge base that mines the user's own past grant documents for reusable, section-tagged, reusability-scored prose, so a new grant draft starts from proven language instead of a blank page.

## User Story

As an Associate Professor who writes grants regularly (an explicit friction point: "Things you do manually that you suspect could be automated" lists Grant writing and Research administration), I want to feed in my past grant drafts and get back a searchable, section-organized library of the prose I can safely reuse, so that I stop re-writing broadly-applicable Significance/Broader Impacts/Data Management language from scratch every submission cycle.

## Scope

### In Scope
- `ingest <path>` — reads a single `.txt`/`.md` file or every such file in a folder; splits each into paragraph-level chunks
- Deterministic section classifier — tags each chunk as one of: Specific Aims, Significance, Innovation, Approach, Broader Impacts, Data Management Plan, Budget Justification, Other (heading-line detection first, keyword-signature scoring fallback)
- Deterministic reusability scorer (0–10, tiered High/Medium/Low) — rewards portable length and generic/transferable language, penalizes chunks anchored to specifics (dollar figures, calendar years, named-entity-like capitalized phrases)
- Deterministic corpus-wide, rarity-weighted keyword tagging (stdlib TF-IDF-style, no external NLP library)
- Optional AI enrichment (`--ai` flag, requires `ANTHROPIC_API_KEY`): one-sentence abstractive summary + suggested tags per chunk via Claude Haiku; silently falls back to the deterministic tags with zero network calls when the flag is off or no key is set
- Local SQLite store (`documents`, `chunks` tables) with content-hash-based incremental ingest — unchanged files are skipped, changed files are re-chunked
- `search <query>` — ranked full-text-ish search over stored chunks, filterable by `--section`, `--tag`, `--min-reuse`
- `stats` — terminal summary: chunk counts by section/tier, document count, top tags
- `render [--output PATH]` — self-contained dark-mode HTML dashboard: per-section tabs, client-side search box, tag filter chips, reusability badges, copy-to-clipboard per chunk; all chunk text embedded as JSON and rendered via `textContent`/`createElement` only (no `innerHTML` from stored text)
- Hand-authored synthetic fixture grant documents (no real personal data) for tests and manual verification

### Out of Scope
- PDF/DOCX ingestion (plain text/Markdown only tonight — PDF text extraction is a clean follow-up)
- Cross-document duplicate/near-duplicate chunk merging
- A "compose a new draft" auto-assembly feature that stitches retrieved chunks into a new section — tonight ships retrieval, not generation
- Multi-user / cloud sync — this is a single-user local tool

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None (stdlib CLI via `argparse`)
- **Dependencies:** `pytest` (test-only). Runtime is stdlib-only: `sqlite3`, `re`, `json`, `hashlib`, `collections`, `math`, `urllib.request` (only for the optional Anthropic call)
- **Runtime requirement:** `python3 main.py <command> ...` — no install beyond `pip install -r requirements.txt` for tests

## Data Structure

SQLite database (default path `./grantvault.db`, overridable with `--db`):

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    content_hash TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    section_type TEXT NOT NULL,
    text TEXT NOT NULL,
    reuse_score INTEGER NOT NULL,
    reuse_tier TEXT NOT NULL,
    tags TEXT NOT NULL,          -- JSON list of strings
    ai_summary TEXT,             -- NULL unless --ai enrichment ran
    created_at TEXT NOT NULL
);
```

`render` reads the whole store and embeds it as one JSON array in a `<script type="application/json" id="data">` block; the page's vanilla JS parses that and builds the DOM client-side.

## Folder Structure

```
builds/2026-08-25-grant-vault/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── chunking.py
│   ├── classifier.py
│   ├── scorer.py
│   ├── tagging.py
│   ├── store.py
│   ├── ai_enrich.py
│   ├── ingest.py
│   ├── search.py
│   ├── render.py
│   └── cli.py
├── fixtures/
│   ├── sample_grant_aims_significance.txt
│   └── sample_grant_approach_budget.txt
└── tests/
    ├── __init__.py
    ├── test_chunking.py
    ├── test_classifier.py
    ├── test_scorer.py
    ├── test_tagging.py
    ├── test_store.py
    ├── test_ingest.py
    ├── test_search.py
    ├── test_ai_enrich.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (from the build folder)
- **What will be tested:**
  - Chunking: paragraph splitting, blank-line variants, trailing whitespace, empty-file edge case
  - Classifier: heading-line override for each of the 7 named section types, keyword-signature fallback, ambiguous text → "Other"
  - Scorer: hand-computed reference scores for a specificity-anchored chunk (low), a generic transferable chunk (high), and length-penalty edge cases (too short / too long); tier boundary correctness
  - Tagging: stopword filtering, corpus-wide rarity weighting, determinism (same input → same tags)
  - Store: schema creation, document upsert, content-hash change detection, chunk insert/retrieve
  - Ingest: incremental skip of unchanged files, folder ingestion of multiple files, malformed/empty file handled without crashing
  - Search: relevance ranking, `--section`/`--tag`/`--min-reuse` filters, no-results case
  - AI enrichment: mocked `urlopen` — zero network calls with no API key or `--ai` unset; successful mocked response parsed and stored; malformed response and network error both fall back to deterministic tags without raising
  - Render: valid HTML produced, chunk text containing `<script>`/`</script>` payloads is JSON-escaped and never emitted as a raw tag outside the embedded JSON block (XSS regression test), all section types represented as tabs when data exists
  - CLI: argparse wiring for all four subcommands, missing-path error handling, custom `--db` path honored

## Success Criteria

1. All tests pass (zero failures)
2. `ingest` on the two fixture documents produces at least one chunk per section type across the corpus, each with a section tag, a reuse tier, and at least one keyword tag
3. Re-running `ingest` on unchanged fixtures inserts zero new chunks (content-hash skip verified)
4. `render` produces a self-contained HTML file that opens directly (`file://`) with zero console errors, and a chunk containing an injected `<script>` payload renders as inert text, not an executed tag (verified live in a headless browser)
5. With no `ANTHROPIC_API_KEY` set and `--ai` omitted, `ingest`/`search`/`render` make zero network calls end-to-end

---

## Scope Changes

None — the ambitious scope above was fully delivered as planned. (This section will be updated if anything is cut during the build.)
