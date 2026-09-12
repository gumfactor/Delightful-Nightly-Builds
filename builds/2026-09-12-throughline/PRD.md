# PRD — Throughline

## Goal

A personal research-corpus knowledge base that automatically pulls the user's own publication record and live citation counts from the free Semantic Scholar API, deterministically clusters their papers into thematic groups, tracks citation growth over time, and produces a grant/CV-ready "research narrative" per theme.

---

## User Story

As a researcher who has to repeatedly reconstruct "what my body of work is about" for grant biosketches, promotion dossiers, and manuscript intros, I want a tool that automatically pulls my publication list, groups it into real thematic clusters, and tracks how each paper's citation count grows over time, so I stop manually re-reading my own CV every time I need to describe my research program.

---

## Scope

### In scope
- `lookup`: search the Semantic Scholar author-search API by name and print a disambiguated candidate list (id, affiliations, paper count, sample titles) so the correct author is confirmed once, manually, before any data is stored
- `sync`: fetch the confirmed author's full paper list (title, year, venue, abstract, citation count, external ids) from Semantic Scholar and upsert into a local SQLite database; each sync also appends a timestamped citation-count snapshot per paper so growth is trackable across runs
- `cluster`: fully deterministic, stdlib-only thematic clustering of the local paper corpus — corpus-wide TF-IDF-style keyword extraction over title+abstract text, followed by keyword-overlap (Jaccard) grouping into named clusters; re-runnable and stable for an unchanged corpus
- `narrative`: per-cluster summary — a deterministic template by default (top keywords, year range, paper count, total citations, paper titles), or, with `--ai` and `ANTHROPIC_API_KEY` set, a Claude Haiku-generated one-paragraph "research narrative" built strictly from already-stored titles/abstracts/keywords; unconditional deterministic fallback on any error or missing key, with zero network calls when AI is not requested or no key is present
- `growth`: compares the two most recent citation snapshots (or first vs. latest) per paper and in aggregate, reporting citation-count deltas since last sync
- `render`: self-contained dark-mode HTML dashboard — cluster cards with narrative text, a sortable paper table (citations/year), a citation-growth chart (Chart.js via pinned CDN URL, with a DOM-table fallback if the chart library fails to load), and a live client-side search box filtering by title/venue/keyword
- Local SQLite persistence (`throughline.db` inside the build's own working directory), safe against re-sync (upsert by Semantic Scholar `paperId`, never duplicates)
- Companion Claude Code Skill (`skill/SKILL.md`) so a sync + narrative pass can be triggered on request from within a coding session, following this catalog's established precedent (GradeLine, Promptbook, Grant Vault, CiteForge, Snipvault, Provenance, Lecture Loom)

### Out of scope
- Automatic author disambiguation without human confirmation (name search is inherently ambiguous; `lookup` always requires the user to pick an author id explicitly before `sync` will run)
- Co-author network graphs or institution-level analytics
- Editing/removing individual papers from the local database (a full `sync` re-run always reconciles state)
- Any OAuth-based service (Google Scholar, ORCID member API) — Semantic Scholar's Graph API needs no authentication for the endpoints used here
- Sending any local data to a third party other than the optional, user-initiated Claude Haiku call, which receives only paper titles/abstracts/keywords already fetched from the public Semantic Scholar API — never the user's name, email, or any PROFILE.md content

---

## Tech Stack

- Python 3, stdlib only for all core logic (`urllib.request` for HTTP, `sqlite3` for storage, `argparse` for the CLI)
- `anthropic` Python package only imported lazily inside the optional `--ai` path; the HTTP call itself goes through `urllib.request` against `https://api.anthropic.com/v1/messages` (model `claude-haiku-4-5-20251001`) so no SDK dependency is required at all — consistent with this catalog's established pattern
- `pytest` for tests, with an injectable HTTP transport so every Semantic Scholar and Anthropic call is mocked in tests
- Chart.js 4.4.4 via pinned CDN URL for the citation-growth chart in the rendered dashboard, with a DOM-table fallback

---

## Data Structure

### SQLite schema (`throughline.db`)

```sql
CREATE TABLE author (
    id INTEGER PRIMARY KEY CHECK (id = 1),   -- single-author, single-row table
    author_id TEXT NOT NULL,
    name TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE papers (
    paper_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    year INTEGER,
    venue TEXT,
    citation_count INTEGER NOT NULL DEFAULT 0,
    external_url TEXT,
    first_seen_at TEXT NOT NULL,
    last_synced_at TEXT NOT NULL
);

CREATE TABLE citation_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    citation_count INTEGER NOT NULL,
    snapshot_at TEXT NOT NULL
);

CREATE TABLE clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,          -- top keywords joined, e.g. "stress / cortisol / coping"
    keywords TEXT NOT NULL,       -- JSON array of keywords, ranked
    computed_at TEXT NOT NULL
);

CREATE TABLE cluster_papers (
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    PRIMARY KEY (cluster_id, paper_id)
);

CREATE TABLE narratives (
    cluster_id INTEGER PRIMARY KEY REFERENCES clusters(id),
    text TEXT NOT NULL,
    source TEXT NOT NULL,   -- "ai" or "deterministic"
    generated_at TEXT NOT NULL
);
```

### In-memory paper record (fetch layer)

```python
{
    "paper_id": str,
    "title": str,
    "abstract": str | None,
    "year": int | None,
    "venue": str | None,
    "citation_count": int,
    "external_url": str | None,
}
```

---

## Folder Structure

```
builds/2026-09-12-throughline/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── skill/
│   └── SKILL.md
├── src/
│   ├── __init__.py
│   ├── semantic_scholar.py   # HTTP client, injectable transport, author search + paper fetch
│   ├── storage.py            # SQLite schema + upsert/query helpers
│   ├── cluster.py            # deterministic TF-IDF keyword extraction + Jaccard clustering
│   ├── narrative.py          # deterministic template + optional Claude Haiku synthesis
│   ├── render.py             # self-contained HTML dashboard generator
│   └── cli.py                # argparse commands: lookup/sync/cluster/narrative/growth/render
└── tests/
    ├── test_semantic_scholar.py
    ├── test_storage.py
    ├── test_cluster.py
    ├── test_narrative.py
    ├── test_render.py
    └── test_cli.py
```

---

## Testing Strategy

- **Semantic Scholar client**: mock `urllib.request.urlopen` with fixture JSON for author search and author+papers fetch; test successful parsing, empty results, HTTP error (404/429) handling, and malformed-JSON handling. No live network calls in any test.
- **Storage**: use an in-memory (`:memory:`) SQLite database per test; test schema creation, paper upsert (insert then update leaves one row, updates citation_count and last_synced_at), citation snapshot append-only behaviour, and cluster/narrative persistence.
- **Cluster**: hand-built fixture corpus of papers with known keyword overlap (e.g. two "stress/cortisol" papers, two "regex/pattern-matching" papers, one unrelated singleton) — assert the deterministic algorithm produces exactly the expected groupings; test the zero-paper and one-paper edge cases; test that re-running clustering on an unchanged corpus is stable (same groupings).
- **Narrative**: test the deterministic template output against a known cluster; test the AI path with a mocked Anthropic HTTP call (success and error-triggers-fallback cases); test that with no `ANTHROPIC_API_KEY` set, the AI code path is never invoked (assert zero calls to the injected transport).
- **Render**: test that the generated HTML is valid, includes the JSON payload script tag with `</script` escaped, and that a deliberately hostile paper title (`</script><script>window.__xss=true;</script>`) appears only as escaped/inert text in the output, never as an executable tag.
- **CLI**: test argument parsing and command dispatch for all six commands using a temporary SQLite file and monkeypatched fetch/AI functions; test error handling for `sync` without a prior `lookup`-confirmed author id, and for `narrative --ai` with no papers clustered yet.
- Minimum 15 tests; target broad coverage of the happy path, edge cases (no papers, no abstract text, ambiguous author search, rate-limited API, missing API key), and error states.
- Run with `python -m pytest tests/ -v`.

---

## Success Criteria

1. `lookup <name>` queries the (mocked-in-tests, real-at-runtime) Semantic Scholar author-search endpoint and prints a disambiguated, human-readable candidate list — never auto-selects an author.
2. `sync --author-id <id>` populates the local SQLite database with the author's full paper list and citation counts, and a second `sync` run does not duplicate any paper row (upsert verified).
3. `cluster` deterministically groups a fixture corpus with known thematic overlap into the expected clusters, and produces stable output on repeated runs against an unchanged corpus.
4. `narrative` produces a correct deterministic summary for every cluster with no API key present, makes zero network calls to the Anthropic endpoint in that mode, and correctly falls back to the deterministic template if the AI call fails when `--ai` is requested.
5. `render` produces a self-contained HTML file that is safe against script injection from paper metadata (verified by test) and correctly displays clusters, the paper table, and citation growth.
6. All tests pass: `python -m pytest tests/ -v` reports zero failures, minimum 15 tests.
