# Future Features — AI Session Context Bridge (ctxlog)

> Ideas for extending this tool. These are intentionally left for future builds to avoid scope creep tonight.

---

## 1. Session Editing and Deletion

Add `python3 main.py edit SESSION_ID` and `python3 main.py delete SESSION_ID` commands. Useful for correcting typos in summaries or removing test entries. Editing should preserve the original timestamp and ID while updating other fields, with a `last_edited` field added to the JSON record.

## 2. Project-Level Configuration and Aliases

Allow a `config` command that sets a default project for the current working directory (stored in `.ctxlog` file at the repo root). This means you could run `ctxlog add --summary "..."` from inside a project folder and it auto-detects the project name from the directory or config. Removes the most common friction point in daily use.

## 3. Richer Export Formats

Beyond plain markdown, add export options:
- `--format json` — structured output for piping to other tools
- `--format txt` — plain text for minimal paste contexts  
- `--format html` — standalone HTML file for archiving a session history
- An `export-all --project PROJ` command that generates a full history document

## 4. Session Linking and Continuations

Add a `--continues SESSION_ID` flag to `add`, letting you link a new session as the continuation of a prior one. The `handoff` command could then follow the chain and present a coherent thread of work rather than treating each session independently. Especially useful for multi-day features that span many sessions.

## 5. Tag Management and Filtering

Add a `tags` command that lists all tags used across sessions with counts, and extend `list` and `search` to support `--tag TAG` filtering. Tags are already stored in the JSON schema — this just requires surface-level CLI work and a few tests.

## 6. Fuzzy / Semantic Search (Optional Upgrade Path)

The current search is exact substring matching. A future version could add:
- **Fuzzy matching** using the stdlib `difflib` module (no extra dependencies)
- **Semantic search** using sentence-transformers or an Anthropic embeddings API call — would require adding a dependency but could dramatically improve recall for "find that thing I was working on about authentication" queries

## 7. Import from Git Log

Add a `python3 main.py import-git [N]` command that reads the last N git commits from the current repo's log and creates session entries from them automatically (using commit message as summary, date as timestamp, changed files as the files list). This would be a strong bridge between ctxlog and actual coding history with zero manual effort.

## 8. Session Statistics Dashboard

Add a `stats` command (or `--stats` flag to `list`) that shows:
- Sessions per project
- Most active days/weeks
- Average sessions per week
- Longest streak of consecutive days logged

Useful for reflecting on work patterns across projects.