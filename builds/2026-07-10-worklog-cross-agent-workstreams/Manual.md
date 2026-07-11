# Manual — Worklog: Cross-Agent Project Activity Workstreams

> **Version:** 1.0 (built 2026-07-10)
> **Complexity:** Ambitious

---

## What This Is

Worklog is a local CLI that automatically turns Git activity, GitHub issues/PRs, and AI-agent
work checkpoints into a durable, queryable record of *what happened, why, and what's left* —
grouped into "workstreams" (one per objective, not one per commit or per session). Point it at
any of your repos, run `worklog sync` occasionally, and drop a checkpoint file whenever an
agent session wraps up something worth remembering. Later — in a fresh terminal, a fresh Claude
session, or six months from now — `worklog resume` or `worklog why` answers the questions you'd
otherwise have to reconstruct by hand from `git log`, GitHub, and memory.

---

## Quick Start

1. `cd` into any git repository (or use `--repo /path/to/repo` from anywhere).
2. Run `python3 -m worklog sync` — this reads commits, branches, tags, and (if `GITHUB_TOKEN`
   is set and the origin remote is GitHub) issues/PRs, and writes them to `.worklog/ledger.db`
   inside that repo.
3. Add `.worklog/` to that repo's `.gitignore` — the ledger is local, per-machine state, not
   something to commit.
4. Whenever an agent session (or you) accomplishes something worth remembering, write a
   checkpoint JSON file (see `sample_checkpoint.json` for a template) and run
   `python3 -m worklog checkpoint --from-file my_checkpoint.json`.
5. Run `python3 -m worklog resume`, `worklog standup`, or `worklog why "<search term>"` any
   time you need the story back.

All commands accept `--repo PATH` (default: current directory) and `--data-dir PATH` (default:
`<repo>/.worklog`) if you want to point at a different repo or keep the ledger elsewhere.

---

## How to Use It

### `worklog sync`

