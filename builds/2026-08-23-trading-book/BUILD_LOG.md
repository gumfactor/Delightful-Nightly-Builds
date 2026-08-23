# Build Log — Trading Book

[00:00 UTC] Step 0: checked `builds/` for interrupted builds. Most recent dated folder (`2026-06-18-regex-dojo`) ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed.

[00:05 UTC] Step 1: read `PROFILE.md` and `STANDARDS.md`. Read `builds/index.md` from the most recent open PR branch (`claude/cool-sagan-iq6fyx`, PR #78) rather than the stale local copy on `main` (last synced 2026-06-24) — synced local `builds/index.md` and `builds/ideas.md` from that branch before doing anything else.

[00:10 UTC] Step 2b: day of year 235 → `(235-1) % 9 = 0` → Category A — Dashboard/Visualizer.

[00:12 UTC] Step 2c: lottery. Corrected a stale duplicate in the backlog first (idea #5, GitHub Repository Health Scorecard, verbatim duplicate of the already-built 2026-06-21 build) — marked `skipped`. Remaining Category A pool: idea #3 (rated 4) and idea #6 (unrated). R=1 → 27% draw chance. Rolled 66 → missed → fresh ideas (Step 2d). Full reasoning in `WhyThis.md`.

[00:20 UTC] Step 2d: generated 3 fresh Category A candidates (Trading Book, Research Pulse, Canada List Business Density Dashboard). Selected Trading Book — a live IBKR portfolio dashboard — as the strongest: PROFILE.md names IBKR twice as a daily tool/credentialed data source, and no prior build (71 to date) has ever connected to the user's real brokerage account. Non-winners logged as ideas #26/#27.

[00:25 UTC] Discovered this session's `.claude/settings.json` denies `Bash(pip install:*)` — confirmed via a direct attempt. No third-party package (not even `yfinance`, used by several prior builds) is installed in this container. Designed around it: `ib_insync` is imported lazily inside `ibkr_client.fetch_snapshot()` only, so the module itself has no import-time dependency on it, and every test injects a fake `ib_insync` module via `sys.modules` rather than requiring the real package. Documented in `WhyThis.md`.

[00:30 UTC] Step 4: `PRD.md` written — goal, user story, scope (explicitly read-only, no order placement), tech stack, SQLite schema (one snapshot row per UTC day, upsert on same-day re-sync), folder structure, full testing strategy, 5 success criteria.

[00:35 UTC] Step 5: build started. `src/ibkr_client.py` — `fetch_snapshot()` wraps `ib_insync.IB.connect()`/`accountSummary()`/`portfolio()`, raises `IBKRConnectionError` on any connection failure, disconnects in a `finally` block.

[00:50 UTC] `src/storage.py` — SQLite init, `sync_snapshot()` (upsert by UTC date, cascading position replace), `get_latest_snapshot()`, `get_history(days)`.

[01:05 UTC] `src/ai_briefing.py` — Claude Haiku call via `urllib.request` only (no `anthropic` package dependency), aggregate-only prompt (percentages and top-mover tickers, never dollar amounts or account ID), deterministic template fallback with zero network calls when `ANTHROPIC_API_KEY` is unset.

[01:20 UTC] `src/report.py` — self-contained dark-mode HTML dashboard: hero stats, Chart.js 4.4.4 net-liquidation trend line + asset-class donut (both with a DOM-table CDN-blocked fallback), sortable/searchable positions table. All dynamic data delivered as an escaped JSON blob read via `textContent`, DOM built with `createElement`/`textContent` only — no `innerHTML` from data.

[01:35 UTC] `main.py` — CLI (`sync`/`show`/`history`/`render`) wiring all four modules together with `argparse`.

[01:45 UTC] Step 5/6: wrote `tests/` (5 files, 41 tests). This container's pytest is a standalone `uv tool install` (not on this Python's import path — `python3 -c "import pytest"` fails, `python3 -m pip install pytest` is denied by `.claude/settings.json`), so the run command is `/root/.local/bin/pytest tests/ -v` from inside the build folder; documented in `Manual.md` alongside the plain `python -m pytest tests/ -v` the user's own machine will use once they `pip install pytest` there.

[02:05 UTC] Tests: 41 passed, 0 failed.

[02:10 UTC] Step 7: verified all 5 PRD success criteria. Seeded a real `trading_book.db` with 7 days of fixture snapshot history (via `storage.sync_snapshot`, not the CLI's `sync`, since a real TWS/Gateway connection isn't reachable from this container) including two position symbols carrying `</script><script>...</script>` and `<img onerror=...>` payloads, ran `main.py render --ai-briefing` (no `ANTHROPIC_API_KEY` set, confirming the deterministic-fallback path), and opened the resulting `dashboard.html` in this container's pre-installed headless Chromium via the global npm `playwright@1.56.1` install (`node` script, not a committed test file). Confirmed live: zero page errors, zero dialogs, `window.Chart` was `undefined` (Chart.js CDN genuinely blocked by this container's egress proxy, as expected) and the DOM-table fallback rendered correctly for both charts; both XSS payloads appeared as literal text in the positions table (`symbolCellTexts` included the raw `</script><script>...` and `<img ...>` strings, never executed) with `window.__xss`/`window.__xss2` both `undefined`, exactly 3 `<script>` tags on the page (the ones this build itself authored) and 0 `<img>` tags. Deleted the seeded `trading_book.db`/`dashboard.html` afterward — they were QA fixtures, not build deliverables.

[02:25 UTC] Step 8: `FutureFeatures.md` (6 suggestions) and `Manual.md` (TWS/Gateway setup, port numbers, CLI usage, pytest run command) written.

[02:30 UTC] Step 9: `builds/index.md` updated — new catalog row, Stats block, Last 7 Builds section.

Build complete. Success criteria reviewed. All tests passing.

[08:30 UTC] Post-PR review: Codex (automated review bot) flagged a real bug in `build_report_payload` (PR #79, `src/report.py:36`) — the allocation-by-asset-class aggregation summed *signed* `market_value` per security type, so a long and a short position of the same type would net against each other before the client-side chart applied `Math.abs()`, understating gross exposure (e.g. a $10k long + $9k short STK pair would show as $1k instead of $19k). This also disagreed with `build_aggregate_summary`, which already summed absolute values correctly for the AI-briefing prompt. Verified the finding by reading the code, fixed by summing `abs(market_value)` in `build_report_payload` to match, and added `test_build_report_payload_allocation_uses_gross_not_net_exposure` as a dedicated regression test. Tests: 42 passed, 0 failed. Pushed as a follow-up commit.
