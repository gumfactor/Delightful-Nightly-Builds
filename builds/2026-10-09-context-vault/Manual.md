# Context Vault — Manual

Searchable vault of your Claude Code sessions. Python 3.11+, stdlib only, no build step.

## Try it with no real data
```bash
cd builds/2026-10-09-context-vault
python -m ctxvault demo          # http://127.0.0.1:8765, sample transcripts, in-memory
```

## Use it on your real sessions
Claude Code writes transcripts to `~/.claude/projects/<project>/<session>.jsonl` (on Windows: `%USERPROFILE%\.claude\projects`).
```bash
python -m ctxvault serve                 # indexes (incrementally), then serves the UI
python -m ctxvault index                 # index only; prints indexed/skipped/removed counts
python -m ctxvault search "dedupe www"   # CLI search, add --project NAME
python -m ctxvault brief canada-list     # print a resume brief (markdown)
export ANTHROPIC_API_KEY=...             # needed only for summaries
python -m ctxvault summarize --limit 10  # AI summaries of the newest un-summarised sessions
```
Global options (before the command): `--src DIR` transcripts folder, `--db FILE` vault path (default `~/.ctxvault/vault.db`).

## The UI
- **Projects**: one card per project; open it for its sessions, a **Resume brief** (copy the markdown into a new AI session) and **Summarise recent**.
- **Search box**: ranked full-text over every message (stemmed + prefix, e.g. `calib` finds *calibration*). The dropdown filters to one project.
- **Session view**: AI summary (goal, decisions, open threads, next steps), files touched, full transcript.
- **Reindex**: re-scan the folder after new sessions.

## Notes
- Only text from user and assistant messages is indexed. Tool output and thinking blocks are skipped.
- Summaries send a condensed transcript (max ~24k characters) to the Anthropic API, only when you click Summarise or run `summarize`. Nothing else leaves your machine.
- The server binds to 127.0.0.1, rejects foreign Host headers, and requires an `X-Ctxvault` header on POSTs.
- A session summary is kept when its transcript grows and is re-indexed; use *Re-summarise* to refresh it.

## Tests
```bash
pip install pytest
python -m pytest tests/ -v
```
All Anthropic calls are mocked.
