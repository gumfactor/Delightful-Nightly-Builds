# Manual — Promptbook

Promptbook builds a searchable, scored library of your own past Claude Code prompts, mined
automatically from the session transcript files Claude Code already keeps on your machine.
You never type anything in twice — it reads what you already wrote.

## Requirements
- Python 3.10+
- `pip install -r requirements.txt` (only installs `pytest`, for running the test suite — the
  tool itself needs nothing beyond the Python standard library)
- Local Claude Code usage history under `~/.claude/projects/` (or wherever `CLAUDE_CONFIG_DIR`
  points, if you've set it)

## Quick start
```bash
cd builds/2026-09-03-promptbook
python main.py ingest
python main.py stats
python main.py render --out promptbook.html
```
Then open `promptbook.html` in any browser — it's a single self-contained file, no server needed.

## Commands

### `ingest`
Scans `~/.claude/projects/**/*.jsonl` (every local project's session history), extracts every
prompt you personally typed, and stores it with a task-type tag and an effectiveness score.
Safe to re-run any time — already-seen sessions are only re-scanned for lines added since the
last run, and prompts are deduplicated by their own unique ID, so re-running never creates
duplicates.

```bash
python main.py ingest                          # default: ~/.claude/projects
python main.py ingest --claude-dir /path/to/dir # point at a different projects directory
```

### `search`
```bash
python main.py search --query "regex"          # text search
python main.py search --task-type bug-fix       # filter by task type
python main.py search --min-score 7             # only strong prompts
python main.py search --project /home/you/some-repo
```
Task types: `bug-fix`, `feature`, `refactor`, `research`, `test`, `docs`, `config`, `review`,
`other`. Results are ranked by score (highest first), then recency.

### `stats`
Prints totals, an average score, and a per-task-type and per-project breakdown.

### `render`
Writes a self-contained dark-mode HTML dashboard: searchable, filterable by task type/project/
score, with a copy button on every prompt so you can reuse it immediately.

```bash
python main.py render --out promptbook.html
python main.py render --out promptbook.html --ai   # add AI notes to your top-scoring prompts
```
`--ai` requires `ANTHROPIC_API_KEY` in your environment. Without it, `render --ai` still works —
every note falls back to a deterministic templated sentence built from the same score/task-type/
tools data, with zero network calls.

## How the effectiveness score works
Every prompt gets a score from 0-10, computed purely from what happened right after you sent it
in that same session — no AI judgment involved:

| Signal detected after the prompt | Points |
|---|---|
| A `git commit` ran | +4 |
| A test command ran and passed | +3 |
| A test command ran with no clear pass/fail signal | +1 |
| At least one file was edited, with no unresolved error | +2 |
| An error occurred with nothing successful afterward (unresolved) | -3 |

Score is clamped to 0-10. A 9 means you asked for something, tests ran and passed, files got
edited cleanly, and you committed the result — about as strong a signal as this tool can give
that the prompt actually worked.

## Known limitations
- **Heuristic, not ground truth.** The score reflects *observable* signals in the transcript
  (commits, test output, error text), not whether the change was actually good — a passing test
  suite that doesn't cover the real behavior still scores well.
- **Session-scoped.** An "episode" only looks forward to the next prompt in the *same* session.
  If you fixed something two prompts later, the original prompt won't get credit for it.
  It's reasonable to interpret the sequence of prompts and events, but not guaranteed exhaustive.
- **Test-pass detection is regex-based.** It looks for common patterns like "N passed" or "N
  failed" in tool output. An unusual test runner's output format may be read as ambiguous
  (+1) rather than a clean pass (+3).
- **Task-type tags are keyword-driven**, not semantic. A prompt that doesn't use any recognized
  keyword pattern is tagged `other`.
- **Local Claude Code session data only.** This does not read anything from ChatGPT, Codex, or
  any other tool, even though PROFILE.md lists them as tools in daily use.

## Privacy
Everything runs locally. `ingest` only reads your own `.jsonl` session files (never writes to
them) and stores extracted prompt text plus small structural signals in a local SQLite file at
`data/promptbook.db`. The only thing ever sent anywhere is, optionally with `--ai`, a single
already-classified prompt's text plus its computed score/task-type/tool-name list to the
Anthropic API — never raw tool output, file contents, or any other part of the transcript.

## Running the tests
```bash
python -m pytest tests/ -v
```
81 tests, all passing, using only synthetic fixture transcripts (no real session data is ever
committed to this repository).
