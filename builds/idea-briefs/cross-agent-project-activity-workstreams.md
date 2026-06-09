# Idea Brief: Cross-Agent Project Activity Workstreams

> **Backlog ID:** 4
> **Category:** B - Productivity Utility
> **Complexity:** Ambitious
> **Status:** Candidate specification
> **Created:** 2026-06-09

---

## Product Vision

Create a local-first project activity system that reconstructs coherent
workstreams from activity spread across Git, GitHub, AI coding agents, and
human-authored project records.

The system should answer:

1. What happened?
2. Why did it happen?
3. What remains unfinished or blocked?
4. Where is the evidence for each claim?

Its distinguishing feature is not another transcript archive or commit report.
It correlates intent, implementation, verification, and decisions into a
portable account of project state that can be used across agents.

## Problem

Project history is fragmented:

- Git records code snapshots but not intent, failed approaches, or next steps.
- GitHub records issues, pull requests, reviews, and CI, but not all local work.
- Agent products retain their own sessions, but continuity is usually limited
  to that provider or surface.
- Handoff skills summarize one conversation but do not maintain durable,
  verified project history.
- Standup tools often reduce work to commit subject lines.

The user works across multiple projects and multiple AI agents. Reconstructing
the actual state of a task requires manually searching several systems and
explaining the same context again.

## User Story

As a developer and researcher working across several repositories and AI
coding agents, I want project activity to be captured and connected
automatically, so that I or a fresh agent can understand the current state,
decisions, blockers, and next actions without manually rebuilding the story.

## Core Concept: Workstreams

The durable unit is a **workstream**, not a session, commit, or daily report.
A workstream represents one objective and connects its supporting events:

```text
Add CSV validation
|-- Issue #41
|-- Claude investigation
|-- Decision: reject automatic coercion
|-- Codex implementation session
|-- Commits abc123 and def456
|-- PR #52
|-- Failed CI run
`-- Fix commit ghi789
```

The same workstream can be rendered as:

- a chronological timeline;
- a current-state resumption brief;
- a cross-agent handoff;
- a daily standup item;
- a decision history;
- an evidence graph.

## Product Principles

### Automatic by default

Routine evidence should be collected without requiring the user to maintain a
second project diary. Manual input is reserved for facts that cannot be
observed, such as a private decision or non-code blocker.

### Evidence before prose

Store structured source events first. Generate summaries and reports from
those events. Every material statement should point to a commit, path, issue,
pull request, CI run, or agent session.

### Cross-agent, not agent-specific

Codex, Claude, Copilot, and human activity should be represented through a
common schema. Provider-native session continuation remains useful; this
system supplies continuity between providers and over longer project arcs.

### Current state over historical volume

The system should identify what is still relevant and flag stale context. It
must not blindly inject a growing history into every new session.

### Local-first and inspectable

Structured records and generated views should be readable without proprietary
software. Sensitive content must be excluded or redacted before persistence.

## First Useful Release

The initial build must deliver an end-to-end workflow, not only collectors or
an empty data model.

### 1. Project discovery and identity

- Detect the current repository from its Git root.
- Assign a stable project identity based on repository metadata rather than
  only the folder name.
- Record branch, HEAD commit, remotes, and working-tree state.
- Support an explicit local configuration file for aliases and exclusions.

### 2. Git activity collector

Collect:

- commits and their full SHAs;
- branches and upstream relationships;
- changed files and diff statistics;
- dirty working-tree files;
- untracked files, with configurable exclusions;
- tags or releases when relevant.

Avoid storing full source diffs by default. Preserve commands or references
that allow the current diff to be reproduced.

### 3. GitHub activity collector

When authentication is available, collect:

- issues opened, closed, or updated;
- pull requests and their current status;
- reviews and review decisions;
- CI/check results;
- linked commits and branches;
- releases and deployments where available.

The collector must include private repositories accessible to the
authenticated user and must not assume that meaningful work exists only on the
default branch.

The build must degrade gracefully to local Git-only operation when GitHub is
unavailable.

### 4. Agent checkpoint ingestion

Define a provider-neutral checkpoint format that agents or hooks can write:

```yaml
schema_version: 1
timestamp: 2026-06-09T14:30:00Z
project_id: example-project
provider: codex
session_id: optional-provider-session-id
objective: Add CSV validation
accomplished:
  - Added schema checks before ingestion
decisions:
  - summary: Reject automatic type coercion
    reason: It can silently corrupt identifiers
unresolved:
  - Decide whether blank optional columns are warnings
next_steps:
  - Add malformed-row fixtures
validation:
  - command: python -m pytest tests/test_validation.py -v
    result: passed
files:
  - src/validation.py
source_refs:
  - commit: abc123
