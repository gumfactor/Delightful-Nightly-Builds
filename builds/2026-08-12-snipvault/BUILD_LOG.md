# Build Log — Snipvault

> **Date:** 2026-08-12
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:18 UTC] Session Start

- Checked Step 0: most recent dated build folder (`2026-06-18-regex-dojo`) ended with "Build complete. Success criteria reviewed. All tests passing." — no interrupted build to resume.
- Read PROFILE.md, STANDARDS.md, and the freshest `builds/index.md`/`builds/ideas.md` synced from the most recent open PR branch (`claude/cool-sagan-yk5axn`, PR #68, 61 builds recorded, none rated below 4/10 yet at the last-rated entry).
- Day-of-year rotation: day 224 → `(224-1) % 9 = 7` → Category H — Developer Tool.
- Category H backlog held one `pending` row (#9), found to be a verbatim duplicate of the already-built `ci-pulse` (2026-06-28) — corrected to `skipped` in `builds/ideas.md`, pool now empty, proceeded to fresh generation.
- Decided to build: Snipvault — personal code-snippet library (SQLite + CLI + optional AI enrichment + companion Claude Code Skill).
- Build folder created: `builds/2026-08-12-snipvault/`

### [08:22 UTC] PRD Written

- Goal: local snippet library with deterministic keyword search, optional Claude Haiku enrichment/query-expansion, and a companion Skill wrapper for mid-session use.
- Scope: `add`/`search`/`get`/`list`/`remove`/`render` CLI commands, SQLite storage, self-contained dark-mode HTML dashboard, `skill/SKILL.md`.
- Notable decision: AI-assisted search expands the query into keywords before handing off to the same deterministic ranker, rather than letting the LLM directly rank results — keeps ranking auditable and makes the "zero network calls without a key" guarantee testable via a real assertion (urlopen call count), not just log inspection.

### [08:30 UTC] Build Phase — Storage + Enrichment

- `src/db.py`: SQLite schema, CRUD, and the deterministic ranked search (title/tags/description/code weighting with recency + usage_count tie-breakers).
- `src/enrich.py`: extension-to-language table, deterministic tag extraction (identifier/import frequency, stopword-filtered), deterministic one-line description fallback, and the optional Claude Haiku calls (`enrich_snippet`, `expand_query`) via `urllib.request` — both wrapped so any exception, non-200 response, or malformed JSON falls back to the deterministic path rather than raising.

### [08:45 UTC] Build Phase — CLI + Render + Skill

- `src/cli.py`: argparse wiring for all six commands; `add` accepts `--code`, a file path, or stdin; clear (non-traceback) errors on missing ids.
- `src/render.py`: dark-mode HTML dashboard, all snippet fields passed through a JSON payload embedded via `json.dumps(..., ensure_ascii=False)` inside a `<script type="application/json">` tag and read back with `JSON.parse` + `textContent`/`createElement` — never string-concatenated into HTML.
- `skill/SKILL.md`: copyable Claude Code Skill definition instructing a session on when/how to shell out to `main.py`.

### [09:05 UTC] Tests Written

- `tests/test_db.py`, `tests/test_enrich.py`, `tests/test_render.py`, `tests/test_cli.py` — 24 tests total covering DB CRUD/search ranking/filters, language/tag/description extraction, mocked AI success + fallback paths (network error, malformed JSON, no API key — each asserted via call-count/monkeypatch, not just output inspection), render escaping (including a live `</script><script>alert(1)</script>` injection payload confirmed inert), and CLI argument handling/error paths.

### [09:12 UTC] Tests Run

Tests: 24 passed, 0 failed.

### [09:15 UTC] Verify — Step 7

- All 5 PRD success criteria reviewed against the actual test suite and a manual CLI round-trip (`add`/`list`/`search`/`get`/`render`/`remove` all exercised against a real local SQLite file).
- STANDARDS.md security checklist grepped across every created file: no `.env`, no hardcoded credentials/secrets, no `eval()`/`exec()`, no `os.system()`/`subprocess`, no path traversal, nothing reads outside the build folder. One `list.innerHTML = ''` (clearing, not user data) was found and rewritten to a `while (list.firstChild) removeChild(...)` loop anyway to keep the codebase free of the pattern entirely — re-ran the full suite after the change (still 44/44 passing).
- Live headless-Chromium verification (real Playwright, not just string-matching in tests): saved two snippets with live injection payloads (`</script><script>alert(1)</script>` as a title, `<img src=x onerror=alert(2)>` as code), rendered the dashboard, and loaded it in Chromium — 2 cards rendered, both payloads showed as inert text content, zero `dialog` events (no `alert()` fired), zero `pageerror` events, and the search filter correctly narrowed 2 cards to 1 on a live query. Confirms PRD success criterion 4 with a real browser, not just the render-time unit tests.

### [09:20 UTC] Documentation

- FutureFeatures.md: 6 concrete enhancements.
- Manual.md: CLI usage, `render` walkthrough, and the exact Skill-install copy command.

Build complete. Success criteria reviewed. All tests passing.