Collects commits (oldest-first, scoped to commits unique to the current branch when it isn't
the repo's default branch), branches, tags, and — if `GITHUB_TOKEN` is set and the `origin`
remote is a GitHub repo — issues and pull requests. Safe to run repeatedly: re-syncing never
creates duplicate events. Use `--no-github` to skip the GitHub call.

```
python3 -m worklog sync
python3 -m worklog --repo ~/code/some-project sync --no-github
```

### `worklog checkpoint --from-file PATH`

Ingests a provider-neutral JSON checkpoint (objective, what was accomplished, decisions with
rationale, unresolved questions, next steps, validation results, touched files, and a source
commit reference). See `sample_checkpoint.json` for the exact shape. Any long token-like
substring in free-text fields (`objective`, `accomplished`, `decisions`) is automatically
redacted before it's written to the ledger. Re-ingesting the identical checkpoint file is a
no-op (matched by `session_id`, or by objective+timestamp if no session ID is given).

### `worklog workstreams`

Lists every workstream for the current repo with its event count and the correlation
signal(s) behind it (`explicit_hint` / `self_anchor` / `issue_reference` / `branch` /
`file_overlap` / `general_bucket`) — so you can see at a glance which groupings are
high-confidence and which are a same-day catch-all.

### `worklog timeline [workstream-id]`

Chronological event list, either for one workstream or (with no argument) the whole project.

### `worklog standup --since 24h`

Groups recent activity into **Completed** (commits since the cutoff, grouped by workstream),
**In progress** (workstreams whose latest checkpoint has unresolved items), **Blocked**
(workstreams whose latest checkpoint recorded a failing validation step), and **Next**
(outstanding next-step items from the latest checkpoint per workstream). `--since` accepts
`Nd` / `Nh` / `Nm`, `today`, `yesterday`, or an ISO timestamp.

### `worklog resume [workstream-id]`

The context package for handing a workstream to a fresh human or agent: objective, recorded
decisions with rationale, unresolved questions, next steps, touched files, and how many source
events back all of it. With no workstream given, it picks the most recently active one. It also
flags two kinds of staleness:
- **HEAD drift** — the repo has moved since the last `sync` (compares live `git rev-parse HEAD`
  against what was recorded).
- **Rebased checkpoints** — a checkpoint's recorded source commit is no longer an ancestor of
  the current HEAD (via `git merge-base --is-ancestor`), meaning that context may no longer
  describe the current code.

### `worklog why "<search text>"`

Case-insensitive substring search over recorded decisions. Shows the decision, its rationale,
which workstream it belongs to, and what happened in that workstream afterward — so you can see
whether a decision was later revisited.

### `worklog show-event EVENT_ID` / `worklog search "<text>"`

Raw-evidence inspection: `show-event` dumps one event's full JSON record; `search` finds any
event (commit, branch, tag, GitHub issue/PR, checkpoint, decision) whose summary or metadata
contains the given text.

---

## The Checkpoint File Contract

```json
{
  "schema_version": 1,
  "provider": "claude",
  "session_id": "optional-provider-session-id",
  "objective": "What this session was working on",
  "accomplished": ["Concrete thing 1", "Concrete thing 2"],
  "decisions": [{"summary": "What was decided", "reason": "Why"}],
  "unresolved": ["Open question"],
  "next_steps": ["What to do next"],
  "validation": [{"command": "pytest tests/", "result": "passed"}],
  "files": ["path/touched.py"],
  "source_refs": [{"commit": "full-sha"}],
  "workstream_hint": "optional: force correlation to a named workstream"
}
```

Only `schema_version`, `provider`, and `objective` are required — everything else defaults to
empty. Any AI agent or hook that can write a JSON file can produce a checkpoint; no
provider-specific integration is required for the contract itself.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--repo` | current directory | Target git repository |
| `--data-dir` | `<repo>/.worklog` | Where the SQLite ledger lives |
| `GITHUB_TOKEN` (env var) | unset | Enables the GitHub issues/PRs collector when set and the origin remote is GitHub |
| `--since` (standup only) | `24h` | Lookback window: `Nd`/`Nh`/`Nm`, `today`, `yesterday`, or ISO timestamp |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `error: git rev-parse --show-toplevel failed` | `--repo` doesn't point at a git repository | Point `--repo` at an actual git repo, or run from inside one |
| `GitHub: skipped (GITHUB_TOKEN not set; ...)` | No token in the environment | Expected in git-only mode; set `GITHUB_TOKEN` to enable GitHub collection |
| `GitHub: skipped (GitHub API error 403: Forbidden)` | Token present but rejected by GitHub (e.g. a CI proxy placeholder token) | Use a real personal access token with `repo` scope, or ignore — sync still records all git activity |
| A workstream looks wrong / two things that should be one aren't | No issue reference or shared branch/file signal connected them | Use `workstream_hint` in a checkpoint to force the correlation, or wait for a stronger signal (e.g. a commit mentioning the issue number) |
| `worklog resume` shows "No workstreams recorded yet" | `sync` (or `checkpoint`) hasn't been run yet against this `--data-dir` | Run `worklog sync` first |

---

## Known Limitations

- Correlation is deterministic and evidence-first by design — it will not link two things it
  has no shared signal for (no AI-guessed correlation in this release). A `general_bucket`
  (dated, low-confidence) workstream is the honest fallback rather than a wrong guess.
- GitHub collection covers issues and pull requests only; reviews and CI check-runs are not
  yet ingested (see `FutureFeatures.md`).
- No AI-provider-specific session-log parsers ship in this release — checkpoints must be
  written to the JSON contract, either by hand or by a small wrapper/hook you control.
- `resume`'s staleness check for checkpoints only looks at the recorded `source_refs.commit`;
  if a checkpoint has no commit reference, it can't be flagged as rebased-past.
- The ledger is per-machine (SQLite file in `.worklog/`), not synced across machines.
