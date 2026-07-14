# Build Log — GrantScope

> **Date:** 2026-07-14
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:09 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Checked `builds/` for an incomplete prior session: the most recent dated folder (2026-06-18-regex-dojo) has a `BUILD_LOG.md` ending in "Build complete. Success criteria reviewed." — nothing to resume.
- Resynced orientation from the most recent open build PR branch (`claude/cool-sagan-ypse45`, PR #40, 2026-07-13) rather than `main`, since `main` is far behind (per CLAUDE.md's resync instructions). Copied that branch's `builds/index.md` and `builds/ideas.md` into the working tree before starting.
- Day of year 195 → `category_index = (195-1) % 9 = 5` → Category **F — Data Explorer**.
- Checked `builds/ideas.md` for pending Category F entries: idea #1 (The Canada List CSV Quality Inspector, rating 7) and idea #10 (SEC EDGAR Financial History Extractor, rating blank). `R` = 1 (only idea #1 has a numeric rating). `lottery_chance = min(75, 25 + 1*2) = 27%`. Rolled a random integer 1–100 via `$RANDOM`: rolled 71. 71 > 27 → fresh-idea path (Step 2d), lottery pool not drawn from.
- Decided to build: **GrantScope** — an NIH RePORTER-backed grant funding landscape explorer for the user's own research domain.

### [08:20 UTC] PRD Written

- Goal: explore NIH grant-funding data (free, no-auth public API) for the user's specific research areas and render a dashboard of funding trends, top institutes, and funding mechanisms, with an optional AI landscape briefing.
- Scope: NIH RePORTER API client, SQLite storage with dedupe, aggregation/analysis layer, optional Claude Haiku briefing with deterministic fallback, self-contained dark-mode HTML dashboard with Chart.js, full CLI (`sync`, `build`, `stats`, `search`, `list-topics`, `briefing`).
- Notable constraint: attempted a live connectivity check against `api.reporter.nih.gov` from this session; the Bash tool's permission layer denied the `curl` call outright (separate from the documented egress-proxy 403 behavior seen in prior builds). Per CLAUDE.md, this is a build-environment constraint, not a signal to redesign — the tool is built to call the real API at the user's runtime, and all API-touching tests use mocks.

### [08:35 UTC] Build Phase — Core Library

- Built `src/topics.py` (5 default topics seeded from PROFILE.md's named research areas), `src/api_client.py` (NIH RePORTER v2 request/response handling via `urllib.request`, no third-party deps), `src/db.py` (SQLite schema + dedupe-by-`project_num` upsert), `src/analysis.py` (funding-by-year, top-institutes, top-organizations, mechanism breakdown, stdlib TF-style keyword extraction), `src/ai_briefing.py` (Claude Haiku call via `urllib.request` with a deterministic template fallback), `src/html_report.py` (self-contained dark-mode dashboard with Chart.js 4.4.4 pinned via CDN, HTML-escaped rendering of all API-sourced text), `src/main.py` (argparse CLI dispatch for all six subcommands).

### [09:05 UTC] Tests Written and Run

- Wrote `tests/test_api_client.py` (11 tests), `tests/test_db.py` (12), `tests/test_analysis.py` (14), `tests/test_ai_briefing.py` (7), `tests/test_html_report.py` (10 initially), `tests/test_main.py` (10). All external API calls (NIH RePORTER and Anthropic) are mocked via `unittest.mock.patch` on the module-level `urllib.request.urlopen` — no live network calls in any test.
- Installed `pytest` locally (`pip install --user pytest`) since it wasn't preinstalled in this container.
- Tests: 65 passed, 0 failed. (`python -m pytest tests/ -v`)

### [09:15 UTC] Manual Verification

- Ran the full CLI against a hand-built fixture DB (bypassing `sync`, since live NIH RePORTER access is unavailable in this session's Bash sandbox — attempting `curl` against `api.reporter.nih.gov` was denied outright by the tool permission layer) to confirm `list-topics`, `sync` error paths, `build`, `stats`, `search`, and `briefing` all produce correct, non-crashing output end-to-end.
- Installed the globally-available `playwright` npm package and drove the generated `output/dashboard.html` in the container's pre-provisioned headless Chromium (`/opt/pw-browsers/chromium-1194`) to verify the dashboard beyond what pytest checks: page title, tab switching (Overview → per-topic panel visibility toggling correctly), chart fallback rendering (Chart.js's CDN was unreachable in this container as expected, and the fallback text divs correctly populated with the same numeric data instead of leaving blank canvases), and the live search filter.
- **Real bug found and fixed:** the live search filter, when a query matched zero rows, displayed "No projects stored yet. Run 'sync' to fetch data from NIH RePORTER." — the same message used for a genuinely empty (never-synced) topic. This is misleading: a user who searches for something obscure and gets no matches would be told to re-sync, not to broaden their search. Fixed `renderTable()` in `src/html_report.py` to accept a distinct `emptyMessage` parameter, and `attachSearch()` now passes "No projects match your search." when the underlying topic has data but the filter matched nothing. Re-verified live in headless Chromium after the fix, and added a regression test (`test_render_distinguishes_no_data_from_no_search_results`) to `tests/test_html_report.py`.
- The manually-seeded fixture database and dashboard used for this verification (`output/`) contain fabricated demo project numbers, not real synced data, so they are deliberately excluded from the commit (staged explicitly by filename, not via a directory-wide `git add`).
- Tests after the fix: 66 passed, 0 failed.

### [09:40 UTC] Documentation

- `FutureFeatures.md`: 8 concrete extensions (multi-source funding data, PI collaborator resolution, saved-topic customization UI, etc.)
- `Manual.md`: quick start, full command reference, configuration, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
