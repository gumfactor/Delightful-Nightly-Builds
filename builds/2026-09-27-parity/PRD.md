# PRD — Parity

> **Build date:** 2026-09-27
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious Project
> **Day of week:** Sunday

---

## Goal

Parity cross-references live Teamwork.com tasks against a live Coda tracking table to surface exactly which items exist in one system but not the other, which matched items disagree on done/open status, and whether that gap is growing or shrinking over successive syncs.

## User Story

As a solo founder and lab director who plans work in Coda and executes it in Teamwork.com across several simultaneous projects (a research lab, The Canada List, Kwyeter), I want a single command that tells me what's tracked in one tool but missing from the other, so that nothing agreed-upon in planning silently fails to become a real task (or vice versa) without me manually re-reading both tools side by side.

## Scope

### In Scope
- A `TeamworkClient` that authenticates with a Teamwork.com API token (HTTP Basic auth, token as username) and paginates through open (non-completed) tasks for one or more configured project IDs, normalizing each into `{id, title, completed, due_date, project_id, url}`.
- A `CodaClient` that authenticates with a Coda API token (Bearer auth) and paginates through rows of one configured table in one configured doc, normalizing each into `{id, title, status_text, is_done, url}` using a configurable "title column" and "status column" plus a configurable list of status values that count as done (case-insensitive).
- A pure, dependency-free matcher (`matcher.py`) that:
  - Normalizes titles (casefold, strip punctuation, collapse whitespace) into token sets.
  - Computes Jaccard similarity between every unmatched Teamwork/Coda title pair.
  - Greedily assigns the highest-similarity pairs first, above a configurable threshold (default 0.5), each item matched at most once.
  - Classifies every item into exactly one bucket: `matched_ok` (matched, statuses agree), `status_conflict` (matched, statuses disagree — records which side says done), `teamwork_only` (no Coda match — planned nowhere, or already closed out on the Coda side), `coda_only` (no Teamwork match — planned but never turned into an executable task).
- Local SQLite persistence (`parity.db`, created inside the build folder) storing one row per historical sync run (timestamp, counts per bucket) so drift over time can be charted, plus the latest run's full item-level results for the dashboard.
- CLI (`src/main.py`) with subcommands:
  - `parity sync --config config.json` — fetches both sources live, runs the matcher, persists the run.
  - `parity sync --config config.json --demo` — runs the exact same pipeline against bundled fixture data (no network calls) so the tool is inspectable without live credentials.
  - `parity history` — prints a table of past sync runs and their bucket counts.
  - `parity render --out dashboard.html` — renders the self-contained dashboard from the latest persisted run.
  - `parity briefing` — optional one-paragraph Claude Haiku summary built strictly from aggregate bucket counts (never item titles); deterministic template fallback with zero network calls when `ANTHROPIC_API_KEY` is unset.
- Self-contained dark-mode HTML dashboard: hero stats (matched / conflicts / Teamwork-only / Coda-only), a native Canvas 2D line chart of gap size (Teamwork-only + Coda-only + conflicts) across historical syncs, and sortable/searchable tables for each non-`matched_ok` bucket. All dynamic data delivered as an escaped JSON payload and rendered via `textContent`/DOM APIs, never `innerHTML`.
- `config.example.json` documenting the required configuration shape (project IDs, doc/table IDs, column names, done-status values) with no real values.

### Out of Scope
- Any write-back to Teamwork or Coda (creating, closing, or editing tasks/rows). Parity is strictly read-only against both systems.
- OAuth flows — a plain API token via environment variable is sufficient for a single-user personal tool.
- Multi-user / multi-account support.
- Real-time/webhook-driven sync — this is an on-demand CLI, run manually or on a schedule the user sets up themselves (see FutureFeatures.md for a Routine wrapper).
- Fuzzy matching beyond token-set Jaccard similarity (e.g. embeddings/semantic matching) — out of scope for tonight's session; documented as a future enhancement.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`urllib.request` for HTTP, `sqlite3` for persistence, `json`, `argparse`, `re`, `datetime`) — Chart rendering uses hand-written Canvas 2D JavaScript in the generated HTML, no CDN dependency, no chart library.
- **Runtime requirement:** `python3 src/main.py <subcommand> ...` — no install step. Real API calls require `TEAMWORK_API_KEY`, `TEAMWORK_DOMAIN`, and `CODA_API_KEY` environment variables (never hardcoded); `--demo` mode works with zero credentials.

