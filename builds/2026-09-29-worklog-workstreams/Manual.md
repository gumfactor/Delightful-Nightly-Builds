# worklog — Manual

worklog turns scattered project activity (Git, GitHub, AI-agent sessions, your own notes) into **workstreams**: one objective with its commits, issue, PR, CI runs, reviews, agent sessions and decisions, each statement traceable to a source event.

Python 3.11+, stdlib only at runtime. Optional: `pip install pyyaml` for YAML checkpoint files (JSON always works).

## Quick start
```bash
cd builds/2026-09-29-worklog-workstreams
./worklog -C /path/to/your/repo sync          # Git + GitHub (uses GITHUB_TOKEN if set)
./worklog -C /path/to/your/repo workstreams
./worklog -C /path/to/your/repo standup --since yesterday
./worklog -C /path/to/your/repo resume         # most recent unfinished workstream
./worklog -C /path/to/your/repo why "type coercion"
```
`python -m worklog` also works with `PYTHONPATH=src`.

The ledger is `<repo>/.git/worklog/ledger.db` (invisible to `git status`); override with `WORKLOG_DB`. `sync` is idempotent. Without GitHub access it prints `github: skipped (...)` and continues in Git-only mode; `--no-github` skips on purpose. `GITHUB_TOKEN` is read from the environment and only sent in the Authorization header; private repos the token can see are included.

## Commands
| Command | Purpose |
|---|---|
| `sync [--since 30d] [--no-github]` | Collect commits (all branches), tags, working-tree state, issues, PRs, reviews, check runs |
| `checkpoint --from-file cp.json` (or JSON on stdin) | Record an agent checkpoint |
| `hook` | Claude Code hook: automatic checkpoint from the session transcript |
| `note --type decision/blocker/note --text ... [--reason --rejected --supersedes --files --workstream]` | Record human facts |
| `workstreams [--status --provider --actor --since]` | List |
| `timeline [WS]` | Chronology, why events are grouped, unapplied suggestions |
| `standup [--since yesterday]` | Completed / in progress / blocked / next |
| `resume [WS]` | Context package for a fresh human or agent, with freshness checks |
| `why "query" [--workstream WS]` | Decision, rationale, rejected alternatives, later evidence |
| `search TERM`, `show-event ID` | Inspect raw events (ID prefix or commit SHA) |
| `merge A B`, `split EVENT`, `rename WS "Title"`, `resolve EVENT` | Override correlation / mark blockers resolved |
| `purge --yes` | Delete everything recorded for this project; `sync` rebuilds Git/GitHub data |

Global flags: `-C DIR`, `--json` (workstreams, timeline, standup, resume, why, search, sync). `WS` is a workstream id (`ws_1a2b3c4d`), an event id, or a unique part of the title.

## Automatic capture from Claude Code
Add `hooks/claude-settings-snippet.json` (absolute path filled in) to `~/.claude/settings.json` or the project's `.claude/settings.json`. On every Stop/SessionEnd the hook stores one checkpoint per session, updated in place: the first line of your first prompt as the objective (max 160 chars, secrets redacted), files the agent edited inside the repo, test-runner commands with pass/fail, and commits made since the session started. Transcripts are never copied. The hook always exits 0, so it cannot break a session.

## Checkpoint format (other agents)
JSON (or YAML) with `provider` and `objective` required:
```json
{"schema_version": 1, "provider": "codex", "session_id": "abc", "timestamp": "2026-09-03T14:30:00Z",
 "objective": "Add CSV validation",
 "accomplished": ["Added schema checks"],
 "decisions": [{"summary": "Reject automatic type coercion", "reason": "Can corrupt identifiers",
                "rejected": ["Coerce to int"], "supersedes": null, "files": ["src/validation.py"]}],
 "unresolved": ["Blank optional columns?"], "blockers": [], "next_steps": ["Add malformed-row fixtures"],
 "validation": [{"command": "pytest", "result": "passed"}], "files": ["src/validation.py"],
 "source_refs": [{"commit": "abc123"}, {"issue": "41"}, {"pr": "52"}]}
```
Branch and HEAD are filled from the checkout if omitted. Re-sending the same `session_id` updates that checkpoint.

## How grouping works
Confirmed links: same commit SHA, same `#N` issue/PR number (commit messages, PR bodies, branch names like `feature/41-x`), same non-default branch, same checkpoint objective, explicit `--workstream` on notes. Inferred links: overlapping files close in time, merged only at score ≥ 0.75 and shown as `[inferred]`. Scores 0.4–0.75 appear as suggestions in `timeline` and change nothing. `merge`/`split`/`rename` always win.

## Reading the output
`[recorded]` = stored source event; `[observed]` = read from your checkout now; `[inferred]` = heuristic; `[STALE]` = a checkpoint's recorded head no longer matches its branch, the branch is gone, or the PR merged/closed since. Every claim carries `[commit abc1234 | evt_xxxxxxxx]`; either half works with `show-event`.

## Config: `.worklog.json` in the repo root
```json
{"name": "lab-tools", "exclude_paths": ["*.lock", "data/*"], "exclude_branches": ["wip/*"],
 "exclude_providers": [], "default_branch": "main", "github_repo": "owner/name", "max_commits": 500}
```

## Privacy
Only metadata and short summaries are stored: no diffs, no transcripts. Likely credentials (GitHub/Anthropic/AWS/Slack tokens, Bearer headers, `password=`, private keys, URL credentials) are redacted before anything is written. The only network calls are to GitHub's API. `purge --yes` deletes everything.

## Tests
```bash
python -m pytest tests/ -v      # 107 tests; needs pytest; temporary git repos, no network
```
