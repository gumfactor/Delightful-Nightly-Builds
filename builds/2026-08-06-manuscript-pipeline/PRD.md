# PRD — Manuscript Pipeline

> **Build date:** 2026-08-06
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project

---

## Goal

Track an academic researcher's own manuscripts through the submission → review → revision → publication pipeline, and automatically detect when a manuscript quietly goes live rather than relying on the researcher to remember to check.

## User Story

As an Associate Professor who writes and submits grants and manuscripts across multiple concurrent projects, I want one durable record of every manuscript's current stage, how long it's been there, and any upcoming revision deadline, so that nothing sits forgotten in an inbox and I find out the moment a paper is actually published, not weeks later.

## Scope

### In Scope
- `add` — register a manuscript: title, authors (comma-separated, first-listed treated as corresponding unless flagged), target journal, submission date, manuscript type (original-research / review / commentary / other), optional expected-review-days override (default 90).
- `list` — show all manuscripts with current stage, days-in-stage, and an at-risk flag (submitted/under_review past its expected-review-days, or a revision past its deadline).
- `update` — manually set status (`submitted`, `under_review`, `revise_resubmit`, `accepted`, `rejected`, `published`, `withdrawn`), with an optional note and, for `revise_resubmit`, a revision deadline date. Every update appends to a permanent status-history log; it never overwrites prior history.
- `capture` — paste (via stdin or `--text`) an unstructured decision/confirmation email; extract journal, decision type, and (for revise & resubmit) the deadline date. Deterministic regex/keyword parser always runs; if `ANTHROPIC_API_KEY` is set, an optional Claude Haiku pass re-extracts the same fields and is preferred when it returns valid, well-formed data, with the deterministic result as the fallback on any error, missing key, or malformed AI response.
- `sync` — for every manuscript not already `published`/`rejected`/`withdrawn`, query the free, no-auth Crossref API (`api.crossref.org/works`) by title + first author surname; if a returned work's title token-overlap ratio is ≥ 0.72 **and** at least one author surname matches, auto-transition the manuscript to `published` and record the discovered DOI, container-title, and publication date in the status log.
- `report` — render a terminal summary and a self-contained dark-mode HTML dashboard (`report.html`) with: a pipeline funnel (counts per stage), an at-risk list, a full manuscript table (sortable/searchable client-side, no external JS dependency required to function — Chart.js used for the funnel chart only, with a DOM-table fallback if unreachable), and per-manuscript status history.
- Local SQLite persistence (`manuscripts.db`), created on first run, living inside the build folder.

### Out of Scope
- OAuth/email-inbox integration to fetch decision emails automatically (paste-based `capture` only).
- Any paid or credentialed API — only Crossref (free, no-auth) and the optional user-supplied `ANTHROPIC_API_KEY`.
- Per-journal historical review-time modeling (a flat configurable default is used instead — see Data Structure).
- Grant tracking or reviewer-response-letter drafting (separate ideas logged to `builds/ideas.md`).

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `urllib`, `argparse`, `re`, `json`, `html`, `datetime`, `difflib`). No third-party packages required at runtime. `pytest` for the dev/test environment only.
- **Runtime requirement:** `python3 src/main.py <command> ...` from the build folder; no install step.

## Data Structure

SQLite database `manuscripts.db` (created at runtime, not committed):

```sql
CREATE TABLE manuscripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,          -- comma-separated, first = corresponding
    journal TEXT NOT NULL,
    manuscript_type TEXT NOT NULL,  -- original-research | review | commentary | other
    submitted_date TEXT NOT NULL,   -- ISO YYYY-MM-DD
    expected_review_days INTEGER NOT NULL DEFAULT 90,
    status TEXT NOT NULL,           -- submitted | under_review | revise_resubmit | accepted | rejected | published | withdrawn
    revision_deadline TEXT,         -- ISO YYYY-MM-DD, nullable
    doi TEXT,                       -- nullable, set once published
    published_date TEXT,            -- nullable
    created_at TEXT NOT NULL
);

CREATE TABLE status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manuscript_id INTEGER NOT NULL REFERENCES manuscripts(id),
    status TEXT NOT NULL,
    note TEXT,
    source TEXT NOT NULL,           -- manual | capture-ai | capture-fallback | sync
    logged_at TEXT NOT NULL
);
```

`status_log` is append-only — a manuscript's full history is always reconstructable.

## Folder Structure

```
builds/2026-08-06-manuscript-pipeline/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py          (CLI entry point / argparse wiring)
│   ├── db.py             (schema + CRUD)
│   ├── parsing.py        (decision-email extraction: deterministic + optional AI)
│   ├── crossref.py        (Crossref client + title/author match scoring)
│   └── render.py         (terminal report + HTML dashboard)
└── tests/
    ├── test_db.py
    ├── test_parsing.py
    ├── test_crossref.py
    └── test_render.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (run from the build folder, using a temp SQLite file/dir per test — never the real `manuscripts.db`)
- **What will be tested:**
  - `db.py`: create manuscript, list, get-by-id, update status (appends to log, does not delete prior entries), days-in-stage computation (including a leap-year boundary), at-risk flag correctness at/just-under/just-over the threshold.
  - `parsing.py`: deterministic parser correctly extracts journal/decision/deadline from 3 hand-written sample emails (accept, reject, revise & resubmit with a date); an ambiguous/malformed email degrades to a partial-but-non-crashing result; the optional AI path is tested with the Anthropic HTTP call fully mocked — verifying (a) zero network calls when no API key is set, (b) correct parsing of a mocked well-formed AI response, and (c) fallback to the deterministic result when the mocked AI response is malformed JSON.
  - `crossref.py`: the HTTP call is mocked in every test — verifying correct query construction, title/author match-scoring at and around the 0.72 threshold (true positive, true negative, near-miss), and that a manuscript already `published` is skipped (never queried).
  - `render.py`: terminal report contains expected stage counts; HTML output correctly escapes a manuscript title containing `<script>` and `<img onerror>` payloads (asserted as literal escaped text, not raw tags, in the generated string); funnel counts in the HTML match the underlying data; the CDN-blocked fallback path renders a table instead of erroring.
  - CLI-level: invalid status value rejected with a clear error; `update` on a nonexistent manuscript id fails gracefully instead of crashing; `capture` with empty input degrades to "unknown" fields rather than raising.

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests.
2. `add` → `list` → `update` → `capture` → `sync` → `report` all function correctly end-to-end against a real (temp) SQLite database, verified manually in addition to pytest.
3. `sync` never calls the network for a manuscript already in a terminal state (`published`/`rejected`/`withdrawn`), and the Crossref match logic correctly distinguishes a true match from a similarly-titled unrelated paper in at least one test case each.
4. The HTML report renders correctly with zero unescaped user-controlled HTML — verified against at least two injection payloads.
5. No network call to the Anthropic API is ever made when `ANTHROPIC_API_KEY` is unset — verified by a test that asserts the mock/patch target was never invoked.

---

## Scope Changes

None — full in-scope feature set as planned above was delivered.
