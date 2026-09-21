# PRD — Star Atlas

> **Build date:** 2026-09-21
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious Project
> **Day of week:** Monday

---

## Goal

A Python CLI that syncs the user's real GitHub starred repositories into a local, searchable, AI-tagged knowledge base so a chaotic stars list becomes an organized personal reference of tools and projects.

## User Story

As a solo founder and researcher who stars GitHub repos faster than he can categorize or remember why, I want to turn my GitHub stars into a searchable, tagged personal library with a note on what each repo is for, so that I can actually find and reuse the tools I've already discovered instead of re-discovering them or forgetting they exist.

## Scope

### In Scope
- `sync` command: fetch the authenticated user's starred repos via the GitHub REST API (`GET /user/starred`, `Accept: application/vnd.github.star+json` for `starred_at` timestamps), paginated, sorted newest-first
- Incremental sync: skip repos already ingested (dedup by GitHub repo id), so re-running `sync` is fast and idempotent
- Local SQLite storage (`star_atlas.db` inside the build folder by default, `--db` override) — full_name, description, html_url, language, topics, stargazers_count, starred_at, deterministic tag, AI note, ingested_at
- Deterministic rule-based tagging (language + topics keyword rules) applied to every repo on ingest — works with zero configuration and zero network calls beyond GitHub
- Optional `--ai` flag on `sync`: sends only already-public repo metadata (name, description, language, topics — never any of the user's personal data) to the Claude API (Haiku model) for a refined category tag and a one-sentence "why this might be useful to you" note; unconditional fallback to the deterministic rule-based tag/note on any API error or missing `ANTHROPIC_API_KEY`, with zero network calls to Anthropic when the flag is absent
- `search QUERY` — full-text search across name/description/topics, optional `--tag` and `--language` filters
- `list` — browse all repos, optional `--tag`/`--language` filters, sorted by starred date
- `stats` — counts by tag and by language, total repo count, sync recency
- `render` — self-contained dark-mode HTML dashboard: tag/language filter chips, live client-side search, per-repo cards linking to GitHub, all data delivered as JSON-in-`<script>` (escaped against premature tag termination) and rendered via `textContent`/`createElement` only, never `innerHTML`, so a malicious repo description can never execute as markup
- `--open` flag on `render` to open the dashboard in the default browser

### Out of Scope
- Un-starring or otherwise writing back to GitHub (read-only tool)
- Organizations' starred repos (personal account stars only)
- Any OAuth flow — relies on a `GITHUB_TOKEN`/`--token` personal access token the user already has (same pattern as the existing GitHub Repository Health Scorecard build)
- Real-time/webhook-driven sync — this is a pull tool the user runs on demand or schedules themselves

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None
- **Dependencies:** stdlib only (`urllib`, `sqlite3`, `argparse`, `json`, `webbrowser`) — no third-party packages required to run; `pytest` for tests
- **Runtime requirement:** `python3 -m src.main sync --token $GITHUB_TOKEN`, then `search`/`list`/`stats`/`render` — no install step beyond Python itself

## Data Structure

SQLite table `repos`:

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | GitHub repo id |
| `full_name` | TEXT | `owner/repo` |
| `description` | TEXT | nullable |
| `html_url` | TEXT | |
| `language` | TEXT | nullable |
| `topics_json` | TEXT | JSON array of GitHub topic strings |
| `stargazers_count` | INTEGER | |
| `starred_at` | TEXT | ISO 8601, from the star API |
| `tag` | TEXT | rule-based or AI-refined category |
| `note` | TEXT | rule-based or AI "why useful" sentence |
| `source` | TEXT | `"rule"` or `"ai"` — which path produced `tag`/`note` |
| `ingested_at` | TEXT | ISO 8601, local sync time |

Sync cursor: the max `starred_at` already stored, used to stop paginating once GitHub returns repos older than the last sync (GitHub's `/user/starred` with `sort=created&direction=desc` is stable for this).

## Folder Structure

```
builds/2026-09-21-star-atlas/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py            (argparse CLI: sync/search/list/stats/render)
│   ├── github_client.py   (GitHub starred-repos API client, pagination, errors)
│   ├── store.py           (SQLite schema, upsert, query, stats)
│   ├── tagging.py         (deterministic rules + optional AI enrichment)
│   └── report.py          (HTML dashboard rendering, JSON escaping)
├── sample_data/
│   └── starred_page.json  (fixture GitHub API response used by tests)
└── tests/
    ├── test_github_client.py
    ├── test_store.py
    ├── test_tagging.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - GitHub client: pagination stops correctly, incremental cutoff by `starred_at`, missing-token error, HTTP error handling (401/403/network) — all via a mocked `urlopen`, never a live call
  - SQLite store: insert, upsert/dedup by id, search filters (query/tag/language), stats aggregation, empty-database behavior
  - Deterministic tagging: each rule (AI/ML, dev tools, data, web, infra, testing, docs, other/fallback) produces the expected tag on representative fixtures
  - AI enrichment: mocked Anthropic client success path, mocked failure path falls back to the deterministic tag/note, and a no-API-key path makes zero network calls
  - HTML report: valid JSON embedding with `</script` escaped, a hostile repo description (`</script><script>...`) never executes/renders as markup in the generated string, dashboard includes expected repo data
  - CLI: `sync`, `search`, `list`, `stats`, `render` argument parsing and end-to-end wiring using a temp SQLite DB

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests, each tied to a real failure mode
2. `sync` against a mocked GitHub API response correctly ingests all repos, is idempotent on a second run (no duplicate rows), and correctly resumes only new stars on a third run with new fixture data
3. Every ingested repo has a non-empty `tag` and `note` even with zero `ANTHROPIC_API_KEY` and no `--ai` flag (deterministic fallback always available)
4. `render` produces a self-contained HTML file with zero unescaped injection from a hostile repo description, verified by a test asserting the raw hostile string never appears unescaped in the output
5. `search`/`list`/`stats` return correct, verifiable results against a known fixture dataset

---

## Scope Changes

None — full scope as specified above was completed as designed.
