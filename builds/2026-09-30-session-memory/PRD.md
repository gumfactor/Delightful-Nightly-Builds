# PRD — Session Memory

> **Build date:** 2026-09-30
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday

---

## Goal

A local, searchable memory of every AI conversation you have had (Claude Code transcripts, Claude.ai exports, ChatGPT exports) that produces a paste-ready "resume brief" for any project, so a new AI session starts with full context.

## User Story

As a researcher/founder who runs many simultaneous AI-assisted projects and loses context between sessions, I want my existing AI transcripts indexed automatically and turned into per-project resume briefs, so that I never re-explain a project from scratch and can find "that thing we decided three weeks ago" in seconds.

## Idea Brief Traceability

No linked Idea Brief (fresh idea). It addresses the PROFILE.md friction points "Context loss between AI coding sessions" and "Re-establishing context across AI sessions", and fixes the failure noted for the 2026-06-06 ctxlog build (rated 3: required manual entry). This tool needs zero manual entry: it reads transcripts already on disk.

## Scope

### In Scope
- Parsers for three real formats: Claude Code JSONL (`~/.claude/projects/*/*.jsonl`), Claude.ai `conversations.json` export, ChatGPT `conversations.json` export (tree `mapping`)
- Auto-discovery of Claude Code transcripts; explicit paths for exports (file or folder)
- SQLite store with FTS5 (porter stemming), content-hash incremental re-ingest
- Local browser UI (served on 127.0.0.1): project sidebar, session list, full-text search with highlighted snippets and source/project filters, session viewer, summary panel, mobile-readable, dark/light
- Heuristic (offline, deterministic) session summary: title, last asks, where it left off, files edited, decision-like and open-item lines
- Optional AI summary (opt-in button/flag, `ANTHROPIC_API_KEY` at runtime, Claude Haiku via HTTPS): title, summary, decisions, open questions, next steps; cached by content hash
- Per-project resume brief (markdown) built from session summaries with a Copy button; optional AI-tightened version
- CLI: `ingest`, `serve`, `search`, `brief`, `summarize`
- Example transcripts + `--demo` mode

### Out of Scope
- Cloud sync, multi-user, auth (local only, bound to loopback)
- Embedding/semantic search (FTS5 keyword search only tonight)
- Editing or deleting source transcripts (read-only)

## Tech Stack

- **Language:** Python 3.11+, vanilla HTML/CSS/JS front end
- **Framework:** none (`http.server`, `sqlite3` with FTS5)
- **Dependencies:** stdlib only at runtime; pytest for tests
- **Runtime requirement:** `python -m sessionmemory serve` then open http://127.0.0.1:8765

## Data Structure

SQLite (`sessionmemory.db` in the working dir, path configurable):
- `sessions(id, source, project, title, started, ended, msg_count, files_json, branch, path, content_hash)`; id is `<source>:<native id>`
- `messages(id, session_id, idx, role, ts, text)`; `msg_fts` FTS5 table keyed by `messages.id`
- `summaries(session_id, content_hash, kind, json, created)` kind is `heuristic` or `ai`
- `briefs(project, kind, markdown, created)`

## Folder Structure

```
builds/2026-09-30-session-memory/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── examples/
│   ├── claude_code_sample.jsonl
│   ├── claude_ai_export.json
│   └── chatgpt_export.json
├── src/sessionmemory/
│   ├── __init__.py
│   ├── __main__.py
│   ├── models.py
│   ├── parsers.py
│   ├── store.py
│   ├── summarize.py
│   ├── brief.py
│   ├── server.py
│   ├── cli.py
│   └── static/index.html
└── tests/
    ├── conftest.py
    ├── test_parsers.py
    ├── test_store.py
    ├── test_summarize.py
    ├── test_brief.py
    └── test_server.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (from the build folder)
- **What will be tested:**
  - Each parser on realistic fixtures (tool_result-only turns skipped, system-reminder stripped, edited files collected, ChatGPT tree linearised in order, malformed lines ignored)
  - Store: incremental ingest (unchanged skipped, changed replaced without stale FTS rows), search ranking/filters/snippets, query sanitisation (FTS operators/quotes cannot raise)
  - Summaries: heuristic output, AI JSON parsing (code fences, garbage), missing key error, cache reuse; Anthropic call fully mocked
  - Brief: ordering, dedup of open items, day window
  - Server: API routes via a real loopback server thread; 404 / bad-input handling; no path traversal; AI endpoint refuses without key
- No live API calls in tests.

## Success Criteria

1. All tests pass (zero failures)
2. `ingest examples/` then `search` returns highlighted hits across all three sources
3. `brief <project>` outputs a paste-ready markdown brief without any API key
4. UI serves and works: search, project filter, session view, copy brief (verified against the running server)
5. Server binds only to 127.0.0.1 and never writes to source transcripts

---

## Scope Changes

(none)
