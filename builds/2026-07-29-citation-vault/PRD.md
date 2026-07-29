# PRD — Citation Vault

> **Build date:** 2026-07-29
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious Project

---

## Goal

A local, self-contained personal research-reading tracker that lets the user add papers by DOI (via the free Crossref API) or manual entry, track each one through a to-read → reading → read → cited workflow with notes and tags, and export a clean BibTeX bibliography on demand.

## User Story

As a research lab director and academic who reads across many overlapping projects (a stress-and-coping book, forensic/affective neuroscience manuscripts, grant applications, AI-workflow research), I want a single running ledger of every paper I've encountered — with my own notes and reading status — so that I stop re-finding and re-formatting the same references by hand every time I write something.

## Scope

### In Scope
- `add <doi>` — resolve a paper's metadata (title, authors, year, journal, abstract if available) from the free Crossref REST API and store it
- `add --search "<query>"` — search Crossref by free text, show top candidates, let the user pick one to add
- `add --manual` — add a paper with no DOI (book chapter, preprint, internal report) via CLI flags for title/authors/year/venue
- `status <id> <to-read|reading|read|cited>` — update reading status, timestamped
- `note <id> "<text>"` — append a timestamped personal note to a paper
- `tag <id> <tag1,tag2,...>` — attach manual tags; `--ai-tag` optionally calls Claude Haiku to suggest concept tags from title+abstract, with a deterministic keyword-frequency fallback when no `ANTHROPIC_API_KEY` is set
- `list [--status X] [--tag Y] [--search Q]` — list papers, filterable, newest first
- `show <id>` — full detail view: metadata, tags, full note history
- `resurface [--days N]` — list "read"/"cited" papers not touched in ≥N days (default 60) that share at least one tag with a current "to-read"/"reading" paper — a lightweight nudge to revisit relevant prior reading
- `export bibtex [--tag X] [--status Y] [--out FILE]` — generate a BibTeX file from the filtered set
- `render [--out FILE]` — generate a self-contained dark-mode HTML dashboard: status-column reading queue (kanban-style), tag cloud/filter, live client-side search, per-paper detail panel with note timeline, one-click "copy BibTeX" per paper
- Local SQLite persistence (`citation_vault.db` by default, path configurable) — every add/status/note/tag is durable across runs, nothing is ever silently overwritten
- Optional Claude Haiku integration for two AI-assisted features (tag suggestion, resurface rationale), both with an unconditional deterministic fallback when no API key is present — zero network calls to Anthropic without a key

### Out of Scope
- Full PDF ingestion/OCR or full-text search inside paper PDFs (metadata + user notes only)
- Automatic import from reference managers (Zotero/Mendeley/EndNote) — a future integration, not tonight's scope
- Citation-graph / "papers that cite this paper" traversal — Crossref exposes this but it multiplies API calls and complexity beyond a one-session scope
- Multi-user sharing or cloud sync — this is a single-user local tool by design (STANDARDS.md: no persistent cloud infrastructure)
- Style variants beyond BibTeX (APA/MLA plain-text export) — noted in FutureFeatures.md

## Tech Stack

- **Language:** Python 3
- **Framework:** None — standard library only for the deterministic core (`argparse`, `sqlite3`, `urllib.request`, `json`, `re`, `html`, `datetime`)
- **Dependencies:** None required. `anthropic` package is *not* imported — the optional Claude call uses `urllib.request` directly against the Messages API (matching the pattern used by Voiceprint, Bridgework, and other recent builds), so `requirements.txt` is empty by design.
- **Runtime requirement:** `python3 src/main.py <command> ...` — no install step. `render` produces a static `.html` file the user opens directly in any browser (Chart.js is not needed for a kanban/list layout, so there is no CDN dependency at all).

## Data Structure

SQLite database (default path `citation_vault.db`, override with `--db`):

```sql
CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doi TEXT UNIQUE,              -- NULL for manual entries with no DOI
    title TEXT NOT NULL,
    authors TEXT NOT NULL,        -- JSON array of strings
    year INTEGER,
    journal TEXT,
    abstract TEXT,
    status TEXT NOT NULL DEFAULT 'to-read',   -- to-read | reading | read | cited
    tags TEXT NOT NULL DEFAULT '[]',          -- JSON array of strings
    added_at TEXT NOT NULL,       -- ISO 8601 UTC
    status_changed_at TEXT NOT NULL
);

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    text TEXT NOT NULL,
    created_at TEXT NOT NULL      -- ISO 8601 UTC
);
```

Crossref API responses (`https://api.crossref.org/works/{doi}` and `https://api.crossref.org/works?query=...`) are parsed into this schema; only the fields above are retained (no raw API payload is stored).

## Folder Structure

```
builds/2026-07-29-citation-vault/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── main.py            # CLI entry point (argparse) — command dispatch
│   ├── crossref_client.py # Crossref DOI lookup + search, injectable request function for tests
│   ├── ai_client.py       # Optional Claude Haiku calls (tag suggestion, resurface rationale) + deterministic fallbacks
│   ├── store.py           # SQLite schema + CRUD (papers, notes)
│   ├── bibtex.py          # BibTeX record generation
│   ├── resurface.py       # Tag-overlap + recency resurfacing logic
│   └── render.py          # Self-contained HTML dashboard generator
└── tests/
    ├── test_crossref_client.py
    ├── test_ai_client.py
    ├── test_store.py
    ├── test_bibtex.py
    ├── test_resurface.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python3 -m pytest tests/ -v` (from `builds/2026-07-29-citation-vault/`)
- **What will be tested:**
  - Crossref DOI-lookup response parsing (well-formed record, missing abstract, missing author list, HTTP error, malformed JSON) — all via an injected fake request function, never a live call
  - Crossref search (multiple candidates returned, zero results)
  - SQLite CRUD: add paper (DOI and manual), duplicate-DOI rejection, status transitions with timestamp updates, tag add/replace, note append and ordering
  - Deterministic keyword-tagging fallback (stopword filtering, top-N term extraction) when no API key is set
  - AI tag-suggestion call: success path, missing-key fallback, network-error fallback, malformed-response fallback (all mocked)
  - AI resurface-rationale call: same four paths, mocked
  - Resurface logic: correct recency cutoff boundary, correct tag-overlap matching, correct exclusion of papers still in to-read/reading
  - BibTeX export: correct field escaping, correct filtering by tag/status, correct citation-key generation and de-duplication when two papers would collide
  - HTML dashboard: renders without error given 0 papers / many papers, all paper-supplied text (title, authors, notes, tags) is HTML-escaped against an injected `<script>` payload, kanban columns show the right papers in the right status column
  - CLI argument parsing: each subcommand invoked with valid and invalid arguments, verifying correct exit behavior and error messages

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. A paper can be added via DOI (mocked Crossref response), moved through all four statuses, annotated with notes and tags, and correctly appears/disappears from `resurface` output as its status and tags change
3. `export bibtex` produces valid, correctly-escaped BibTeX entries filterable by tag and status
4. The rendered HTML dashboard opens with zero console errors in headless Chromium and correctly escapes user-supplied text against a script-injection payload
5. Zero network calls to the Anthropic API occur unless `ANTHROPIC_API_KEY` is set, verified by test and by manual `--ai-tag` run with no key present

---

## Scope Changes

(none — filled in during the build only if scope changes)
