# PRD — Worklog: Cross-Agent Project Activity Workstreams

> **Build date:** 2026-07-10
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious
> **Day of week:** Friday

---

## Goal

A local-first CLI that automatically correlates Git activity, GitHub issues/PRs, and AI-agent
work checkpoints into evidence-backed "workstreams," so a human or a fresh AI agent can answer
"what happened, why, what's left, and where's the proof?" without manually reconstructing the
story from three different tools.

## User Story

As a researcher and solo founder who runs multiple repositories and works with several AI
coding agents across sessions, I want project activity captured and connected automatically,
so that I or a fresh agent can understand current state, decisions, blockers, and next actions
without re-explaining context every session.

## Idea Brief Traceability

This build implements Backlog ID 4 ("Cross-Agent Project Activity Workstreams"), drawn from
`builds/ideas.md` via the nightly lottery (see `WhyThis.md`). The full specification is in
`builds/idea-briefs/cross-agent-project-activity-workstreams.md` and was read in full before
this PRD was written.

The brief explicitly names two precursor builds this must absorb and fix:
- **AI Session Context Bridge** (2026-06-06, rated 3/10) — failed because it required manual
  note-taking; this build makes Git/GitHub capture automatic and reserves manual input
  (checkpoints) for facts that genuinely cannot be observed.
- **Git Standup Reporter** (2026-06-07, unrated) — a one-shot report generator with no
  persistence or correlation; this build adds a durable, queryable event ledger and
  cross-source correlation on top of the same collection idea.

Per the brief's Implementation Guidance, this PRD takes a **thin but complete vertical slice**:
fewer collectors, but the full automatic-capture → normalize → correlate → evidence-backed-view
loop must work end to end. No dashboard, no multi-agent-provider integrations, no semantic
retrieval — those are explicitly out of scope for the first release per the brief itself.

## Scope

### In Scope
- **Project discovery**: identify the current repo (git root, GitHub `owner/repo` if a GitHub
  remote exists, else a stable path-hash id), record branch/HEAD/remotes/dirty state.