## Data Structure

**`config.json`** (user-supplied, not committed with real values — see `config.example.json`):
```json
{
  "teamwork": { "project_ids": [123456, 789012] },
  "coda": {
    "doc_id": "AbCdEfGhIj",
    "table_id": "grid-xxxxxxxx",
    "title_column": "Name",
    "status_column": "Status",
    "done_values": ["Done", "Complete", "Closed"]
  },
  "match_threshold": 0.5
}
```

**`parity.db`** (SQLite, created at first `sync`):
```sql
CREATE TABLE sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,            -- ISO 8601 UTC
    matched_ok INTEGER NOT NULL,
    status_conflict INTEGER NOT NULL,
    teamwork_only INTEGER NOT NULL,
    coda_only INTEGER NOT NULL
);

CREATE TABLE sync_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES sync_runs(id),
    bucket TEXT NOT NULL,             -- matched_ok | status_conflict | teamwork_only | coda_only
    teamwork_title TEXT,
    teamwork_url TEXT,
    coda_title TEXT,
    coda_url TEXT,
    detail TEXT                       -- e.g. "done in Teamwork, open in Coda"
);
```

Only the latest run's `sync_items` are rendered in full on the dashboard; `sync_runs` accumulates indefinitely to drive the drift-over-time chart.

## Folder Structure

```
builds/2026-09-27-parity/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── config.example.json
├── .gitignore
├── src/
│   ├── main.py
│   ├── teamwork_client.py
│   ├── coda_client.py
│   ├── matcher.py
│   ├── store.py
│   ├── dashboard.py
│   └── briefing.py
└── tests/
    ├── test_matcher.py
    ├── test_teamwork_client.py
    ├── test_coda_client.py
    ├── test_store.py
    ├── test_dashboard.py
    ├── test_briefing.py
    ├── test_cli.py
    └── fixtures/
        ├── teamwork_tasks.json
        └── coda_rows.json
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Matcher: identical titles match; near-identical titles (punctuation/case differences) match above threshold; unrelated titles stay unmatched; below-threshold similarity is rejected; a matched pair with agreeing done-status is `matched_ok`; a matched pair with disagreeing status is `status_conflict` (both directions); unmatched Teamwork items become `teamwork_only`; unmatched Coda items become `coda_only`; every item is matched at most once even when multiple candidates exceed threshold (greedy uniqueness); empty input on either side is handled without error.
  - Teamwork client: pagination stops correctly at a partial page; completed tasks are excluded; HTTP errors surface as a typed exception rather than crashing; all HTTP calls are mocked (no live network access in tests).
  - Coda client: row values are extracted correctly by configured column name; missing/blank status values are treated as not-done; pagination via `nextPageToken` is followed until exhausted; all HTTP calls are mocked.
  - Store: a sync run and its items persist and round-trip correctly; `history` returns runs in chronological order; a fresh (nonexistent) database file initializes its schema on first use.
  - Dashboard: rendered HTML contains no unescaped item titles when a title includes `</script><script>` (XSS regression test) and the JSON payload round-trips exactly.
  - Briefing: with no `ANTHROPIC_API_KEY` set, produces a deterministic template string and makes zero network calls (verified via mock assert-not-called); with a key set, the Anthropic HTTP call is mocked and only aggregate counts appear in the constructed request body, never any item title.
  - CLI: `--demo sync` runs end-to-end against bundled fixtures with no network access and exits 0; `render` produces a file; missing config file produces a clear non-crashing error.

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests.
2. `python src/main.py sync --config config.example.json --demo` runs the full pipeline against bundled fixtures with zero network calls and correctly classifies every fixture item into the right bucket (hand-verified against the fixture data before being asserted in tests).
3. `python src/main.py render --out dashboard.html` produces a single self-contained HTML file that opens directly in a browser with no console errors, shows correct hero-stat counts, and renders a title containing a script-injection payload as inert text (manually verified in headless Chromium).
4. Running `sync` twice against the same fixtures and then `history` shows two persisted runs with correct per-bucket counts, proving drift tracking works across repeated syncs.
5. Live Teamwork/Coda calls are fully isolated behind `TeamworkClient`/`CodaClient` and never invoked in the test suite — confirmed by grep for any un-mocked `urlopen` in `tests/`.

---

## Scope Changes

None — full scope as planned above shipped tonight.
