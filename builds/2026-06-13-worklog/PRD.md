# PRD — worklog: Cross-Agent Project Activity Workstreams

> **Build date:** 2026-06-13
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project
> **Day of week:** Saturday → Ambitious Project

---

## Goal

Build a local-first Python CLI (`worklog`) that collects Git and GitHub activity, ingests agent checkpoints, stores everything in a normalized SQLite event ledger, automatically groups related events into workstreams, and produces evidence-backed `standup`, `resume`, and `why` reports.

## User Story

As a developer and researcher working across several repositories and multiple AI coding agents, I want project activity to be captured and correlated automatically — from Git commits, GitHub PRs/issues, and agent session checkpoints — so that I or a fresh agent can understand the current state, decisions, and next actions without manually rebuilding the story.

## Scope

### In Scope

- **Project discovery:** Detect the current Git repository root; derive a stable project ID from remote URL or folder name; record HEAD, branch, remotes, and dirty-tree state.
- **Git collector:** Collect commits (SHA, author, timestamp, message, files changed, stats), current branch, tags, and dirty/untracked file list via `git` subprocess calls.
- **GitHub collector:** Collect issues (open/closed/updated), pull requests (state, linked commits, CI status), and releases via GitHub REST API using `GITHUB_TOKEN`; degrade gracefully when token is absent.
- **Agent checkpoint ingestion:** Accept a YAML checkpoint file (schema defined in PRD) and ingest it as structured events; support a `--from-stdin` mode for hook-compatible capture.
- **Normalized event ledger:** SQLite database at `~/.worklog/<project_id>.db`; schema-versioned; deterministic source IDs for deduplication; append-only event rows; atomic writes.
- **Workstream correlation:** Group events deterministically by: (a) issue/PR refs extracted from commit messages and checkpoint objectives, (b) branch name, (c) overlapping files within a 7-day window, (d) temporal proximity (< 2 hours). Retain confidence level and rationale per grouping.
- **`worklog standup [--since N]`**: Group recent events by workstream into done / in-progress / blocked / next; omit redundant commit lines when multiple commits serve one accomplishment.
- **`worklog resume [WORKSTREAM_ID]`**: Produce a concise context package — objective, current state, decisions, blockers, next steps, relevant files, latest Git/GitHub state, source refs.
- **`worklog why QUERY`**: Search decisions recorded in checkpoints by keyword; show decision, rationale, alternatives rejected, and source event IDs.
- **`worklog workstreams`**: List all detected workstreams with status and event count.
- **`worklog events [--workstream W] [--since N] [--type T]`**: Show raw events with provenance.
- **Freshness checks:** Before generating `resume`, compare recorded HEAD against current HEAD; flag stale checkpoints where HEAD or branch has moved on; never present stale state as confirmed-current.
- **Local Git-only mode:** All features except GitHub data work without a GITHUB_TOKEN.

### Out of Scope

- Rich dashboard UI (deferred to FutureFeatures)
- Multiple agent provider-specific integrations (checkpoint YAML format is the single capture path)
- Cloud synchronization or multi-user collaboration
- Full diff storage (store stats only; record refs needed to reproduce diffs)
- Automatic workstream merge/split via user commands (auto-detection only tonight)
- Semantic/LLM-assisted summarization (deterministic only)
- Calendar and research-document event sources
- Performance tuning for repositories with >10,000 commits (reasonable defaults)

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** `pyyaml` (checkpoint YAML parsing), `pytest` (tests); all else stdlib
- **Runtime requirement:** `python3 main.py <command> [args]` from the build folder; `pip install -r requirements.txt` once

## Data Structure

### Event ledger schema (SQLite)

```sql
CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT);

CREATE TABLE events (
    id TEXT PRIMARY KEY,           -- deterministic: sha256(provider:ref:type)
    timestamp TEXT NOT NULL,       -- UTC ISO-8601
    project_id TEXT NOT NULL,
    type TEXT NOT NULL,            -- commit | issue | pull_request | checkpoint | release | dirty_file
    actor_kind TEXT,               -- human | agent | ci | unknown
    actor_name TEXT,
    summary TEXT,
    status TEXT,                   -- completed | open | closed | merged | failed | stale
    workstream_id TEXT,
    provider TEXT NOT NULL,        -- git | github | agent
    source_ref TEXT,               -- SHA, issue number, session ID, etc.
    source_url TEXT,
    metadata TEXT                  -- JSON blob for type-specific fields
);

CREATE TABLE workstreams (
    id TEXT PRIMARY KEY,           -- deterministic slug
    title TEXT,
    status TEXT,                   -- active | stale | closed
    created_at TEXT,
    updated_at TEXT,
    evidence TEXT                  -- JSON: list of {signal, value, confidence}
);

CREATE TABLE decisions (
    id TEXT PRIMARY KEY,
    event_id TEXT,
    workstream_id TEXT,
    summary TEXT,
    reason TEXT,
    alternatives TEXT,             -- JSON list
    timestamp TEXT
);
```

