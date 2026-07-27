# Build Log — SiliconWatch

> **Date:** 2026-07-27
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md in full.
- Step 0: the most recent dated folder present locally was 2026-06-18-regex-dojo, but this branch's `builds/index.md` was stale relative to the true repo state — resynced from the most recent open PR branch (`claude/cool-sagan-qicbny`, PR #52, 2026-07-26 TripKit) per CLAUDE.md's Step 1 instructions. That branch's `index.md`/PR body confirm TripKit finished cleanly (status `complete`, 43/43 tests). No incomplete build to resume.
- Copied `builds/index.md` and `builds/ideas.md` from `origin/claude/cool-sagan-qicbny` into this branch's working tree so tonight's work builds on the true current state (45 builds, last date 2026-07-26).
- Day of year 208 → `(208-1) % 9 = 0` → Category A — Dashboard/Visualizer.
- Category A backlog lottery: R=1 (one rated pending idea), threshold 27%, rolled 26 → draw triggered; weighted draw (14 tickets across #3/#5/#6) rolled 7 → selected backlog idea #5, "GitHub Repository Health Scorecard." Discovered this is a verbatim duplicate of the already-built, already-rated (6/10) 2026-06-21 build of the same name and concept. Idea #6 is likewise a duplicate of the 2026-06-20 Run Planner's Open-Meteo activity scoring. Marked both `skipped` in `builds/ideas.md` with rationale, overrode to fresh-idea generation rather than rebuild a zero-differentiation duplicate. Full reasoning in `WhyThis.md`.
- Topic-diversity check on last 10 builds: Canada-related (CanEcon Pulse, CanFile) and academic-research (Protocol Forge, Bridgework, Bayes Lab) topics both appeared multiple times — ruled out a third Canada dashboard and a citation-tracker dashboard, appended both as backlog ideas #17/#18 for later.
- Decided to build: **SiliconWatch** — a comparative dashboard over AI-infrastructure/semiconductor companies (GPU/accelerators, foundry, equipment, memory, IP/analog), targeting PROFILE.md's named "AI infrastructure and semiconductors" rabbit-hole topic, never previously built.
- Build folder created: `builds/2026-07-27-siliconwatch/`
- Verified `yfinance` (1.5.2) and `pytest` (9.1.1) install cleanly via pip in this build container — PyPI access works even though direct external API hosts (query1.finance.yahoo.com) return no data, consistent with CLAUDE.md's network-policy guidance.

### [08:20 UTC] PRD Written

- Goal: sector-comparative dashboard over 12 curated AI-infra/semiconductor tickers with valuation, margin, and price-trend data that compounds across repeated `sync` runs.
- Scope: `sync`/`report`/`list` CLI, SQLite persistence (snapshots + price history, both deduplicated), Chart.js dashboard with graceful CDN-fallback, optional Claude Haiku sector narrative with an always-available deterministic fallback.
- Notable constraints: no intraday data (yfinance is EOD-oriented — a research tool, not a trading terminal); no portfolio/position tracking (that's the existing Investment Research Platform's job).

### [08:25 UTC] Build Phase — Data, Storage, Metrics, AI, Dashboard, CLI

- `src/config.py`: default 12-ticker/6-subsector list; `--config` JSON override with validation (missing file, malformed JSON, missing required fields, and empty array all raise a clear `ConfigError`).
- `src/data_fetch.py`: `fetch_snapshot()` and `fetch_price_history()`, both take an injectable `ticker_factory` so tests never touch the network; `.info` field access is defensive (`.get()` with `None` fallback and a NaN/type guard) since yfinance's info dict fields are inconsistently populated across tickers; neither function ever raises.
- `src/storage.py`: SQLite schema with `(ticker, snapshot_date)` and `(ticker, date)` primary keys via `INSERT OR REPLACE`, so re-running `sync` the same day upserts rather than duplicating.
- `src/metrics.py`: price-delta (1-day/1-year, with a reliability flag based on date span) and sector-aggregate calculations, all `None`-safe.
- `src/ai_narrative.py`: optional Claude Haiku call via `urllib` (no `anthropic` package dependency, matching this repo's established pattern), sends only aggregated public numbers and public company names, never personal data; deterministic template fallback on any missing key/network error/malformed response, returning `(text, source)` so the dashboard can label which one was used.
- `src/dashboard.py`: HTML renderer, `html.escape()` on every string sourced from ticker config (defends against a malicious `--config` file), Chart.js 4.4.4 pinned CDN with a plain-table fallback path detected via `typeof window.Chart === 'undefined'`.
- `src/main.py`: argparse CLI wiring `sync`/`report`/`list`; `--tickers` filters the loaded universe (default or `--config`) and synthesizes minimal metadata for any ticker not already in it.

### [08:50 UTC] Tests Written and Run

Tests: 67 passed, 0 failed. (`python3 -m pytest tests/ -v` from the build folder, first clean run — no fix-up iterations needed)

Every `yfinance` call and every Anthropic API call is mocked via dependency injection (`ticker_factory`, `http_post`); SQLite tests use a `tmp_path`-backed temp-file database per test. No live network calls made during the suite.

### [09:05 UTC] Manual Verification (real container run, not part of the committed suite)

- Confirmed this container's egress policy blocks live `yfinance` data (`fetch_snapshot("NVDA")` against the real network returned all-`None` metrics, no exception) — consistent with CLAUDE.md's documented build-container network constraint. The code is written against yfinance's real, documented API and degrades gracefully; this is a build-environment limitation, not a design signal.
- Ran a standalone script (outside the test suite) that monkeypatches `main.fetch_snapshot`/`main.fetch_price_history` with realistic randomized fixture data for all 12 default tickers, then exercised the real CLI end-to-end: `sync` → `sync` again same day → `report`.
- `sqlite3` row count after two same-day `sync` calls: **12**, not 24 — upsert-not-duplicate confirmed outside the test suite too.
- Opened the generated dashboard in headless Chromium (pre-provisioned in this environment, via the global `playwright` npm package) and confirmed via `page.on('pageerror')`/`page.on('console')`: **zero page errors**. The Chart.js CDN request was in fact blocked (`ERR_TUNNEL_CONNECTION_FAILED`, confirmed via console message) and the fallback path engaged correctly — `window.Chart` was `undefined`, all 4 canvases hid themselves, and all 4 fallback tables displayed with the correct row counts (12 companies, non-empty price/P/E trend rows).
- Exercised the interactive JS live: selecting a different ticker in the price-history dropdown correctly switched the fallback table's contents; typing "NVDA" into the search box correctly narrowed the visible table rows to exactly 1; clicking a table header triggered the sort handler with no errors.
- Confirmed the AI-sector-narrative deterministic fallback text rendered correctly with real aggregate numbers (e.g., "Across the 12 tracked AI-infrastructure and semiconductor companies, combined market capitalization stands at $19.60T...").

### [09:20 UTC] Verify — Step 7 Success Criteria Check

1. All 67 tests pass — confirmed above.
2. `sync` → `report` produces a valid self-contained HTML file with all 12 default companies grouped by sub-sector — confirmed by the manual run (12 rows, 4 KPI cards, 4 canvases) and `test_dashboard.py`/`test_cli.py`.
3. Re-running `sync` same-day does not duplicate rows — confirmed by `test_storage.py::test_upsert_snapshot_same_day_updates_not_duplicates`, `test_cli.py::test_cli_sync_twice_same_day_does_not_duplicate`, and the manual same-day double-sync (12 rows, not 24).
4. Dashboard degrades gracefully with no `--ai` flag and with Chart.js CDN unreachable — confirmed by `test_dashboard.py`'s placeholder/label tests and the manual run, where the CDN was genuinely blocked and the fallback engaged with zero page errors.
5. Every config-sourced string is HTML-escaped — confirmed by `test_dashboard.py::test_render_dashboard_escapes_html_injection_payload`.

Security checklist (STANDARDS.md):
- No `.env` files present
- No hardcoded credentials/API keys — `grep` for password/api_key/secret/private_key patterns found only test-fixture placeholders (`api_key="test-key"`) and env-var references; the real Anthropic key is read only from `ANTHROPIC_API_KEY` at runtime
- No `eval()`/`exec()` anywhere in `src/` or `tests/`
- No `innerHTML` assignment from user-controlled data — the two `innerHTML` occurrences in `dashboard.py`'s embedded JS only clear a container (`= ''`) before rebuilding rows via `createElement`/`textContent`
- No `subprocess`/`os.system()` calls anywhere
- No file-path traversal — `--db`/`--config`/`--output` are user-supplied local paths passed directly to `open()`/`sqlite3.connect()`, never concatenated into another path
- All code confined to `builds/2026-07-27-siliconwatch/`; `__pycache__`/`.pytest_cache` cleaned before commit

### [09:25 UTC] Documentation Complete

- `FutureFeatures.md`: 8 concrete follow-on ideas across quick wins, medium effort, and ambitious extensions
- `Manual.md`: quick start, full command reference, configuration, troubleshooting, known limitations

Build complete. Success criteria reviewed. All tests passing.
