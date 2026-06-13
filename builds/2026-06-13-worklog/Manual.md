# Manual — worklog: Cross-Agent Project Activity Workstreams

> **Version:** 1.0 (built 2026-06-13)
> **Complexity:** Ambitious Project

---

## What This Is

`worklog` is a local-first Python CLI that captures project activity from Git commits, GitHub issues and pull requests, and agent session checkpoints, correlates them into evidence-backed workstreams, and generates three key views: `standup` (what happened), `resume` (what a fresh agent or human needs to know), and `why` (the decision history). It solves the recurring problem of having to manually reconstruct project state every time a new AI coding session begins.

Data is stored in a SQLite ledger at `~/.worklog/<project_id>.db`. All features work offline; GitHub data is collected opportunistically when `GITHUB_TOKEN` is available.

---

## Quick Start

1. **Install dependencies** (once):
   ```bash
   pip install -r requirements.txt
   ```

2. **Sync your repo** (run after each work session):
   ```bash
   python3 main.py sync
   ```

3. **Start your next session** with a resume brief:
   ```bash
   python3 main.py resume
   ```

4. **Write checkpoints** when an agent session ends:
   ```bash
   python3 main.py checkpoint --file my_session.yaml
   ```

---

## Commands

### `worklog sync [--since N]`

Collects recent Git commits, dirty-tree state, and (if `GITHUB_TOKEN` is set) GitHub issues and pull requests. Stores events in the ledger and auto-detects workstreams.

```bash
python3 main.py sync              # last 30 days
python3 main.py sync --since 7   # last 7 days only
```

Re-running sync is safe — duplicate events are skipped by deterministic ID.

---

### `worklog checkpoint --file PATH | --from-stdin`

Ingests an agent session checkpoint YAML. The YAML records what an AI agent accomplished, what decisions were made, what is unresolved, and what comes next. These facts become searchable events and decisions in the ledger.

```bash
python3 main.py checkpoint --file session.yaml
```

**Checkpoint YAML format:**
```yaml
schema_version: 1
timestamp: 2026-06-13T14:30:00Z   # UTC ISO-8601
provider: claude                    # claude | codex | copilot | human
session_id: sess-abc123             # optional; any identifier
objective: "Add CSV validation"
accomplished:
  - "Added schema checks before ingestion"
decisions:
  - summary: "Reject automatic type coercion"
    reason: "Can silently corrupt identifiers"
    alternatives:
      - "Coerce to inferred type (rejected)"
unresolved:
  - "Decide whether blank optional columns are warnings"
next_steps:
  - "Add malformed-row fixtures"
validation:
  - command: "python -m pytest tests/ -v"
    result: passed                  # passed | failed
files:
  - src/validation.py
source_refs:
  - commit: abc123def456
```

**Note on YAML gotcha:** If an alternative contains `: ` (colon-space), wrap it in quotes: `"Use JSONL: fast but fragile"`.

For use with Claude Code hooks (hook-compatible stdin mode):
```bash
cat checkpoint.yaml | python3 main.py checkpoint --from-stdin
```

---

### `worklog standup [--since N]`

Groups recent events by workstream into **Done / In Progress / Blocked / Next**. Deduplicates commit lines when multiple commits serve one accomplishment.

```bash
python3 main.py standup           # last 1 day
python3 main.py standup --since 7 # last week
```

---

### `worklog resume [WORKSTREAM_ID]`

Produces a context package for a fresh agent or human: objective, accomplished, unresolved, next steps, decisions, recent commits, open PRs, and source session IDs. Emits a freshness warning if the stored HEAD doesn't match the current HEAD.

```bash
python3 main.py resume                         # uses latest checkpoint's workstream
python3 main.py resume ws_49e344b5f45fd71a     # specific workstream
```

**Freshness warning** example:
```
⚠ STALE: stored HEAD abc123456789 != current HEAD def098765432
```
This means `worklog sync` should be run before relying on the output.

---

### `worklog why QUERY`

Searches the decision history by keyword. Shows each matching decision with its reason, alternatives rejected, and source event ID.

```bash
python3 main.py why "coercion"
python3 main.py why "SQLite"
python3 main.py why "authentication"
```

---

### `worklog workstreams`

Lists all detected workstreams with their IDs, titles, status, and event count. Use IDs shown here as arguments to `resume`.

```bash
python3 main.py workstreams
```

---

### `worklog events [--since N] [--type TYPE] [--workstream WS_ID]`

Shows raw events from the ledger for inspection. All filters are optional.

```bash
python3 main.py events                              # all events (up to 100)
python3 main.py events --type commit                # commits only
python3 main.py events --type checkpoint            # agent checkpoints only
python3 main.py events --since 3                    # last 3 days
python3 main.py events --workstream ws_49e344b5f45fd71a  # one workstream
```

---

## Configuration

### `GITHUB_TOKEN` (environment variable)

Set to any GitHub personal access token or GITHUB_TOKEN from GitHub Actions to enable GitHub data collection during `sync`. Without it, only local Git data is collected.

```bash
export GITHUB_TOKEN=ghp_yourtoken
python3 main.py sync
```

### `.worklog.json` (optional, at repo root)

Override the auto-detected project ID:
```json
{
  "project_id": "my-custom-project-name"
}
```

---

## Workstream Correlation

Workstreams are detected automatically using four deterministic signals:

| Signal | Example | Confidence |
|--------|---------|-----------|
| Issue/PR reference in commit message | `Fixes #42` → `issue:42` workstream | high |
| Branch name (non-default branches) | `feature/csv-validation` commits grouped | high |
| File overlap within 7 days | Two commits touching `src/auth.py` | medium |
| Temporal proximity (< 2 hours) | Events within 2h of each other | low |

Events that match no signal are placed in an `uncorrelated` workstream.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `No git repository found` | Running from outside a repo | `cd` into the repo first |
| `GitHub: no GITHUB_TOKEN found` | Token not exported | `export GITHUB_TOKEN=...` |
| Resume shows stale warning | `sync` not run recently | Run `python3 main.py sync` |
| YAML parse error with `:` in alternatives | YAML interprets colon-space as dict | Quote the string: `"text: more"` |
| Checkpoint shows 0 events (dedup) | Already ingested this session | Expected behavior — no action needed |

---

## Running Tests

```bash
python3 -m pytest tests/ -v
```

Tests cover: ledger schema and deduplication, Git commit parsing, dirty-file detection, checkpoint YAML validation, workstream correlation signals, standup/resume/why view content, and freshness detection.

Expected: **62 tests, 0 failures**.

---

## Known Limitations

- Workstream correlation recorrelates all events on every sync; user-defined workstream names are not persisted (Future: workstream rename command)
- GitHub collection fetches only the most recent 30–50 items per endpoint; very active repos may have older events missed
- The `why` view uses exact substring matching; it does not perform fuzzy or semantic search
- DB path is always `~/.worklog/` (Future: `WORKLOG_DB_DIR` env var override)