### Agent checkpoint YAML format

```yaml
schema_version: 1
timestamp: 2026-06-13T14:30:00Z  # UTC ISO-8601
project_id: my-project            # optional; inferred from git root if absent
provider: claude                  # claude | codex | copilot | human
session_id: optional-id
objective: "Add CSV validation"
accomplished:
  - "Added schema checks before ingestion"
decisions:
  - summary: "Reject automatic type coercion"
    reason: "Can silently corrupt identifiers"
    alternatives:
      - "Coerce to inferred type (rejected: data loss risk)"
unresolved:
  - "Decide whether blank optional columns are warnings"
next_steps:
  - "Add malformed-row fixtures"
validation:
  - command: "python -m pytest tests/ -v"
    result: passed
files:
  - src/validation.py
source_refs:
  - commit: abc123
```

## Folder Structure

```
builds/2026-06-13-worklog/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py                        # entry point: python3 main.py <cmd>
├── src/
│   ├── __init__.py
│   ├── config.py                  # project identity, DB path resolution
│   ├── ledger.py                  # SQLite schema, insert_event, dedup, query
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── git.py                 # subprocess git → events
│   │   └── github.py              # REST API → events, graceful degradation
│   ├── checkpoint.py              # YAML checkpoint → events + decisions
│   ├── correlation.py             # workstream detection and grouping
│   ├── freshness.py               # stale checkpoint detection
│   └── views.py                   # standup, resume, why renderers
└── tests/
    ├── test_ledger.py
    ├── test_collectors_git.py
    ├── test_checkpoint.py
    ├── test_correlation.py
    └── test_views.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Ledger: schema creation, event insert, deduplication (same source ref = no duplicate), query by workstream, query by type, query by since-date
  - Git collector: commit parsing from `git log` output, dirty file detection, branch resolution (tested against the live repo in the build environment; isolated via temp repo for unit tests)
  - Checkpoint: valid YAML parsed to events + decisions, missing fields handled, invalid schema version rejected, decisions stored correctly
  - Correlation: issue ref extraction from commit messages, branch-name grouping, workstream assignment, confidence level stored
  - Views: standup output contains done/in-progress/blocked/next sections, resume includes decisions and next steps, why query returns matching decisions with evidence, freshness flag raised when HEAD has changed
  - Freshness: stale detection when stored HEAD != current HEAD

## Success Criteria

1. All tests pass (zero failures, ≥ 15 tests)
2. `python3 main.py sync` runs against the current nightly-builds repo without error and stores ≥ 1 commit event in the SQLite ledger
3. `python3 main.py checkpoint --file sample.yaml` ingests a YAML checkpoint, stores a checkpoint event, and stores ≥ 1 decision row — re-running produces 0 new rows (deduplication)
4. `python3 main.py standup` and `python3 main.py resume` produce non-empty, different outputs referencing source evidence (commit SHAs or event IDs)
5. `python3 main.py resume` emits a freshness warning when the stored HEAD in the ledger does not match the current repo HEAD (confirmed by manually advancing HEAD or injecting a stale record)

---

## Idea Brief Traceability

**Brief path:** `builds/idea-briefs/cross-agent-project-activity-workstreams.md`

**Capabilities included in this build:**
- Project discovery (§1)
- Git activity collector (§2)
- GitHub activity collector (§3) with graceful degradation
- Agent checkpoint ingestion (§4), YAML format
- Normalized event ledger with deduplication (§5), SQLite
- Workstream correlation — deterministic signals only (§6)
- `standup`, `resume`, `why` views (§7)
- Freshness and stale-state detection (§8)
- Basic event inspection and workstream listing (§9, simplified)

**Capabilities intentionally deferred:**
- User-controlled workstream merge/split commands (§6 — auto-detection only)
- Rich search across all event fields (§9 — basic filtering only)
- MCP server packaging (Future Expansion §1)
- Multiple agent provider-native integrations beyond YAML checkpoint (Future Expansion §2)
- Cross-project "where was I?" view

**Changed assumptions:**
- Checkpoint capture is manual (write a YAML file) rather than automatic hook for this build. A hook-compatible stdin mode is included so a future Claude Code Hook can pipe directly to `worklog checkpoint --from-stdin` without code changes.
- Workstream correlation uses only deterministic signals; no LLM-assisted clustering (keeps the build self-contained and fast).
