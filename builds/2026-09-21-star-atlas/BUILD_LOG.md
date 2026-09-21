# Build Log — Star Atlas

> **Date:** 2026-09-21
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for an interrupted prior session. The most recent open PR branch (`claude/cool-sagan-10kqlj`, PR #104, 2026-09-20 "Counterpoint") has a `BUILD_LOG.md` ending in "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Read `builds/index.md` and `builds/ideas.md` from that same branch (the local `main`/working-branch copies are weeks stale; there are ~100 open, un-merged nightly-build PRs on this repo going back to June — noted here for visibility but out of scope to fix tonight).
- Day of year 264 → category rotation index 2 → Category C — Personal Knowledge Tool.
- Lottery: 7 pending Category C backlog ideas, all unrated (R=0) → 25% lottery chance. Rolled 75 → fresh generation.
- Decided to build: **Star Atlas** — a GitHub-stars knowledge base (realizes backlog idea #56). Full reasoning in `WhyThis.md`.
- Build folder created: `builds/2026-09-21-star-atlas/`

### [00:15 UTC] PRD Written

- Goal: sync the user's real GitHub starred repos into a local, searchable, AI-tagged personal knowledge base.
- Scope: `sync` (GitHub API + SQLite, incremental, deduped), deterministic rule-based tagging always on, optional `--ai` enrichment via Claude Haiku with unconditional fallback, `search`/`list`/`stats`/`render` (dark-mode HTML dashboard).
- Notable constraints: stdlib-only for the GitHub/Anthropic HTTP calls (urllib, no `requests`/`anthropic` package dependency) to keep the runtime dependency-free; every external-API test uses a mock, never a live call.

### [00:20 UTC] Build Phase — Core Modules

- `src/github_client.py`: `fetch_starred(token, since=None)` calls `GET /user/starred` with `Accept: application/vnd.github.star+json`, `sort=created&direction=desc`, paginates via `per_page=100` until an empty page or until every repo on a page is older than or equal to `since` (then trims to only the newer ones). Raises `MissingTokenError` / `GitHubAPIError` (carries status code) so `main.py` can give a clear message instead of a raw traceback.
- `src/store.py`: SQLite schema per PRD. `upsert_repo` uses `INSERT OR REPLACE` keyed on GitHub repo id, so re-ingesting the same repo (e.g. across incremental syncs where the cutoff isn't exact) never duplicates a row. `latest_starred_at(conn)` returns the sync cursor. `search_repos`/`list_repos` build parameterized SQL (never string-interpolated) to avoid injection from search text. `stats(conn)` aggregates counts by tag and language with plain SQL `GROUP BY`.
- `src/tagging.py`: `rule_tag(language, topics, description)` — ordered keyword rules over topics + language + description (AI/ML, Data & Analytics, Dev Tools & CLI, Web & Frontend, Infra & DevOps, Testing & QA, Docs & Reference, Other fallback) plus a deterministic note template. `ai_enrich(repo, api_key, request_fn=...)` builds an Anthropic Messages API request (Haiku model, small `max_tokens`) sending only `full_name`, `description`, `language`, `topics` (all already public on GitHub) and parses a `TAG: ... | NOTE: ...` formatted reply; any exception (network, malformed reply, non-2xx) falls back to `rule_tag`'s output. `request_fn` is injected so tests never perform a real HTTP call.
- `src/report.py`: `render_html(repos, stats)` — embeds repo data as JSON inside a `<script type="application/json">` block with `</script` string-escaped (`.replace("</script", "<\\/script")`), and the page's own JS reads that JSON and builds cards purely via `document.createElement` + `.textContent` (never `.innerHTML`) so a hostile `description` string can never execute as markup. Dark mode via CSS custom properties, mobile-responsive (single-column below 640px), client-side search/filter with no network calls.
- `src/main.py`: argparse with `sync`, `search`, `list`, `stats`, `render` subcommands; `sync` reads `--token` or falls back to the `GITHUB_TOKEN` env var, `--ai` reads `--api-key` or `ANTHROPIC_API_KEY`; `--db` defaults to `star_atlas.db` inside the build folder (via `Path(__file__).resolve().parent.parent`) so it never writes outside the build folder regardless of the caller's CWD.

### [00:45 UTC] Build Phase — Tests & Fixtures

- `sample_data/starred_page.json`: a realistic fixture page of the star API's shape (list of `{starred_at, repo: {...}}` objects), including one repo with a hostile `</script><script>window.__xss=true;</script>` description to drive the XSS-safety test.
- Wrote `tests/test_github_client.py`, `tests/test_store.py`, `tests/test_tagging.py`, `tests/test_report.py`, `tests/test_cli.py` alongside the modules, not after — each test targets one real failure mode (pagination cutoff, dedup on re-sync, SQL injection safety of search input, missing-token error, AI-failure fallback, AI-success parsing, hostile-description escaping, stats aggregation correctness, empty-db behavior, CLI wiring for every subcommand).

### [01:05 UTC] Tests Run

Tests: 49 passed, 0 failed. (`pytest tests/ -v`, using the pre-installed `pytest` binary at `/root/.local/bin/pytest` on this container since the project-local Python has no `pytest` module and `pip install` targets a fresh venv unnecessarily for a stdlib-only build — `requirements.txt` still lists `pytest` for a normal `pip install -r requirements.txt` in the user's own environment.)

### [01:10 UTC] Manual End-to-End Verification

Ran the actual CLI (`src/main.main`) directly against `sample_data/starred_page.json`, outside pytest, via a one-off script that monkeypatches only `github_client.fetch_starred` (no live GitHub call, consistent with this container's egress policy — the parsing/storage/tagging/rendering code underneath is exercised unmodified): `sync` ingested all 5 fixture repos and printed "Total in library: 5"; a second `sync` run printed "Synced 0 repo(s)" confirming the incremental-cutoff logic and dedup both work outside of mocks; `search llm` and `list --tag "AI/ML"` both correctly returned only `acme/llm-agent-toolkit`; `stats` printed correct per-tag (5 tags, 1 each) and per-language (Python:2, TypeScript:1, JavaScript:1, Go:1) counts; `render` wrote a real `dashboard.html` (8322 bytes) and a follow-up substring check confirmed the raw hostile payload `</script><script>window.__xss=true;</script>` from the fixture's `hostile/xss-fixture` repo does not appear anywhere in the output.

### [01:15 UTC] Verify — Step 7

Success criteria review:
1. ✓ 49 tests pass, 0 failures (exceeds the 15 minimum by more than 3x), each tied to a real failure mode.
2. ✓ `sync` against the mocked fixture ingests all repos, is idempotent (`INSERT OR REPLACE` by id, verified by a test asserting row count is unchanged after a second identical sync), and only new repos are added when a second fixture page with one additional, newer-`starred_at` repo is supplied.
3. ✓ Every repo has a non-empty `tag`/`note` from `rule_tag` even with `--ai` unset and no `ANTHROPIC_API_KEY` — asserted directly in `test_tagging.py` and via a full `sync` run with the env var unset in `test_cli.py`.
4. ✓ `render` with the hostile-description fixture never contains the raw unescaped `</script><script>window.__xss=true;</script>` substring in its output — asserted in `test_report.py`.
5. ✓ `search`/`list`/`stats` verified against the known fixture dataset with exact expected counts/results.

Security checklist (STANDARDS.md):
- No `.env` files committed.
- No hardcoded credentials — `GITHUB_TOKEN`/`ANTHROPIC_API_KEY` read only from `os.environ` or explicit CLI flags the user supplies.
- No `eval()`/`exec()`.
- No unescaped injection into the HTML report — data delivered as escaped JSON, rendered via `textContent`/`createElement` only.
- No `subprocess`/`os.system()` calls anywhere in the build.
- SQL is fully parameterized (no string-built queries from search input).
- All files confined to `builds/2026-09-21-star-atlas/`.
- No personal data ever sent to the Anthropic API — only already-public GitHub repo metadata (name/description/language/topics).

### [01:20 UTC] Documentation — Step 8

- `FutureFeatures.md`: 6 concrete suggestions across quick wins, medium effort, and ambitious extensions.
- `Manual.md`: quick start, full command reference, configuration table, troubleshooting.

Build complete. Success criteria reviewed. All tests passing.
