# PRD — Provenance

## Goal

Turn a spreadsheet of business names into a Canadian-ownership research batch job: a CLI that resolves each one against free public data, applies a transparent rule engine to classify it Canadian / Foreign / Uncertain with a confidence score and cited evidence, and writes an enriched CSV plus a persistent local research history — instead of researching each company one at a time.

## User Story

As the person curating businesses for The Canada List, I have a CSV of dozens-to-hundreds of candidate businesses from a submission form or a scraped list. Today, verifying each one's Canadian-ownership status means opening a browser tab per company and manually checking Wikipedia/corporate filings/news. I want to point a tool at the whole CSV, walk away, and come back to an enriched file with a verdict, a confidence score, and the evidence trail for every row — flagging only the genuinely uncertain ones for me to look at by hand.

## Scope

### In scope
- CSV batch input: one row per business, `name` column required, optional `website` and `notes` columns passed through untouched to the output.
- Per-business resolution via the free, no-auth Wikidata API: entity search → claims lookup for country (`P17`), headquarters location (`P159`), parent organization (`P749`), owned by (`P127`); one-hop resolution of a parent/owner's own country when the business's own claims don't state one directly.
- A deterministic rule engine (ported and extended from the same shape CanFile proved on 2026-07-20, reimplemented fresh in this build's own folder — no cross-build imports) that turns resolved claims into a verdict (`canadian` / `foreign` / `uncertain`) with a 0–1 confidence score and a plain-English rationale citing exactly which claim(s) drove the call.
- Local SQLite cache keyed by normalized business name: a business already resolved in a prior run is served from cache (no re-query) unless `--refresh` is passed, so repeated batches over overlapping business lists don't re-hit the API or burn rate-limit budget. Every resolution is stored as a new, append-only version (never overwritten) so a business's classification history is inspectable — same "never overwrite, always version" pattern this catalog's other research-ledger builds (CanFile, Manuscript Pipeline, Panel Prep) use.
- Optional Claude Haiku enrichment (`--ai-enrich`, requires `ANTHROPIC_API_KEY` at runtime) that writes a one-sentence plain-English summary of *why* a business landed in the `uncertain` bucket, from the same resolved claims the deterministic engine already saw — never a second opinion that can override the rule engine's verdict. Unconditional deterministic fallback (empty/omitted note) with zero network calls when no key is set.
- CSV output: every input column preserved, plus `verdict`, `confidence`, `evidence`, `wikidata_qid` (or blank if unresolved), and `ai_note` columns appended.
- Terminal summary after every run: counts by verdict, cache hit/miss counts, and a short list of `uncertain` rows worth a human look.
- `--render` flag: optional self-contained dark-mode HTML batch report (sortable/filterable table, verdict breakdown) for reviewing a large batch without opening the CSV in a spreadsheet app.
- A companion Claude Code Skill (`skill/SKILL.md`) wrapping the CLI, so a coding session working on Canada List content can invoke it on a CSV the user just produced ("classify this batch of businesses") without leaving the session — matching the precedent Snipvault (2026-08-12) set for shipping a Skill alongside a CLI.

### Out of scope
- No live web scraping beyond Wikidata/Wikipedia's own REST APIs (no arbitrary corporate-filing lookups — those aren't in PROFILE.md's Data Sources).
- No automatic write-back into The Canada List's actual production database — output is a CSV the curator reviews and imports manually. Wiring this into a live ingestion pipeline is a `FutureFeatures.md` item, not tonight's scope.
- No fuzzy/duplicate-business detection across the input CSV itself (that's Ingest Gate's job, 2026-08-10) — this tool assumes one row per distinct business already.
- No UI beyond the optional static HTML report; Category B does not require a visual interface per `STANDARDS.md`, and the CLI + CSV + Skill is the primary interface.

## Tech Stack

- Python 3, stdlib only for the core (`urllib.request` for Wikidata/Wikipedia HTTP, `sqlite3` for the cache/history, `csv`, `argparse`, `json`, `html` for the report).
- `urllib.request` for the optional Anthropic API call (matches the pattern used by CanFile, Manuscript Pipeline, and every other B/C-category build this catalog has shipped — no SDK dependency).
- `pytest` for tests, all network calls mocked via `unittest.mock.patch` on `urllib.request.urlopen`.
- No `requirements.txt` third-party entries needed (stdlib only) — file still created, documented as empty by design.

## Data Structure

SQLite schema (`provenance.db`, created in the build's own working directory when the CLI first runs — never committed):

```sql
CREATE TABLE resolutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_key TEXT NOT NULL,        -- normalized (casefold + whitespace-collapsed) business name
    business_name TEXT NOT NULL,       -- original input name, preserved verbatim
    website TEXT,
    wikidata_qid TEXT,
    verdict TEXT NOT NULL,             -- 'canadian' | 'foreign' | 'uncertain'
    confidence REAL NOT NULL,
    evidence TEXT NOT NULL,            -- plain-English rationale citing the claim(s) used
    ai_note TEXT,                      -- optional Claude enrichment, only ever populated for 'uncertain'
    resolved_at TEXT NOT NULL          -- ISO 8601 UTC timestamp
);
CREATE INDEX idx_business_key ON resolutions(business_key);
```

Batch CSV row shape (in-memory, mirrors the output CSV's columns): `name, website, notes, verdict, confidence, evidence, wikidata_qid, ai_note`.

## Folder Structure

```
builds/2026-08-15-provenance/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt          ← empty by design (stdlib only), documented in Manual.md
├── skill/
│   └── SKILL.md
├── src/
│   ├── __init__.py
│   ├── wikidata.py           ← Wikidata/Wikipedia HTTP client (search, claims, label resolution)
│   ├── rules.py               ← deterministic verdict/confidence/evidence rule engine
│   ├── store.py               ← SQLite cache/history layer
│   ├── ai_enrich.py           ← optional Claude Haiku enrichment call + deterministic fallback
│   ├── batch.py                ← CSV in → per-row resolution (cache-first) → CSV out orchestration
│   ├── report.py              ← self-contained HTML report renderer
│   └── cli.py                  ← argparse entry point (classify / history / render)
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   └── sample_businesses.csv
    ├── test_rules.py
    ├── test_wikidata.py
    ├── test_store.py
    ├── test_ai_enrich.py
    ├── test_batch.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- `pytest`, all tests in `tests/`, run with `python -m pytest tests/ -v`.
- **Rule engine (`test_rules.py`):** direct country match → `canadian`/`foreign` with high confidence; no country claim but a resolvable Canadian parent → `canadian` via one-hop with reduced confidence; conflicting country vs. headquarters claims → `uncertain`; zero claims resolved at all → `uncertain` with confidence 0 and an evidence string saying so; confidence is always in `[0, 1]`.
- **Wikidata client (`test_wikidata.py`):** entity search parses a mocked search-API JSON response into a QID; claims lookup extracts country/headquarters/parent/owner claim values from a mocked claims response; a 0-result search returns `None` cleanly (no crash on a business Wikidata has never heard of); a malformed/empty API response is handled without raising.
- **Store (`test_store.py`):** a resolution write is retrievable by normalized business key; a second run with the same business name returns the cached row and does not re-resolve; `--refresh` forces a fresh row to be appended (history preserved, not overwritten) and `latest()` returns the newest version; normalization treats `"Acme Inc."` and `"  acme inc.  "` as the same cache key.
- **AI enrichment (`test_ai_enrich.py`):** with no `ANTHROPIC_API_KEY` set, `enrich()` makes zero network calls (asserted via a call-count check on the mocked `urlopen`) and returns `None`; with a key set and a mocked successful response, the note is extracted correctly; a mocked network failure falls back to `None` rather than raising; enrichment is only ever invoked for `uncertain` verdicts, never `canadian`/`foreign`.
- **Batch orchestration (`test_batch.py`):** a small CSV fixture with a mix of resolvable/unresolvable business names produces the expected verdict distribution against fully mocked Wikidata responses; a business already in the cache is not re-queried on a second `classify` run over the same CSV; malformed input rows (missing `name`) are skipped with a warning, not a crash; output CSV column order and header match the PRD's documented shape.
- **Report (`test_report.py`):** rendered HTML contains no unescaped business-name-derived `<script>` tags when a fixture includes an XSS payload as a business name (string-based assertion — content is inserted via a JSON payload consumed with `textContent`/`createElement`, never raw string concatenation into HTML).
- **CLI (`test_cli.py`):** `classify` end-to-end against a fixture CSV and a fully mocked network layer produces the documented output columns; `history <business>` prints the version trail for a business with more than one resolution; running with no arguments prints usage and exits non-zero rather than crashing.
- Minimum 15 tests total across the suite; every test mocks `urllib.request.urlopen` for any Wikidata/Wikipedia/Anthropic call — no live network access in the test suite.

## Success Criteria

1. Running `classify sample.csv --out enriched.csv` against a real, unmocked internet connection (the user's runtime, not the build container) produces an `enriched.csv` with a non-empty `verdict` for every resolvable row, each with a `confidence` in `[0, 1]` and a non-empty `evidence` string.
2. Running `classify` twice in a row over the same CSV produces identical verdicts on the second run and issues zero additional Wikidata queries for rows already cached (verified via the terminal summary's cache-hit count).
3. `--ai-enrich` with no `ANTHROPIC_API_KEY` set makes zero calls to the Anthropic API and the tool still runs to completion with `ai_note` left blank for every row.
4. A business name containing a script-injection payload is rendered as inert, escaped text in both the output CSV and the `--render` HTML report — never executed, never breaking CSV structure.
5. All 15+ tests pass with zero failures, and the STANDARDS.md security checklist (no hardcoded credentials, no `eval`/`exec`, no `innerHTML` from external data, no path traversal, nothing outside this build folder) passes on manual review.

## Idea Brief Traceability

No linked Idea Brief — this idea was freshly generated tonight after both pending Category B backlog rows turned out to be already-built duplicates (see `WhyThis.md`).
