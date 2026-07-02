# PRD — PubMed Research Radar

## Goal
Give a working neuroscience researcher a personal, AI-triaged feed of new PubMed publications matched to their specific lab topics, so literature review becomes a five-minute daily scan instead of a manual search chore.

## User Story
As a lab director running research on affective neuroscience, psychopathy, empathy, and stress/coping, I want a tool that automatically pulls new PubMed articles matching my saved research topics, ranks them by relevance to my specific interests, and gives me a plain-English summary of each — so I can decide in seconds which papers are worth reading in full, without manually re-running PubMed searches across five topics every week.

## Scope

### In Scope
- Saved, named search topics, each backed by a real PubMed search query (seeded with 5 topics drawn from the user's stated research interests: affective neuroscience, psychopathy, empathy, stress & coping, forensic neuroscience/neuroimaging)
- `fetch`: query PubMed E-utilities (`esearch` + `efetch`, no auth) for articles published in a configurable recent window, parse title/authors/journal/date/abstract/PMID
- Local SQLite store with deduplication by PMID across repeated runs (re-running `fetch` never creates duplicate rows)
- Relevance scoring (1–10) and a plain-English 2–3 sentence summary + methodology tag (e.g. fMRI, behavioral, review, meta-analysis) per article, via Claude Haiku (Anthropic API) when `ANTHROPIC_API_KEY` is set
- Graceful, fully-functional fallback when `ANTHROPIC_API_KEY` is absent: keyword-overlap relevance scoring against the topic's query terms, abstract shown in place of an AI summary, methodology tag left blank — the tool never crashes or blocks on a missing key
- `report`: render a single self-contained dark-mode HTML page — topic tabs, relevance-sorted article list, client-side text search, and starred/read state (persisted via `localStorage` in the browser, since the report is a static file)
- `search`: terminal full-text search across stored titles/abstracts/summaries
- `topics`: list / add / remove saved search topics from the CLI
- `stats`: quick terminal counts (total articles, per-topic breakdown, unscored count)
- Basic XSS-safe HTML escaping of all externally-sourced text (titles/abstracts come from PubMed, an external source) before embedding in the report

### Out of Scope
- Google Scholar sourcing (no public API; would require scraping against ToS) — noted in FutureFeatures.md
- Full-text PDF retrieval or ingestion (PubMed E-utilities only exposes abstracts/metadata, not full text for most articles)
- Multi-user accounts or cloud sync — this is a single-user local tool
- Automatic recurring scheduling (a Routine wrapper is a natural extension, documented in FutureFeatures.md, but tonight ships the core CLI + report first)

## Tech Stack
- Python 3 (stdlib: `sqlite3`, `argparse`, `html`, `xml.etree.ElementTree`, `urllib`/`json`)
- `requests` for HTTP (PubMed E-utilities REST calls, Anthropic Messages API REST calls — no SDK dependency required)
- `pytest` for tests, with all HTTP calls mocked via `unittest.mock` against recorded fixture responses (no live network required to test)
- No frontend build step — the HTML report is a single static file with inline CSS/JS (no CDN dependency needed; all interactivity is vanilla JS)

## Data Structure

SQLite database at `data/radar.db` (created on first `fetch`/`topics add` call; not committed to git — the repo ships empty, the tool creates it locally):

```sql
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE articles (
    pmid TEXT PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    journal TEXT,
    pub_date TEXT,
    abstract TEXT,
    url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    relevance_score REAL,
    ai_summary TEXT,
    methodology_tag TEXT,
    scoring_method TEXT,   -- 'ai' or 'fallback'
    starred INTEGER DEFAULT 0,
    read_state INTEGER DEFAULT 0
);
```

`starred`/`read_state` are maintained server-side too (not just localStorage) so state survives a `report` regeneration if the user later wires up a small local server — for tonight, the static report uses `localStorage` keyed by PMID and the DB columns exist for future extension (documented as such, not read/written by tonight's CLI).

## Folder Structure

```
builds/2026-07-02-pubmed-research-radar/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py         # default topic definitions
│   ├── pubmed.py         # E-utilities client + XML/JSON parsing
│   ├── db.py             # SQLite schema, dedup, CRUD, search
│   ├── ai_scoring.py     # Claude Haiku scoring + keyword fallback
│   ├── report.py         # HTML report rendering (escaping, tabs, search, localStorage)
│   └── cli.py            # argparse entrypoint: fetch/report/search/topics/stats
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── esearch_sample.json
│   │   ├── efetch_sample.xml
│   │   └── efetch_empty.xml
│   ├── test_pubmed.py
│   ├── test_db.py
│   ├── test_ai_scoring.py
│   ├── test_report.py
│   └── test_cli.py
└── data/                 # created at runtime, not committed (.gitkeep only)
```

## Testing Strategy
All tests run offline — every HTTP call (PubMed E-utilities, Anthropic Messages API) is mocked with `unittest.mock.patch` against realistic fixture payloads captured in `tests/fixtures/`. No test requires network access or a real API key, so the suite is deterministic in any environment (including this build sandbox, whose network policy blocks direct calls to external hosts — see BUILD_LOG.md).

- **`test_pubmed.py`** — esearch JSON → PMID list parsing; efetch XML → article dict parsing (title, multi-author formatting, journal, date, abstract, PMID); empty result set handling; malformed/partial XML (missing abstract, missing date) degrades to sensible defaults instead of raising.
- **`test_db.py`** — schema creation is idempotent; inserting the same PMID twice does not duplicate rows (dedup); topic add/list/remove CRUD; search matches title and abstract text (case-insensitive); stats counts total/per-topic/unscored correctly.
- **`test_ai_scoring.py`** — keyword-overlap fallback scorer produces higher scores for on-topic abstracts than off-topic ones; AI scoring path parses a well-formed mocked Anthropic response into (score, summary, methodology tag); a malformed/unparseable AI response falls back to the keyword scorer instead of crashing; scoring path is skipped correctly (uses fallback) when `ANTHROPIC_API_KEY` is unset, verified via `monkeypatch`.
- **`test_report.py`** — rendered HTML contains one tab per topic with articles; articles are sorted by relevance descending within a topic; a title/abstract containing `<script>` or `&` is HTML-escaped in the output (XSS safety, since this text comes from an external source); a topic with zero articles renders without error; report is a single self-contained file (no external asset fetch required to view it, aside from browser-native rendering).
- **`test_cli.py`** — `topics add/list/remove` wiring against a temporary DB path (`tmp_path` fixture); `fetch` invokes the PubMed client and scorer with mocks and persists results; `report` writes an HTML file to the requested path; `search` filters and prints matching rows; unknown subcommand / missing required argument produces a clean error, not a traceback.

Run: `python -m pytest tests/ -v`

## Success Criteria
1. `fetch` pulls articles for all 5 default topics from PubMed, parses them correctly, and stores them with zero duplicate PMIDs across repeated runs — verified by `test_pubmed.py` + `test_db.py` dedup tests.
2. The tool is fully functional with `ANTHROPIC_API_KEY` unset (keyword fallback scoring, no crash, no AI summary) and enhanced when it is set — verified by `test_ai_scoring.py`'s key-present/key-absent paths.
3. `report` produces a single dark-mode HTML file with topic tabs, relevance-sorted articles, working client-side search, and no unescaped external text (XSS-safe) — verified by `test_report.py` and manual inspection in a browser.
4. `search` and `stats` return correct results against a populated local database — verified by `test_cli.py` and `test_db.py`.
5. All 15+ tests pass with zero network calls (fully mocked), confirming the tool's logic is correct independent of any specific runtime's network policy.
