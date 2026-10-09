# PRD — Context Vault

> **Build date:** 2026-10-09
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious Project
> **Day of week:** Friday

## Goal

Index every local Claude Code session transcript into a searchable SQLite vault with a mobile-friendly browser UI, AI-extracted decisions/open threads per session, and a one-click "resume brief" per project.

## User Story

As a researcher-founder running many simultaneous AI-assisted projects, I want my past AI coding sessions automatically indexed, searchable and summarised into handoff briefs, so that I stop losing context between sessions without having to write anything by hand.

## Scope

### In Scope
- Parser for Claude Code `~/.claude/projects/*/*.jsonl` transcripts (defensive: unknown line types, string or block content, tool_use/tool_result, malformed lines).
- Incremental indexer into SQLite (FTS5): sessions, messages, files touched; skips unchanged files by size+mtime; removes vanished sessions.
- Ranked full-text search with snippets, project filter, safe query sanitising.
- AI summaries (Anthropic Messages API via stdlib `urllib`, `ANTHROPIC_API_KEY` at runtime): title, goal, decisions, open threads, next steps; tolerant JSON parsing; stored in the DB.
- Resume brief per project (markdown): recent sessions, open threads, decisions, hot files, git branch — deterministic, uses AI summaries when present.
- Local web server (127.0.0.1 only) + single-page responsive UI (dark/light): Search, Projects, Session viewer, Brief with copy button, Summarize and Reindex buttons.
- CLI: `index`, `search`, `brief`, `summarize`, `serve`, `demo`.
- Demo transcript generator so the UI can be tried with no real data.

### Out of Scope
- Codex / Copilot / ChatGPT export formats (listed in FutureFeatures).
- Embeddings / semantic search.
- Remote hosting or sync; transcript excerpts leave the machine only when the user explicitly runs summarize (sent to Anthropic).

## Tech Stack

- **Language:** Python 3.11+, HTML/CSS/JS (vanilla, no build step)
- **Framework:** None (`http.server`, `sqlite3` FTS5)
- **Dependencies:** stdlib only at runtime; pytest for tests
- **Runtime requirement:** `python -m ctxvault serve`, then open http://127.0.0.1:8765

## Data Structure

SQLite (`vault.db`, default `~/.ctxvault/vault.db`):
- `sessions(id PK, project, cwd, branch, started, ended, msg_count, first_prompt, source_path, size, mtime, summary_json, summarized_at)`
- `messages(id PK, session_id, idx, role, ts, text)` + FTS5 table `messages_fts` (external content)
- `session_files(session_id, path, touches)`
Summary JSON: `{title, goal, decisions[], open_threads[], next_steps[]}`.

## Folder Structure

```
builds/2026-10-09-context-vault/
├── PRD.md  WhyThis.md  BUILD_LOG.md  FutureFeatures.md  Manual.md
├── requirements.txt
├── ctxvault/__init__.py  __main__.py  parser.py  store.py  summarize.py  brief.py  server.py  demo.py  cli.py
├── ctxvault/static/index.html
└── tests/conftest.py  test_parser.py  test_store.py  test_summarize.py  test_brief.py  test_server.py
```

## Testing Strategy

- **Framework:** pytest
- **Location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **Tested:** parser variants (string/block content, tool_use file paths, malformed lines, summary lines, empty files); incremental indexing (unchanged skipped, changed re-indexed, deleted removed); FTS search incl. hostile query strings and project filter; summary JSON parsing (fenced, garbage), API call mocked (never live), missing key error; brief content; HTTP API (projects, search, session, brief, 403 on POST without header, 404, summarize with mocked client).

## Success Criteria

1. All tests pass (zero failures)
2. `demo` + `index` + `search` works end-to-end on generated transcripts, and re-index of unchanged files indexes zero.
3. Server answers all API routes on localhost and rejects state-changing requests lacking the `X-Ctxvault` header.
4. Resume brief for a project contains open threads, decisions and files touched.
5. UI renders and is usable at phone width (screenshot check).

---

## Scope Changes

(none)
