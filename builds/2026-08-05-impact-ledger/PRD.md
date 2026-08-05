# PRD — Impact Ledger

> **Build date:** 2026-08-05
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday

---

## Goal

A Python CLI that tracks the real-world citation growth of a researcher's own publications over time (via the free OpenAlex API) and renders a dark-mode HTML dashboard showing citation trends, top-cited papers, and which papers are gaining attention right now.

## User Story

As an Associate Professor who regularly writes grants and manuscripts and needs to speak to research impact, I want a tool that watches how my own publications' citation counts move over time and surfaces which papers are picking up momentum, so that I can quote up-to-date, evidence-backed impact statements without manually re-checking Google Scholar or OpenAlex before every grant deadline.

## Scope

### In Scope
- `search-author` command: query the OpenAlex Authors API by name to find candidate author IDs (disambiguated by affiliation, works count, cited-by count) — no author ID needs to be hardcoded anywhere.
- `sync` command: given an OpenAlex author ID, fetch the author's summary stats (works count, total citations, h-index, i10-index) and every work (title, year, DOI, host venue, citation count, concepts/topics, reconstructed abstract), and store a dated snapshot in local SQLite. Re-running on the same UTC day upserts (never duplicates); running on a later day adds a new snapshot row per work, building a genuine multi-run history.
- `history` command: terminal table showing, per work, citation count at each snapshot date and the delta since the previous snapshot. Clearly states "only one snapshot so far — sync again later to see trends" when history is insufficient.
- `render` command: self-contained dark-mode HTML dashboard —
  - Hero stats (total citations, works count, h-index, i10-index, last synced date)
  - Citation-growth-over-time line chart (Chart.js, only plotted once ≥2 distinct sync dates exist; otherwise a clear "not enough history yet" message — a hand-built DOM table fallback renders if the Chart.js CDN is unreachable)
  - Sortable/searchable paper table (title, year, venue, citations, concepts)
  - "Rising" panel: papers whose citation count increased since the previous snapshot, ranked by citation velocity
  - Optional Claude Haiku one-sentence note per rising paper on why it might be gaining traction (using the paper's own reconstructed abstract + citation delta), with an unconditional deterministic-template fallback when `ANTHROPIC_API_KEY` is not set or the call fails — zero network calls without a key
- All user-facing text (titles, venues, concepts, AI notes) inserted via safe DOM construction (`textContent`/`createElement`), never `innerHTML` from dynamic strings.
- Local SQLite persistence at `data/impact_ledger.db` (created at runtime, not committed).
- Optional `--mailto` flag / `OPENALEX_MAILTO` env var to opt into OpenAlex's "polite pool" for higher rate limits — never hardcoded, always user-supplied.

### Out of Scope
- Co-author network graphs (future extension — see FutureFeatures.md)
- Automatic OpenAlex author-ID resolution without user confirmation (disambiguation always requires a human to pick from `search-author` candidates — too risky to guess automatically given common-name collisions)
- Cross-referencing grant/funding data (GrantScope, 2026-07-14, already covers NIH RePORTER funding landscape scanning)
- Scheduling/automation wrapper (Routine/Skill packaging) — this ships as a CLI tonight; a Routine wrapper is a natural future extension once the user has validated the core tool

## Tech Stack

- **Language:** Python 3
- **Framework:** None — stdlib only (`urllib` for HTTP, `sqlite3` for persistence, `argparse` for CLI)
- **Dependencies:** stdlib only; Anthropic API called directly via `urllib` (optional, no `anthropic` package dependency)
- **Runtime requirement:** `python3 src/main.py <command> ...` — no install step

## Data Structure

SQLite database (`data/impact_ledger.db`), created on first `sync`:

```sql
CREATE TABLE authors (
    author_id TEXT PRIMARY KEY,      -- OpenAlex ID, e.g. "A5023888391"
    display_name TEXT NOT NULL,
    works_count INTEGER NOT NULL,
    cited_by_count INTEGER NOT NULL,
    h_index INTEGER,
    i10_index INTEGER,
    last_synced TEXT NOT NULL         -- UTC date "YYYY-MM-DD"
);

CREATE TABLE work_snapshots (
    work_id TEXT NOT NULL,            -- OpenAlex work ID
    sync_date TEXT NOT NULL,          -- UTC date "YYYY-MM-DD"
    author_id TEXT NOT NULL,
    title TEXT NOT NULL,
    publication_year INTEGER,
    doi TEXT,
    host_venue TEXT,
    cited_by_count INTEGER NOT NULL,
    concepts TEXT,                    -- JSON list of concept display names
    abstract TEXT,                    -- reconstructed from abstract_inverted_index
    PRIMARY KEY (work_id, sync_date)
);
```

OpenAlex responses are JSON over HTTPS, no auth required. Abstracts arrive as an `abstract_inverted_index` (word → list of positions) and are reconstructed into plain text locally.

## Folder Structure

```
builds/2026-08-05-impact-ledger/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── main.py          — CLI entry point (argparse: search-author, sync, history, render)
│   ├── openalex.py       — OpenAlex HTTP client, pagination, abstract reconstruction
│   ├── db.py             — SQLite schema, snapshot upsert, trend/velocity queries
│   ├── ai.py             — optional Claude Haiku call + deterministic fallback templates
│   └── dashboard.py      — self-contained HTML dashboard renderer (escaped/safe DOM)
└── tests/
    ├── test_openalex.py
    ├── test_db.py
    ├── test_ai.py
    ├── test_dashboard.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Abstract reconstruction from `abstract_inverted_index` (normal case, empty case, out-of-order positions)
  - OpenAlex works pagination via cursor (mocked HTTP, multi-page walk terminates correctly)
  - Author search result formatting (mocked HTTP, multiple candidates)
  - Network/HTTP error handling for OpenAlex calls (mocked failure → clear error, no crash)
  - SQLite snapshot upsert: same-day re-sync does not duplicate rows (row count check)
  - SQLite snapshot upsert: later-day sync adds a new distinct-date row per work
  - Citation velocity calculation: increase, no change, and "first sync — no prior snapshot" cases
  - Trend query: returns "insufficient history" signal with 1 distinct sync date, real series with ≥2
  - `history` command output for 0, 1, and 2+ snapshots
  - AI note generation: mocked successful Claude call, mocked failed call (falls back to template), and no-`ANTHROPIC_API_KEY` path (asserts zero network calls attempted)
  - Dashboard HTML escaping: a `<script>` payload in a work title renders as inert text, never executed markup
  - Dashboard renders correctly with zero rising papers (no velocity data yet)
  - Dashboard renders correctly with a full multi-snapshot dataset (chart data present)
  - CLI argument parsing: missing required `--author-id` produces a clear error, not a traceback

## Success Criteria

1. All tests pass (zero failures)
2. `sync` fetches an author's works from OpenAlex (mocked in tests; live in real use) and persists a dated snapshot without duplicating same-day re-syncs
3. `render` produces a self-contained dark-mode HTML dashboard that opens directly in a browser, showing hero stats, a paper table, and a rising-papers panel that gracefully states "not enough history yet" on a first run
4. A malicious payload placed in a work title cannot execute script in the rendered dashboard (verified live in headless Chromium)
5. With no `ANTHROPIC_API_KEY` set, `render --ai` makes zero network calls to Anthropic and still produces complete, non-broken AI-note text via the deterministic fallback

---

## Scope Changes

None — full in-scope feature set was completed as planned.
