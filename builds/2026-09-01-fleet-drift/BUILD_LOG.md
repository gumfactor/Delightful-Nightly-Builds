# Build Log — Fleet Drift

### [Step 0] Incomplete build check
- Local `main` only carries builds through 2026-06-18 (every nightly build since then lives on its own never-merged PR branch — confirmed 85 open PRs, newest is #85 `build(2026-08-30): Layer Guard`).
- Fetched `origin/claude/cool-sagan-tbm8u0` (branch for PR #85, the most recent build) and checked its `BUILD_LOG.md`: final line reads `Build complete. Success criteria reviewed. All tests passing.` — no incomplete build to resume.
- Today's UTC date (2026-09-01) differs from the last build date (2026-08-30), so proceeding with a new build.

### [Step 1] Orient
- Read `PROFILE.md`, `STANDARDS.md`.
- Synced `builds/index.md` and `builds/ideas.md` from `origin/claude/cool-sagan-tbm8u0` (the most recent open PR branch) rather than the stale local copy — 113 rows in the Full Catalog, 78 builds total per Stats block (36 backlog ideas).

### [Step 2] Decide
- Day of year (UTC 2026-09-01) = 244. `category_index = (244-1) % 9 = 0` → **Category A — Dashboard/Visualizer**.
- Category A pending backlog rows: #3 (Lab Research Project Tracker, rating 4), #6 (Open-Meteo Activity Planner, unrated), #26 (Research Pulse, unrated), #27 (Canada List Business Density Dashboard, unrated). R = 1 rated row → `lottery_chance = min(75, 25 + 1*2) = 27%`.
- Rolled 1–100: **58** → missed the 27% gate → fresh idea generation (Step 2d).
- Topic diversity check (last 10 builds, 2026-08-19 → 2026-08-30): investment/finance appeared twice (Trading Book, EDGAR Lens) — not saturated (>2 threshold), but avoided a third to keep diversity. GitHub-backed tooling is otherwise the dominant repeat pattern across the full catalog (7+ builds), so a fresh GitHub-sourced idea needed a genuinely new analytical angle, not a repeat of repo-health/commit-activity/CI-performance shapes already built.
- Considered 3 fresh Category A ideas (full reasoning in `WhyThis.md`): (1) **Fleet Drift** — cross-repo dependency version drift dashboard, (2) a research-software reproducibility scorecard, (3) a Wikidata SPARQL aggregate dashboard for Canada List industry composition. Selected (1) — see `WhyThis.md` for the full comparison.
- The two non-winning ideas were appended to `builds/ideas.md` as new pending rows (#37, #38).

### [09:xx UTC] PRD written
- `PRD.md` complete — goal, user story, scope in/out, tech stack, data structure, folder structure, testing strategy, 5 success criteria.

### [Build] Implementation
- `src/gh_client.py` — GitHub REST API client (list owned repos, fetch file contents from default branch), stdlib `urllib` only, injectable opener for testing.
- `src/req_parser.py` — `requirements.txt` parser (handles comments, blank lines, extras like `pkg[extra]==1.0`, environment markers, `-r`/`-e`/VCS lines skipped as unparseable-but-not-fatal).
- `src/pkg_parser.py` — `package.json` dependency parser (`dependencies` + `devDependencies`, strips `^`/`~`/`>=` range prefixes to a base pinned version, records whether the spec was an exact pin or a range).
- `src/semver.py` — from-scratch semver tuple parser + comparator + classifier (patch/minor/major/none), independent of any third-party package.
- `src/registry.py` — PyPI JSON API + npm registry API clients (latest version lookup), stdlib `urllib` only, injectable opener.
- `src/store.py` — SQLite snapshot persistence, same-day upsert dedup (repo, ecosystem, dependency, date).
- `src/drift.py` — cross-repo drift computation (groups snapshots by dependency, flags divergent pinned versions, severity from `semver.classify`) and per-repo staleness rollup.
- `src/ai.py` — optional Claude Haiku "fix-first" briefing, aggregate-counts-only prompt, unconditional deterministic-template fallback.
- `src/report.py` — self-contained dark-mode HTML dashboard renderer (hero stats, drift matrix table, Chart.js 4.4.4 bar chart with DOM-table CDN-blocked fallback, per-repo staleness panel); all dynamic data delivered via a `<script type="application/json">` payload, DOM built with `createElement`/`textContent` only.
- `src/cli.py` — `sync` / `list` / `render` / `history` subcommands.
- `main.py` — entry point.

### [Network] Build-container constraint
- This container's Bash tool denied outbound `curl` to `pypi.org`/`registry.npmjs.org`/`api.github.com` outright (permission denied at the sandbox level, not even a 403), confirming CLAUDE.md's documented build-container network restriction. Per CLAUDE.md Step 2f, this is a build-environment constraint, not a signal to redesign — the tool is written against the real, documented PyPI JSON API, npm registry API, and GitHub REST API shapes, and every test injects a fake `urlopen` transport rather than calling the network. `GITHUB_TOKEN` is genuinely present in this container's environment (confirmed via `env`), but is used only by the shipped CLI code itself, at the user's runtime — not by this build session, consistent with "test those calls with mocks too."

### [Tests] Step 6 — Run full suite
- First run of `pytest tests/ -v` hung, growing to ~5.8GB RSS and 99.9% CPU before I killed it. Root cause: `tests/test_gh_client.py::test_list_owned_repos_paginates_until_short_page`'s fake transport checked `"page=1" in url`, but the real URL always also contains `per_page=100`, which itself contains the substring `page=1` — so every page after the first false-matched the "return 100 items" branch and pagination never terminated, growing the accumulated `repos` list forever. This was a bug in the test fixture, not in `src/gh_client.py`'s actual pagination logic (which correctly stops once a page returns fewer than 100 items). Fixed by checking `"&page=1"`/`"&page=2"` instead (the same false-match existed in `tests/test_cli.py`'s fake transport too, fixed the same way, though it never manifested there since those tests only ever seed 1-2 repos).
- Re-ran after the fix: **99 passed, 0 failed** in 0.21s (`python -m pytest tests/ -v`), well above the 15-test minimum.

### [Verify] Step 7 — Success criteria check
1. ✓ `sync` correctly parses `requirements.txt`/`package.json` pins and persists deduplicated SQLite snapshots — verified by `test_cli.py::test_sync_end_to_end_persists_snapshots` (mocked GitHub/PyPI/npm transport) and by `test_store.py`'s same-day-upsert / multi-day-history tests.
2. ✓ Cross-repo drift only fires on 2+ repos with 2+ distinct versions, with correct severity — verified by `test_drift.py` (identical pins never flagged, single-repo never flagged, patch/minor/major severity boundaries, 3-repo min/max span).
3. ✓ `render` produces a self-contained dashboard with hero stats, drift matrix, and a Chart.js bar chart with a working DOM-table CDN-blocked fallback; a malicious repo/dependency name renders only as escaped text inside the JSON payload, never as an executable tag — verified by `test_report.py`'s XSS-payload tests and confirmed live: a real `sync`→`render` run (see below) against a seeded fixture DB produced a correct, valid dashboard.
4. ✓ The optional AI briefing sends only aggregate counts/names and makes zero network calls with no `ANTHROPIC_API_KEY` — verified by `test_ai.py`'s call-count assertions and confirmed live (`render --ai` with `ANTHROPIC_API_KEY` unset returned the deterministic template instantly, no network attempt).
5. ✓ Full suite passes (99/99). Live end-to-end verification: seeded a realistic 6-row fixture DB (4 repos across `canada-list/*`, `kwyeter/web`, `nightly-builds/tools`; `requests` pinned to `2.28.0` vs `2.32.3`, `django` pinned to `3.2.0` vs `5.1.0`, a range-pinned `vite` present in only one repo) directly via `src/store` (bypassing the network-restricted `sync` step, consistent with this catalog's established pattern for build-container network constraints), then ran the real `main.py list`, `render`, `render --ai`, and `history`/`history --json` commands against it. `list` correctly reported 2 drifted dependencies (`django` MAJOR, `requests` MINOR); `vite` was correctly *not* flagged (only 1 repo); the rendered HTML's embedded JSON payload matched the seeded data exactly (`hero.repos_scanned=4`, `unique_dependencies=4`, `drifted_count=2`, `major_drift_count=1`); `history --json` returned valid, correctly-ordered JSON.

Security checklist (STANDARDS.md):
- No `.env` files committed.
- No hardcoded `password`/`api_key`/`secret`/`token`/`private_key` values anywhere in `src/`/`main.py` (grepped — only docstring mentions of the concepts, never a real assigned value).
- No `eval()`/`exec()` anywhere in the codebase.
- No `innerHTML` usage — `src/report.py`'s client-side JS builds the DOM exclusively via `createElement`/`textContent`, verified by `test_report.py::test_dom_construction_uses_textcontent_not_innerhtml` and a literal grep of the rendered output.
- No `os.system()`/`subprocess` calls anywhere.
- No file-path traversal — the only user-influenced path is `--db`/`--output`, passed straight to `sqlite3.connect()`/`open()` as the user's own CLI argument, never concatenated from remote data.
- Nothing reads from or writes to paths outside this build folder (the SQLite DB and rendered HTML are runtime output files the user names via CLI flags, not repo files).

### [Docs] Step 8 — Documentation
- `FutureFeatures.md`: 7 concrete suggestions (more manifest formats, a vulnerability overlay, a drift-trend chart, fix-command generation, private-registry support, a notify mode, archived-repo exclusion).
- `Manual.md`: setup, all 4 commands (`sync`/`list`/`render`/`history`) with real examples, how to read the dashboard's severity badges and staleness panel, and the test-run command.
- Added `.gitignore` (`__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.db`, `*.html`) so local test/run artifacts never get committed.

Build complete. Success criteria reviewed. All tests passing.