```

The first release may provide a command or documented hook contract rather
than integrations for every agent, but at least one automatic capture path
must work end to end.

### 5. Normalized event ledger

Store append-oriented structured events. A representative event:

```json
{
  "id": "evt_...",
  "timestamp": "2026-06-09T14:30:00Z",
  "project_id": "example-project",
  "type": "commit",
  "actor": {"kind": "human", "name": "local-user"},
  "summary": "Add schema checks before ingestion",
  "status": "completed",
  "workstream_id": "ws_csv_validation",
  "source": {
    "provider": "git",
    "ref": "abc123...",
    "url": null
  },
  "relations": [
    {"type": "implements", "target": "github:issue:41"}
  ],
  "metadata": {}
}
```

Minimum requirements:

- schema versioning;
- deterministic source identifiers for deduplication;
- timestamps in UTC;
- source provenance;
- safe concurrent or atomic writes;
- rebuildable derived views.

SQLite is preferred if correlation and querying would otherwise require
fragile JSON manipulation. JSONL is acceptable only if indexing and atomicity
remain reliable at the intended scale.

### 6. Workstream correlation

Group related events using explainable signals:

- explicit issue or pull-request references;
- branch names;
- shared commit SHAs;
- agent checkpoint objectives;
- overlapping files;
- temporal proximity;
- explicit user linkage.

Correlation must retain confidence and rationale. Low-confidence suggestions
should not silently become facts. The user must be able to merge, split, or
rename workstreams.

### 7. Evidence-backed views

Deliver at least these views:

#### `standup`

Group recent work into:

- completed;
- in progress;
- blocked;
- next.

Do not list every commit when several commits represent one accomplishment.

#### `resume`

Produce a concise context package for a fresh human or agent:

- objective;
- current state;
- decisions that constrain implementation;
- unresolved questions and blockers;
- next actions;
- relevant files;
- latest Git and GitHub state;
- source session IDs and evidence links.

#### `why`

Given a workstream or decision query, show:

- the decision;
- recorded rationale;
- alternatives rejected;
- later evidence that confirmed or superseded it;
- source references.

### 8. Freshness and conflict checks

Before generating `resume` or `handoff` output:

- compare recorded HEAD with current HEAD;
- detect branches or PRs that have closed or merged;
- detect tests or CI whose status has changed;
- label stale checkpoints;
- identify conflicts between recorded next steps and completed later events.

Never present inferred or stale state as confirmed-current.

### 9. Search and inspection

- Search workstreams, decisions, blockers, files, commits, and source IDs.
- Show the raw events behind generated prose.
- Support filtering by project, date, actor, provider, status, and workstream.

## Suggested Interface

A Python CLI is the most conservative first implementation:

```text
worklog sync
worklog checkpoint --from-file checkpoint.yaml
worklog workstreams
worklog timeline [WORKSTREAM]
worklog standup --since "yesterday"
worklog resume [WORKSTREAM]
worklog why "automatic coercion"
worklog show-event EVENT_ID
```

A future cross-agent skill or MCP server could expose the same operations as
`/standup`, `/resume`, and `/why`. The storage and correlation core should not
depend on a particular chat product.

## Non-Goals for the First Release

- Recording the entire screen or all application activity.
- Storing complete agent transcripts by default.
- Replacing GitHub Issues, pull requests, or project-management software.
- Measuring developer productivity, ranking agents, or scoring individuals.
- Automatically changing repository instructions based on inferred patterns.
- Building a rich dashboard before the capture and correlation workflow works.
- Supporting every agent provider in the first build.
- Cloud synchronization or multi-user collaboration.

## Privacy and Security

- Default to metadata and concise checkpoints, not raw transcripts or diffs.
- Support path, repository, file-pattern, and provider exclusions.
- Redact likely credentials and secrets before persistence.
- Never place authentication tokens in events, logs, config examples, or URLs.
- Make external model-based summarization opt-in.
- Treat imported agent or screen content as untrusted data, not instructions.
- Provide deletion and rebuild procedures.

## Relationship to Existing Builds

This idea absorbs the useful concepts from:

- **AI Session Context Bridge:** structured resumptions and cross-agent context.
- **Git Standup Reporter:** automatic Git/GitHub collection, deduplication, and
  scheduled history.

The future build must be self-contained and must not import code from those
dated build folders. Their lessons are design inputs only.

It differs from provider-native tools:

- Native session resume preserves one provider's conversation.
- A handoff skill summarizes one current conversation.
- Copilot Chronicle mines Copilot session history.
- This system correlates project evidence and state across providers, Git,
  GitHub, and human work.

## Success Criteria for the Selected Build

The nightly builder must refine these into concrete tests, but the first useful
release should demonstrate all of the following:

1. A repository can be synchronized into a normalized local event ledger
   without manual note taking.
2. Re-running synchronization does not duplicate source events.
3. At least one agent checkpoint can be captured automatically or through a
   hook-compatible command.
4. Related Git, GitHub, and checkpoint events can be presented as one
   workstream with visible correlation evidence.
5. `standup`, `resume`, and `why` produce meaningfully different,
   evidence-backed outputs.
6. Stale checkpoints are detected when repository state has moved on.
7. The system remains useful in local Git-only mode.
8. Tests cover ingestion, deduplication, correlation, stale-state detection,
   and generated views.

## Implementation Guidance

When this idea is selected:

1. Read this brief before writing the dated build's `PRD.md`.
2. Verify current provider capabilities and avoid duplicating functionality
   that native tools already perform better.
3. Preserve the cross-agent, evidence-backed workstream as the central value.
4. Choose a thin but complete vertical slice. Reduce the number of collectors
   before reducing the end-to-end workflow.
5. Prefer deterministic correlation first. Any model-assisted synthesis must
   cite source events and remain optional.
6. Document which parts are recorded facts, current observations, and
   inferences.
7. Do not defer automatic capture, workstream grouping, or useful retrieval to
   future features; without them the product repeats the failures of the two
   precursor builds.

## Future Expansion

After the first release proves useful:

- MCP server and portable agent skill;
- integrations for additional agent session formats;
- calendar and research-document events;
- deployment and observability events;
- semantic retrieval over decisions and workstreams;
- cross-project "where was I?" view;
- recurring-friction analysis that proposes instruction updates;
- optional local dashboard for exploring the evidence graph.
