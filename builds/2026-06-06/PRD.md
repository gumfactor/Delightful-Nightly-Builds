# PRD — AI Session Context Bridge (ctxlog)

> **Build date:** 2026-06-06
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project
> **Day of week:** Saturday → Ambitious Project

---

## Goal

A Python CLI tool that captures, stores, and retrieves AI coding session context snapshots — letting you hand off state to the next session without losing your place.

## User Story

As a researcher and developer who runs multiple projects simultaneously and regularly loses context between AI coding sessions, I want to quickly record what I was working on, the current state, and my next steps, then retrieve that information as a ready-to-paste markdown handoff document, so that every new AI session starts from exactly where the last one ended rather than from scratch.

## Scope

### In Scope
- `add` command: capture project name, summary, end-of-session context, next steps, active files, and tags
- `list` command: show recent sessions, filterable by project and date
- `search` command: full-text search across summaries, context, files, and tags
- `handoff` command: generate a formatted markdown document for pasting into a new AI session
- `projects` command: list all tracked projects with session counts
- `show` command: display full detail for a specific session by ID
- JSON flat-file storage in `data/sessions.json` within the build folder
- Minimum 8 tests (Ambitious target); targeting 20+

### Out of Scope
- Web UI or TUI (CLI only)
- External API integrations or syncing to cloud services
- Encryption or access control
- Session editing or deletion
- Semantic/embedding-based search (plain text search only)
- Import from other tools

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None
- **Dependencies:** stdlib only (argparse, json, pathlib, uuid, datetime); pytest for tests
- **Runtime requirement:** `python3 main.py <command>` from the build folder

## Data Structure

Sessions are stored in `data/sessions.json` as a JSON object:

```json
{
  "sessions": [
    {
      "id": "a3f1b2c4",
      "timestamp": "2026-06-06T08:44:00Z",
      "project": "canada-list",
      "summary": "Rewrote the CSV ingestion pipeline",
      "context": "Parser handles quoted commas now. Redis cache is invalidated on upload.",
      "next_steps": ["Add column validation", "Write integration tests"],
      "files": ["src/ingest.py", "tests/test_ingest.py"],
      "tags": ["pipeline", "csv"]
    }
  ]
}
```

## Folder Structure

```
builds/2026-06-06/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py                    ← entry point: delegates to src/cli.py
├── data/
│   └── .gitkeep              ← runtime data lives here (sessions.json created on first use)
├── src/
│   ├── __init__.py
│   ├── models.py             ← Session dataclass with to_dict/from_dict
│   ├── storage.py            ← JSON persistence (load, save, append)
│   ├── journal.py            ← Journal class (add, list, get, projects)
│   ├── search.py             ← full-text search across session fields
│   ├── handoff.py            ← markdown handoff document generator
│   └── cli.py                ← argparse commands wiring everything together
└── tests/
    ├── __init__.py
    ├── conftest.py           ← shared fixtures (tmp_path storage, pre-built sessions)
    ├── test_models.py        ← Session creation, serialization, defaults
    ├── test_storage.py       ← load, save, append, directory creation
    ├── test_journal.py       ← add, list (filters, order, limit), get, projects
    ├── test_search.py        ← keyword search, case insensitivity, project filter
    └── test_handoff.py       ← handoff generation, empty states, field inclusion
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Session dataclass creation sets correct defaults and generates an 8-char ID
  - `to_dict` / `from_dict` roundtrip preserves all fields exactly
  - Storage: empty file returns `[]`; append then load returns the session; multiple sessions preserved; parent directories auto-created
  - Journal: `add_session` returns a Session object; `list_sessions` returns most recent first; project filter; limit respected; `get_session` by ID; returns None for unknown ID; `get_projects` returns sorted unique list
  - Search: finds match in summary; case insensitive; no match returns `[]`; project filter; matches in tags; matches in files
  - Handoff: contains project name; contains summary; graceful on empty sessions; graceful on missing project; limits to N sessions; includes next steps; includes files

## Success Criteria

1. All tests pass with zero failures (`python -m pytest tests/ -v`)
2. `python3 main.py add --project test --summary "test entry" --context "state" --next-steps "step one"` runs without error and writes to `data/sessions.json`
3. `python3 main.py list` shows the added session
4. `python3 main.py handoff` produces markdown with a `# AI Session Handoff` header and the session summary
5. `python3 main.py search "test"` returns the added session

---

## Scope Changes

<!-- Leave blank; add here if scope changes during build -->
