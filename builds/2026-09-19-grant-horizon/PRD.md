# PRD — Grant Horizon

> **Build date:** 2026-09-19
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious
> **Day of week:** Saturday

---

## Goal

A Python CLI that syncs live NIH RePORTER funding-award data for a configurable set of research topics into local SQLite, then renders a self-contained dark-mode HTML dashboard showing funding trends, top-funded institutions, and agency mix — a competitive-intelligence tool for grant writing.

## User Story

As a mid-career neuroscience researcher who names "grant writing" as a recurring manual friction point and ranks "Academic research" among the domains where a personal tool would add the most value, I want to see the real, current federal funding landscape for my specific research subfields (psychopathy, affective neuroscience, stress/cortisol, forensic neuroscience) in one place, so that I can write a stronger "gap in the literature/funding" argument and identify comparable funded projects and institutions before submitting a grant, without manually searching NIH RePORTER's web UI topic by topic.

## Scope

### In Scope
- `sync` command: for each configured topic and fiscal year in range, calls NIH RePORTER's public `v2/projects/search` REST API (no auth required) via `urllib.request`, normalizes each result into a `Project` record, and upserts into local SQLite deduplicated by `(topic, project_num)`
- Configurable topic list and fiscal-year range via `config.json` in the build folder (default: 5 topics drawn from PROFILE.md's named research areas — psychopathy, affective neuroscience, empathy neuroscience, stress cortisol, forensic neuroscience — and the last 6 fiscal years through the current year)
- Deterministic aggregation layer (pure functions, fully unit-tested, no network): funding-by-fiscal-year per topic, year-over-year growth, top-funded institutions, top PIs by total award amount, agency/IC funding mix
- `report` command renders three outputs from the local SQLite data: a terminal summary, a `flagged_projects.csv`-style full project export (`projects_export.csv`), and a self-contained dark-mode HTML dashboard
- Dashboard: hero stats (total tracked funding, total projects, topic count, fiscal-year range), a per-topic Chart.js multi-line funding-over-time chart with a sortable DOM-table fallback if the CDN is blocked, a top-institutions bar chart, an agency/IC breakdown, and a live search/filter/sort project table
- Optional `--ai` flag: one Claude Haiku-written "funding landscape briefing" paragraph per topic, built strictly from that topic's own computed aggregates and project titles (fiscal-year totals, top institution, project count) — PI names are deliberately excluded from the AI prompt entirely (a stronger privacy bar than sending redacted data, since the field simply never reaches the request). Direct `urllib.request` call to the Anthropic API (no SDK), with an unconditional deterministic-template fallback that produces a complete briefing with zero network calls when `ANTHROPIC_API_KEY` is unset or the call fails
- All user-controlled and API-sourced strings (project titles, institution names, PI names) are HTML-escaped before embedding in the dashboard; chart data is embedded as an escaped `<script type="application/json">` block with `</script>` sequences neutralized, never string-built into executable JS
- Topic names are slugified through an `[a-z0-9-]` allowlist before being used as SQLite lookup keys or HTML element IDs, verified against path-traversal-shaped input

### Out of Scope
- No write access to NIH RePORTER (read-only public search API)
- No CIHR/NSERC/SSHRC Canadian funding-agency data — none of the three publish a comparable free, documented, machine-readable award-search API; a future build could scope this in if/when one becomes available
- No per-grant PDF/notice-of-award parsing — RePORTER's structured project-search fields only
- No automatic weekly re-sync scheduling in this build (a Routine wrapper is a natural FutureFeatures extension, not required for tonight's core value)

## Tech Stack

- **Language:** Python 3.11+ (core tool); Node.js 22 + `@playwright/test` 1.56.1 (browser regression suite for the rendered dashboard's JS only — dev dependency, not part of the shipped tool)
- **Framework:** None (stdlib `urllib.request` for HTTP, `sqlite3` for storage)
- **Dependencies:** stdlib only for the core tool; `pytest` for Python tests (dev-only, in `requirements.txt`); `@playwright/test` for the browser suite (dev-only, in `package.json`, run against the pre-installed Chromium — see Testing Strategy)
- **Runtime requirement:** `python3 src/main.py sync` then `python3 src/main.py report`, or `python3 src/main.py report --ai` with `ANTHROPIC_API_KEY` exported; opens `output/dashboard.html` directly in a browser afterward, no server needed

## Data Structure

**`config.json`** (build folder root):
```json
{
  "topics": ["psychopathy", "affective neuroscience", "empathy neuroscience", "stress cortisol", "forensic neuroscience"],
  "fiscal_year_start": 2020,
  "fiscal_year_end": 2026
}
```

**SQLite (`output/grant_horizon.db`)** — single table `projects`:
| Column | Type | Notes |
|---|---|---|
| topic | TEXT | search topic this record was fetched under |
| project_num | TEXT | RePORTER project number |
| core_project_num | TEXT | stable cross-year project identifier |
| title | TEXT | |
| fiscal_year | INTEGER | |
| award_amount | REAL | |
| org_name | TEXT | |
| org_city | TEXT | |
| org_state | TEXT | |
| org_country | TEXT | |
| pi_names | TEXT | JSON-encoded list |
| agency_ic | TEXT | e.g. "NIMH" |
| start_date | TEXT | ISO date or null |
| end_date | TEXT | ISO date or null |
| first_seen | TEXT | ISO timestamp, set once |
| last_synced | TEXT | ISO timestamp, updated every sync |

Primary key: `(topic, project_num)`. Re-running `sync` upserts (`INSERT ... ON CONFLICT DO UPDATE`), never duplicates.

**NIH RePORTER API assumption:** the exact v2 response schema is written from documented public API knowledge, not live-verified — this build container's egress proxy blocks the live host (confirmed via a denied direct connectivity check tonight), the same constraint prior builds (Dominion Index, Preprint Pulse) hit against Wikidata/arXiv. The HTTP layer is isolated behind `fetch_all_projects(topic, fiscal_years, http_post, page_size)` (in `src/reporter_client.py`), which paginates and takes an injectable `http_post` transport — RePORTER's `v2/projects/search` endpoint is a POST with a JSON search-criteria body, not a GET, so every call site posts a body rather than encoding query parameters. Every other layer (normalization, aggregation, rendering) is tested against realistic fixture JSON shaped to the documented schema, and the real transport (`default_http_post`) is exercised only by the user at runtime.

## Folder Structure

```
builds/2026-09-19-grant-horizon/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── config.json
├── requirements.txt
├── package.json             (devDependency: @playwright/test, for tests/dashboard.spec.js only)
├── package-lock.json
├── playwright.config.js
├── src/
│   ├── main.py              (CLI entry point: sync / report subcommands)
│   ├── reporter_client.py   (NIH RePORTER HTTP client + pagination + normalization)
│   ├── storage.py           (SQLite schema + upsert + query helpers)
│   ├── aggregate.py         (pure aggregation functions: funding_by_year, top_institutions, top_pis, agency_breakdown, yoy_growth)
│   ├── briefing.py          (AI briefing prompt builder + Anthropic call + deterministic fallback)
│   ├── render.py            (HTML dashboard renderer + CSV export + escaping helpers)
│   └── slug.py              (topic slugification / allowlist sanitizer)
├── tests/
│   ├── conftest.py           (adds src/ to sys.path for test imports)
│   ├── test_reporter_client.py
│   ├── test_storage.py
│   ├── test_aggregate.py
│   ├── test_briefing.py
│   ├── test_render.py
│   ├── test_slug.py
│   ├── test_main.py
│   ├── build_fixtures.py     (regenerates tests/fixtures/*.html from the real render.py before every Playwright run)
│   ├── global-setup.js       (Playwright globalSetup: shells out to build_fixtures.py)
│   ├── dashboard.spec.js     (Playwright: hero stats, CDN-blocked fallback, search, click+keyboard sort, hostile-payload XSS safety, mobile viewport)
│   └── fixtures/             (generated, gitignored -- dashboard_normal.html, dashboard_hostile.html)
└── sample_output/
    ├── README.md            (explains the sample was generated from a synthetic fixture, not a live sync, and why)
    ├── dashboard.html       (rendered from the synthetic fixture, so the user can see the real output before running a live sync)
    ├── projects_export.csv  (CSV export of the same synthetic fixture)
    └── grant_horizon_sample.db  (the synthetic fixture's SQLite database, for inspection)
```

## Testing Strategy

- **Frameworks:** pytest (core logic) + `@playwright/test` (the rendered dashboard's actual browser behavior)
- **Test file location:** `tests/test_*.py` (pytest); `tests/dashboard.spec.js` (Playwright)
- **Run commands:** `python -m pytest tests/ -v`; `npx playwright test` (installs its own `node_modules` via `npm install` first — see Manual.md)
- **What will be tested:**
  - RePORTER client: pagination stops when a page returns fewer than the page size; normalization of a full record; normalization with missing/null optional fields (defensive defaults, no crash); malformed-JSON and non-200 HTTP responses raise a typed `ReporterAPIError` instead of crashing
  - Storage: upsert dedupes on `(topic, project_num)` across two syncs with changed award data (second sync's value wins, no duplicate row); querying by topic returns only that topic's rows; `filtered_projects` restricts to the requested topics + fiscal-year range even when the database holds broader prior-sync data; `reconcile_topic` deletes rows no longer returned by the latest sync for that topic/fiscal-year range, without touching other topics or other fiscal years
  - Aggregation: `funding_by_year` totals and counts against a hand-computed fixture; `year_over_year_growth` correct percentage change and `None` for the first year in range; `top_institutions` ranking and tie-breaking; `top_pis` ranking; `agency_breakdown` totals; `dedupe_by_project` collapses an award matched by multiple topics into one row for cross-topic totals
  - Briefing: deterministic fallback produces a complete, non-empty briefing referencing only computed aggregate numbers with zero network calls when `ANTHROPIC_API_KEY` is unset (`urllib.request.urlopen` monkey-patched to raise if invoked); a mocked successful Anthropic response is threaded into the briefing text; the constructed prompt string never contains any PI name from the fixture data (privacy-by-construction check)
  - Browser (Playwright): hero stats match the fixture exactly; the Chart.js CDN-blocked fallback renders its DOM tables (exercised against this environment's real, genuinely-blocked CDN, not a simulation); the search box filters rows; clicking a sortable column header sorts and updates `aria-sort`; the same sort is reachable by keyboard alone (Tab to focus, Enter/Space to activate); zero horizontal overflow at a 375px viewport; a dedicated hostile-payload fixture (script/img-onerror injected into a title, institution, PI name, and AI briefing simultaneously) produces zero dialogs, zero page errors, zero injected globals, and exactly the page's own 3 `<script>` tags
  - Rendering: HTML output HTML-escapes a hostile fixture title (`</script><script>window.__xss=true;</script>`) and a hostile institution name (`<img src=x onerror=...>`), confirmed the raw hostile strings do not appear unescaped and the page's own `<script>` tag count matches expectation; CSV export contains the expected header and correctly quotes a title containing a comma; dashboard hero stats reflect the fixture's true totals
  - Slug: topic slugification collapses whitespace/punctuation into a safe `[a-z0-9-]` id, and a path-traversal-shaped topic (`"../../etc/passwd"`) never produces a slug containing `/` or `..`
  - CLI: argument parsing for `sync`/`report`/`--ai`/`--topics` produces the expected parsed config; an invalid fiscal-year range (`start > end`) raises a clear `ValueError` rather than silently returning no data

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. `sync` normalizes and upserts fixture-shaped RePORTER records into SQLite with correct deduplication on re-run (verified by test, and by a live CLI run against a mocked transport)
3. `report` produces a `dashboard.html` whose hero stats, per-topic funding totals, and top-institution ranking exactly match a hand-computed fixture — verified end-to-end, not just via unit tests of the aggregation functions in isolation
4. The dashboard is safe against a hostile project title/institution name (XSS-shaped strings render as inert text, never executable)
5. `report --ai` with no `ANTHROPIC_API_KEY` set makes zero network calls and still produces a complete, readable briefing via the deterministic fallback

---

## Scope Changes

None — full in-scope list above was delivered as planned.
