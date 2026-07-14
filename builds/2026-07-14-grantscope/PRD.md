# PRD — GrantScope

> **Build date:** 2026-07-14
> **Category:** F — Data Explorer
> **Complexity:** Ambitious Project
> **Day of week:** Tuesday

---

## Goal

A Python CLI that queries the NIH RePORTER public API for grants funded in the user's own research domain (empathy, psychopathy, stress, forensic neuroscience, affective neuroscience), stores them in a local SQLite library, and renders a searchable, filterable dark-mode HTML dashboard of the funding landscape — trends by year, top funding institutes, top receiving institutions, funding-mechanism breakdown, and an optional AI-generated landscape briefing.

## User Story

As a neuroscience lab director who writes grants and manages research administration, I want to explore who is currently funding work in my specific research domain, at what institutes, through what funding mechanisms, and at what scale, so that I can target grant applications more effectively and spot funding trends and potential collaborators before writing a proposal.

## Scope

### In Scope
- NIH RePORTER API v2 client (`urllib.request`, no third-party HTTP library) that searches funded projects by keyword/topic across a configurable fiscal-year window
- 5 default saved topics seeded directly from PROFILE.md's named research areas: empathy/prosocial neuroscience, psychopathy/antisocial behavior, stress and coping neurobiology, forensic neuroscience and risk assessment, affective neuroscience/emotion
- Local SQLite storage of fetched projects, deduplicated by NIH core project number, with incremental `last_seen` tracking so re-syncing doesn't create duplicates
- Aggregation/analysis layer (stdlib only): funding total and project count by fiscal year per topic, top funding institutes/centers (IC), top receiving organizations, funding-mechanism (activity code, e.g. R01/R21/K01) breakdown, and a lightweight corpus-wide term-frequency concept extractor over abstracts to surface trending keywords per topic
- Optional AI landscape briefing: sends only the aggregated statistics and a small sample of public project titles/abstracts (already public government data) to Claude Haiku for a plain-English "where the funding is heading and what to target" summary; deterministic template fallback when `ANTHROPIC_API_KEY` is unset or the call fails
- Self-contained dark-mode HTML dashboard (Chart.js via pinned CDN URL, degrades to text summary if the CDN is unreachable): funding-by-year line chart, top-institutes bar chart, mechanism-breakdown doughnut chart, per-topic tabs, a searchable/sortable project table, and a briefing panel
- CLI commands: `sync` (fetch/update from API), `build` (render HTML from local DB), `stats` (terminal summary), `search <query>`, `list-topics`, `briefing` (generate/refresh the AI briefing text)
- Graceful handling of network failures, empty result sets, and malformed API responses

### Out of Scope
- Grant application writing or auto-drafting proposal text (this is a landscape/awareness tool, not a proposal generator)
- Non-NIH funding sources (NSF, private foundations) — NIH RePORTER is the only data source used tonight; a multi-source extension is listed in FutureFeatures.md
- Author/PI-level social network graphs (would need a second data source to resolve collaborators reliably)
- Any write access back to NIH RePORTER (read-only API usage throughout)

## Tech Stack

- **Language:** Python 3
- **Framework:** None — stdlib CLI (`argparse`)
- **Dependencies:** stdlib only (`urllib.request`, `sqlite3`, `json`, `argparse`, `re`, `html`, `datetime`, `collections`) for the core tool; the HTML dashboard loads Chart.js from a pinned CDN URL at view time (no Python-side dependency)
- **Runtime requirement:** `python3 src/main.py <command>` — no install step beyond stdlib; generated `output/dashboard.html` opens directly via `file://`

## Data Structure

SQLite database at `output/grantscope.db` (created on first `sync`), one table:

```sql
CREATE TABLE projects (
    project_num TEXT PRIMARY KEY,      -- NIH core project number, e.g. "5R01MH123456-03"
    topic TEXT NOT NULL,               -- which saved topic surfaced this project
    title TEXT NOT NULL,
    abstract TEXT,
    pi_name TEXT,
    org_name TEXT,
    org_city TEXT,
    org_state TEXT,
    ic_admin TEXT,                     -- administering NIH Institute/Center, e.g. "NIMH"
    activity_code TEXT,                -- funding mechanism, e.g. "R01"
    award_amount INTEGER,
    fiscal_year INTEGER,
    project_start TEXT,
    project_end TEXT,
    first_seen TEXT NOT NULL,          -- ISO date this project was first synced
    last_seen TEXT NOT NULL            -- ISO date of the most recent sync that saw it
);
```

`briefings` table stores the most recent AI (or fallback) briefing per topic (`topic TEXT PRIMARY KEY, text TEXT, generated_at TEXT, source TEXT` where `source` is `"ai"` or `"template"`).

All monetary and project data originates from NIH RePORTER, a public U.S. government dataset — no personal or proprietary data is stored.

## Folder Structure

```
builds/2026-07-14-grantscope/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py           # CLI entry point (argparse, command dispatch)
│   ├── api_client.py     # NIH RePORTER API request/response handling
│   ├── db.py             # SQLite schema, insert/dedupe, query helpers
│   ├── analysis.py       # aggregation stats + concept/keyword extraction
│   ├── ai_briefing.py    # Claude Haiku call + deterministic fallback template
│   ├── html_report.py    # renders the self-contained HTML dashboard
│   └── topics.py         # default topic definitions
└── tests/
    ├── __init__.py
    ├── test_api_client.py
    ├── test_db.py
    ├── test_analysis.py
    ├── test_ai_briefing.py
    ├── test_html_report.py
    └── test_main.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - API request payload construction (topic → correct search criteria/fiscal-year window)
  - API response parsing into project records, including missing/null fields
  - HTTP error handling (network failure, non-200 status, malformed JSON) degrades gracefully rather than crashing
  - DB schema creation, insert, and dedupe-by-`project_num` (re-syncing updates `last_seen` without duplicating rows)
  - DB query helpers (by topic, search by keyword)
  - Aggregation: funding-by-year, top-institutes, top-organizations, mechanism breakdown, all against known fixture data with hand-computed expected results
  - Keyword/concept extraction against a small fixture corpus
  - AI briefing: mocked successful Anthropic API call, missing-API-key fallback, API-error fallback — all three paths produce non-empty text
  - HTML report renders expected sections and correctly escapes user-adjacent text (project titles/abstracts) against script-injection content, to guard against XSS from API-sourced text
  - Empty-database edge case for both aggregation and HTML rendering (no crash, sensible empty state)
  - CLI argument parsing / command dispatch for each subcommand

## Success Criteria

1. All tests pass (zero failures)
2. `python3 src/main.py sync` fetches and stores projects from NIH RePORTER for all 5 default topics when network access is available, and fails with a clear, non-crashing error message when it is not
3. `python3 src/main.py build` renders `output/dashboard.html` that opens directly via `file://` and displays funding-by-year, top-institutes, and mechanism-breakdown charts plus a searchable project table, using only locally stored data (works fully offline once synced)
4. Re-running `sync` does not create duplicate project rows
5. The AI briefing path produces a non-empty, readable summary both with a mocked Anthropic API key and with no key set (template fallback)

---

## Scope Changes

None — full in-scope feature set was delivered as planned. See BUILD_LOG.md for any implementation-level decisions.
