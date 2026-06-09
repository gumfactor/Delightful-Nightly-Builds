# Manual — AI Session Context Bridge (ctxlog)

> A Python CLI tool for capturing AI coding session state and generating handoff documents.
> All data is stored locally in `data/sessions.json`.

---

## Quick Start

```bash
# From this folder (builds/2026-06-06/)

# Capture what you just worked on
python3 main.py add \
  --project canada-list \
  --summary "Rewrote the CSV parser to handle RFC 4180 edge cases" \
  --context "Redis cache is invalidated on every upload trigger" \
  --next-steps "Add column validation" "Write integration tests" \
  --files "src/ingest.py" "tests/test_ingest.py" \
  --tags "csv" "pipeline"

# See recent sessions
python3 main.py list

# Get a handoff document for the next AI session
python3 main.py handoff --project canada-list
```

---

## Commands

### `add` — Capture a session

```
python3 main.py add [options]
```

| Flag | Short | Description |
|------|-------|-------------|
| `--project` | `-p` | Project name (required if non-interactive) |
| `--summary` | `-s` | What you were working on (required if non-interactive) |
| `--context` | `-c` | Key state at the end of the session |
| `--next-steps` | `-n` | Next steps; pass multiple values: `--next-steps "A" "B"` |
| `--files` | `-f` | Files being worked on; pass multiple values |
| `--tags` | `-t` | Tags for later filtering; pass multiple values |

Run without flags in a terminal to enter interactive mode (prompts for each field).

### `list` — Show recent sessions

```
python3 main.py list [--project PROJ] [--limit N] [--today]
```

Shows sessions in reverse chronological order. Defaults to last 10.

### `search` — Find sessions by keyword

```
python3 main.py search QUERY [--project PROJ]
```

Case-insensitive substring search across: summary, context, project name, tags, files, and next steps.

### `handoff` — Generate a markdown handoff document

```
python3 main.py handoff [--project PROJ] [--sessions N]
```

Outputs a structured markdown document ready to paste at the start of a new AI coding session. Shows the latest session's full detail, then summarises prior sessions. Defaults to 3 sessions.

**Typical workflow:**
```bash
python3 main.py handoff --project canada-list | pbcopy  # macOS
python3 main.py handoff --project canada-list | xclip   # Linux
```

Then paste into a new Claude/ChatGPT session.

### `projects` — List all tracked projects

```
python3 main.py projects
```

### `show` — View full detail for a session

```
python3 main.py show SESSION_ID
```

The session ID is the 8-character code shown in square brackets by `list` and `search`.

---

## Data Storage

All data is stored in `data/sessions.json` within this build folder. The file is created automatically on first use. Sessions are appended only — there is no delete command by design, keeping the record complete.

To back up your sessions, copy `data/sessions.json` to another location.

---

## Running Tests

```bash
# From this folder (builds/2026-06-06/)
python -m pytest tests/ -v
```

Expected output: 44 tests passing, 0 failures.

Test files:
- `tests/test_models.py` — Session creation, serialization, defaults (5 tests)
- `tests/test_storage.py` — Persistence layer (7 tests)
- `tests/test_journal.py` — Journal operations (10 tests)
- `tests/test_search.py` — Full-text search (11 tests)
- `tests/test_handoff.py` — Handoff generation (11 tests)

---

## Requirements

- Python 3.10+
- No external dependencies for runtime (stdlib only)
- `pytest` for running tests (`pip install pytest`)