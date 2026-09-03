---
name: promptbook
description: Search your own past Claude Code prompts by task type, project, or effectiveness score, or refresh the library from recent local sessions. Use when the user asks to find a prompt they used before, wants to see what worked well in past sessions, or wants to update their Promptbook library.
---

# Promptbook

Promptbook is a local, zero-manual-entry library of the user's own past Claude Code prompts,
mined from their `~/.claude/projects/` session history and scored by what happened right after
each prompt (edits, passing tests, commits, unresolved errors).

## When to use this skill
- The user asks something like "did I already write a prompt for X" or "find my best prompt for
  fixing flaky tests."
- The user wants to refresh the library with their most recent sessions before searching.
- The user wants an overview of what kinds of prompts they send most, or which ones tend to work.

## How to run it
The tool lives at `builds/2026-09-03-promptbook/` in this repository. Run its CLI directly:

```bash
cd builds/2026-09-03-promptbook
python main.py ingest                     # pick up any new sessions since last run (fast, incremental)
python main.py search --query "<terms>"    # free-text search
python main.py search --task-type bug-fix --min-score 7
python main.py stats                       # overview: counts by task type and project
python main.py render --out /tmp/promptbook.html   # full browsable dashboard
```

Always run `ingest` before `search`/`stats` if the user's request implies "recent" or "latest" —
it is fast and safe to run every time (already-seen prompts are skipped, never duplicated).

## Interpreting results
- Score is 0-10. Treat 7+ as "this pattern reliably worked" and below 3 as "this stalled or hit
  an unresolved error" — see `Manual.md` in the build folder for the exact scoring formula.
- `search` output truncates prompt text to ~100 characters for a quick scan; if the user wants
  the full prompt to reuse, either widen the terminal read or point them at the rendered HTML
  dashboard, which has a copy button on every card.
- If `ingest` reports 0 files scanned, the user's `~/.claude/projects/` directory may not exist
  yet on this machine (e.g. a fresh install) or `CLAUDE_CONFIG_DIR` points elsewhere — mention
  the `--claude-dir` override.
