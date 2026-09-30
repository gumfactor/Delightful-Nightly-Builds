# Build Log — Session Memory

> **Date:** 2026-09-30

## Log

### Session Start
- Read CLAUDE.md, PROFILE.md, STANDARDS.md, builds/index.md. No `gh` CLI available, so the main copy of index.md was used (it already lists builds through 06-24).
- Step 0: latest dated folder on main (2026-06-18-regex-dojo) is complete; nothing to resume.
- Day 273, category index 2 = C (Personal Knowledge Tool). Backlog has no pending C rows: fresh ideas. Chose Session Memory.
- Branch: the session designated `claude/cool-sagan-ygw1tm`, so work stays there instead of a `build/...` branch.

### PRD Written
- Stdlib Python (http.server, sqlite3 FTS5), vanilla JS UI, optional Anthropic Haiku summaries via urllib (no SDK dependency).

### Build Phase
- Parsers for Claude Code JSONL, Claude.ai export, ChatGPT export (tree walked from `current_node`).
- Store with content-hash incremental ingest; FTS rows deleted explicitly on re-ingest (tested for stale hits).
- Heuristic summary + opt-in AI summary; brief builder; loopback-only server with Host-header check (DNS-rebinding guard); UI builds DOM with textContent only.
- Obstacle: first example fixture put three sessions in one JSONL, which merged them into one session (real files hold one session each). Split into three files.
- Obstacle: nested double quotes in an f-string failed on Python 3.11; changed quote style.
- `pip install` was blocked in the build sandbox; the preinstalled `pytest` binary was used. Playwright ran from the global install with the bundled Chromium.
- Deviation: `playwright.config.js` and the UI spec import `playwright/test` (package.json lists `playwright`) rather than `@playwright/test`.

### Tests Run
- Tests: 55 passed, 0 failed (pytest: parsers, store, summaries, brief, server).
- Tests: 5 passed, 0 failed (Playwright UI smoke: `npx playwright test`).
- Security checklist run: no eval/exec/subprocess, no innerHTML from data, no hardcoded keys, no path input from HTTP (session ids are only SQL parameters).
- Live Anthropic calls were not exercised (no key in build env); the HTTP layer is mocked in every test.

Build complete. Success criteria reviewed. All tests passing.
