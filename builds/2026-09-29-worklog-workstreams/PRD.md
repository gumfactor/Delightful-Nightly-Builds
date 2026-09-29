# PRD — worklog: Cross-Agent Project Activity Workstreams

> **Build date:** 2026-09-29
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project
> **Idea Brief:** `builds/idea-briefs/cross-agent-project-activity-workstreams.md` (backlog #4)

## Goal

A local-first Python CLI that syncs Git, GitHub and AI-agent checkpoints into a SQLite event ledger, correlates them into evidence-backed workstreams, and renders `standup`, `resume` and `why` views with freshness checks.

## User Story

As a researcher/founder juggling many repos and several AI coding agents, I want project activity captured automatically and grouped by objective, so that I or a fresh agent can see current state, decisions, blockers and next steps — each with evidence — without re-explaining context.

## Idea Brief Traceability

| Brief requirement | Where satisfied |
|---|---|
| 1 Project discovery/identity | `project.py` (remote-hash identity, `.worklog.json` aliases/exclusions) |
| 2 Git collector | `gitcollect.py` (commits, numstat, branches/upstream, dirty/untracked, tags) |
| 3 GitHub collector | `ghcollect.py` (issues, PRs, reviews, check runs; degrades to Git-only) |
| 4 Agent checkpoints | `checkpoint.py` (JSON/YAML) + `hook.py` (automatic Claude Code hook capture from the session transcript) |
| 5 Event ledger | `ledger.py` (SQLite, schema_version, deterministic IDs, WAL, transactions) |
| 6 Correlation | `correlate.py` (strong keys + weighted weak signals, rationale, merge/split/rename overrides) |
| 7 Views | `views.py` (`standup`, `resume`, `why`, `timeline`) |
| 8 Freshness | `freshness.py` |
| 9 Search/inspection | `search`, `show-event`, filters in `cli.py` |
| Privacy | `redact.py`; no transcripts or diffs stored; no model calls |

Deviations: no model-assisted summarisation (brief marks it optional). Only Claude Code has an automatic capture path (hook); other agents use `checkpoint --from-file`. Skill/MCP packaging is deferred (brief's "Future Expansion").

## Scope

### In Scope
- Commands: `sync`, `checkpoint`, `hook`, `note`, `workstreams`, `timeline`, `standup`, `resume`, `why`, `search`, `show-event`, `merge`, `split`, `rename`, `resolve`, `purge`
- Facts vs observations vs inferences labelled in views
- Secret redaction before persistence
- Idempotent sync

### Out of Scope
- Dashboard, MCP server, transcript archiving, cloud sync, LLM calls, non-Claude transcript parsers

## Tech Stack

- **Language:** Python 3.11+
- **Dependencies:** stdlib only at runtime; `pyyaml` optional (YAML checkpoints; JSON always works); `pytest` for tests
- **Runtime:** `./worklog <command>` (or `python -m worklog`) inside any git repo

## Data Structure

SQLite (`<git-dir>/worklog/ledger.db`, override with `WORKLOG_DB`): `meta`, `events(id PK, ts, project_id, type, actor_kind, actor_name, provider, summary, status, ref, url, keys JSON, files JSON, metadata JSON, ingested_at)`, `overrides(id, project_id, kind, payload JSON)`, `state(project_id, snapshot JSON, observed_at)`. Event ID = `evt_` + sha1(provider:type:ref)[:24]. Timestamps UTC `YYYY-MM-DDTHH:MM:SSZ`. Correlation keys: `sha:`, `gh:N`, `branch:`, `obj:`.

## Folder Structure

```
builds/2026-09-29-worklog-workstreams/
├── PRD.md WhyThis.md BUILD_LOG.md FutureFeatures.md Manual.md requirements.txt
├── worklog                      (wrapper script)
├── hooks/claude-settings-snippet.json
├── src/worklog/{__init__,__main__,cli,project,redact,ledger,gitcollect,ghcollect,checkpoint,hook,correlate,freshness,views}.py
└── tests/{conftest.py,test_redact.py,test_ledger.py,test_gitcollect.py,test_ghcollect.py,test_checkpoint_hook.py,test_correlate.py,test_freshness_views.py,test_cli_e2e.py}
```

## Testing Strategy

- **Framework:** pytest; `python -m pytest tests/ -v`
- Real temporary git repos; GitHub via an injected fake fetch; no live network or Anthropic calls.
- Covered: sync idempotency, dedup, strong/weak correlation and thresholds, overrides, redaction, checkpoint validation, hook transcript parsing, staleness, all three views, Git-only degradation, GitHub failure degradation, CLI end-to-end.

## Success Criteria

1. All tests pass (zero failures)
2. Re-running `sync` inserts zero new events
3. Git commits, a PR/issue and a checkpoint sharing a ref appear in one workstream with visible evidence
4. `standup`, `resume`, `why` give different evidence-cited output; stale checkpoints are flagged
5. Works with no GitHub access; secrets never persisted
