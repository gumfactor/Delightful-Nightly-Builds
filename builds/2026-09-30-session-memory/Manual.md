# Session Memory: Manual

Search every AI conversation you have had, and get a paste-ready "resume brief" for any project.

## Setup
Python 3.11+ with SQLite FTS5 (standard in python.org and most distro builds). No runtime packages.

```bash
cd builds/2026-09-30-session-memory
export PYTHONPATH=src                     # PowerShell: $env:PYTHONPATH="src"
python -m sessionmemory serve --demo      # try it on the bundled examples
python -m sessionmemory serve             # index ~/.claude/projects (Claude Code) and start the UI
```
Open http://127.0.0.1:8765 (bound to this machine only). The database is `./sessionmemory.db`; use `--db PATH` to move it.

## Sources
| Source | How to add |
|---|---|
| Claude Code | automatic: `~/.claude/projects/*/*.jsonl` |
| Claude.ai | Settings, Export data; pass the extracted `conversations.json` or its folder |
| ChatGPT | Settings, Data controls, Export; pass `conversations.json` or its folder |

```bash
python -m sessionmemory serve ~/Downloads/claude-export ~/Downloads/chatgpt-export ~/.claude/projects
```
Transcripts are only read, never modified. Rescan (button or `ingest`) is incremental.

## Using the UI
- **Projects (left):** click one for its resume brief. **Copy brief**, then paste at the start of a new AI session.
- **Search box:** full-text with stemming ("normalising" finds "normalise"); the last word matches as a prefix. Matches are highlighted; click one to open the session scrolled to that message. The source dropdown and project selection narrow results.
- **Session view:** offline summary (open items, decisions, files edited) above the transcript.
- **Summarise with Claude / Tighten with Claude:** optional. Needs `ANTHROPIC_API_KEY` set before starting the server. This sends that session's transcript (or the brief) to the Anthropic API; nothing is sent unless you click. Uses `claude-haiku-4-5-20251001` (override with `SESSION_MEMORY_MODEL`). Results are cached until the session changes.

## CLI
```bash
python -m sessionmemory ingest [paths] [--demo]
python -m sessionmemory search postal code --project canada-list --source claude-code
python -m sessionmemory brief canada-list --sessions 6 --days 30 [--ai]
python -m sessionmemory summarize --project canada-list      # AI, needs key
```

## Tests
```bash
python -m pytest tests/ -v                # 55 tests, no network
npm install && npx playwright test        # 5 UI tests (starts its own server on :8792)
```
If Playwright cannot find its browser, set `CHROMIUM_PATH` to a Chromium binary. `node_modules/` is git-ignored.

## Limits
- Heuristic decision/open-item detection is keyword based; use the Claude button for better results.
- Project names come from each Claude Code session's working directory; export sources are grouped as "claude.ai chats" / "chatgpt chats".