- **Git collector**: commits (with SHA, author, timestamp, subject, changed files, branch refs
  they're reachable from), branches (name + upstream), tags. Working-tree dirty/untracked files
  are captured as live *state* (in `sync_state`), not as historical ledger events — they are
  transient and not evidence of a discrete accomplishment.
- **GitHub collector**: issues and pull requests (title, state, merged flag, body, labels, URL)
  via the GitHub REST API using `GITHUB_TOKEN`, when the origin remote is a GitHub repo and a
  token is present. Degrades to git-only mode with a clear message otherwise. (Reviews and CI
  check-run ingestion are deferred — see Out of Scope.)
- **Agent checkpoint ingestion**: a provider-neutral JSON checkpoint format (matching the
  brief's YAML example structurally, JSON to stay dependency-free) ingested via
  `worklog checkpoint --from-file PATH`. Captures objective, accomplished items, decisions
  (with rationale), unresolved items, next steps, validation results, touched files, and a
  source commit reference.
- **Secret redaction**: checkpoint free-text fields are scanned for likely API keys/tokens
  before being written to the ledger.
- **Normalized SQLite event ledger**: append-oriented, deterministic per-event IDs for
  dedup-safe re-sync, schema-versioned, atomic writes.
- **Deterministic workstream correlation**: explicit checkpoint hint → issue/PR number
  reference → active branch → touched-file overlap with recent commits → dated general bucket
  (last resort, clearly labeled low-confidence). Every event's correlation records its signal
  and confidence rather than presenting a guess as fact.
- **Evidence-backed views**: `standup`, `resume`, `why`, `workstreams`, `timeline`,
  `show-event`, `search` — all reading from the ledger, never re-deriving from scratch.
- **Staleness detection**: `resume` compares the live repo HEAD/dirty state against what was
  recorded at last sync and flags drift; checkpoints whose recorded commit has been rebased
  past (no longer an ancestor of HEAD) are flagged stale.
- **Idempotent re-sync**: running `sync` twice produces zero duplicate events.

### Out of Scope (tonight)
- GitHub review and CI check-run ingestion (issues + PRs only for now).
- Any specific AI-agent provider integration beyond the generic checkpoint file contract (no
  Codex/Claude/Copilot session-log parsers).
- A rendered HTML/browser dashboard — Category B does not require a visual interface, and the
  brief itself says not to build a dashboard before the capture/correlation core works.
- Cloud sync, multi-user collaboration, or any persisted infrastructure.
- Model-assisted (Anthropic API) summarization — the brief requires deterministic correlation
  first, with AI synthesis optional and citation-bound; adding it tonight would be exactly the
  kind of premature-polish layer the brief warns against. Documented as a natural v2 addition
  in `FutureFeatures.md`.
- Fuzzy/semantic decision search in `why` (substring match only, case-insensitive).

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `subprocess`, `urllib.request`, `argparse`,
  `hashlib`, `json`, `re`, `dataclasses`) — zero third-party runtime dependencies, so the tool
  runs anywhere Python 3 is installed with no `pip install` step
- **Runtime requirement:** `python3 -m worklog <command>` run from (or pointed at, via `--repo`)
  any local git repository

## Data Structure

SQLite database at `<repo>/.worklog/ledger.db` (created on first `sync`; the tool documents
adding `.worklog/` to the target repo's `.gitignore`).

**`events`** — append-oriented ledger, one row per observed fact:
`id` (deterministic hex digest, PK), `project_id`, `timestamp` (UTC ISO-8601), `type`
(`commit`|`branch`|`tag`|`github_issue`|`github_pr`|`checkpoint`|`decision`), `actor_kind`
(`human`|`agent`), `actor_name`, `summary`, `status`, `workstream_id` (FK, nullable until
correlated), `source_provider` (`git`|`github`|`checkpoint`), `source_ref`, `source_url`,
`relations` (JSON array of `{type, target}`), `metadata` (JSON object), `correlation` (JSON
object: `{signal, confidence}`).

**`workstreams`**: `id` (PK), `project_id`, `title`, `created_at`, `updated_at`.

**`sync_state`**: `project_id`, `key`, `value` — last-synced HEAD SHA, dirty/untracked file
snapshot, last sync timestamp; used only for staleness comparisons, not historical evidence.

Checkpoint input file (JSON):
```json
{
  "schema_version": 1,
  "provider": "codex",
  "objective": "Add CSV validation",
  "accomplished": ["Added schema checks before ingestion"],
  "decisions": [{"summary": "Reject automatic type coercion", "reason": "Can silently corrupt identifiers"}],
  "unresolved": ["Decide whether blank optional columns are warnings"],
  "next_steps": ["Add malformed-row fixtures"],
  "validation": [{"command": "pytest tests/test_validation.py -v", "result": "passed"}],
  "files": ["src/validation.py"],
  "source_refs": [{"commit": "abc123"}]
}
```

## Folder Structure

```
builds/2026-07-10-worklog-cross-agent-workstreams/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt          (empty — stdlib only, documented)
├── sample_checkpoint.json    (example checkpoint a user/agent can adapt)
├── worklog/
│   ├── __init__.py
│   ├── __main__.py           (python -m worklog entry point)
│   ├── cli.py                (argparse command dispatch)
│   ├── util.py                (time/hash/slug/redaction helpers)
│   ├── project.py             (repo discovery + identity)
│   ├── ledger.py              (SQLite schema + CRUD + dedup)
│   ├── git_collector.py       (git subprocess collector)
│   ├── github_collector.py    (GitHub REST collector via urllib)
│   ├── checkpoint.py          (checkpoint schema validation + ingestion)
│   ├── correlate.py           (deterministic workstream correlation)
│   └── views.py               (standup/resume/why/timeline/workstreams/show-event/search)
└── tests/
    ├── conftest.py             (temp git repo fixture + helpers)
    ├── test_util.py
    ├── test_project.py
    ├── test_ledger.py
    ├── test_git_collector.py
    ├── test_github_collector.py
    ├── test_checkpoint.py
    ├── test_correlate.py
    ├── test_views.py
    └── test_cli_integration.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Project discovery on a real temp git repo (root, branch, HEAD, remote parsing incl.
    GitHub owner/repo extraction from both HTTPS and SSH remote URLs)
  - Git collector: commits, branches, tags against a temp repo built with real `git` commands
  - Ledger: schema creation, deterministic ID dedup (re-inserting the same event is a no-op),
    atomic write behavior, workstream upsert
  - GitHub collector: request construction and response parsing against a mocked
    `urllib.request.urlopen`, and graceful no-token / non-GitHub-remote fallback
  - Checkpoint: schema validation (required fields, defaults for optional fields), rejection
    of malformed input, secret redaction on free-text fields
  - Correlation: explicit hint wins over issue reference wins over branch wins over file
    overlap wins over dated general bucket; idempotent re-correlation
  - Views: `standup` grouping (completed/in progress/blocked/next), `resume` staleness
    detection (HEAD drift, rebased checkpoint), `why` decision search, `timeline` ordering
  - CLI integration: `sync` twice on the same repo produces zero duplicate events end-to-end;
    `checkpoint` ingestion end-to-end; error handling for a non-git directory

## Success Criteria

1. All tests pass (zero failures)
2. `worklog sync` on a real git repo populates the ledger with commits/branches/tags without
   any manual note-taking, and re-running it produces zero duplicate events
3. `worklog checkpoint --from-file` ingests at least one checkpoint end-to-end and its
   decisions are retrievable via `worklog why`
4. Git and checkpoint events referencing the same issue number or branch are correlated into
   one workstream, and `worklog workstreams` / `worklog timeline` show that correlation with
   its signal and confidence
5. `worklog resume` correctly flags a repo as stale when HEAD has moved since the last sync,
   and reports current state accurately when it hasn't
6. The tool remains fully functional in local-Git-only mode (no `GITHUB_TOKEN`, or a non-GitHub
   remote) with a clear, non-alarming message rather than an error

---

## Scope Changes

(none — see "Out of Scope" above for scope decided deliberately before implementation)
