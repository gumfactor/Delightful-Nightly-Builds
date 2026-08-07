# PRD — Waymark

> **Build date:** 2026-08-07
> **Category:** C — Personal Knowledge Tool
> **Complexity:** Ambitious Project
> **Day of week:** Friday

---

## Goal

Waymark mines git commit history across the user's own local repositories into a single, searchable, cross-project knowledge base of *decisions* — the "why" behind changes — without requiring any manual note-taking.

## User Story

As a mid-career researcher and solo founder who runs many simultaneous software projects with AI-assisted coding and constantly loses context between sessions, I want a tool that automatically extracts and indexes the meaningful decisions buried in my git history across all my repos, so that I can search "what did we decide about X and why" months later instead of re-reading diffs or reconstructing context from scratch.

## Scope

### In Scope
- `index` command: point at a local git repo path, walk its full commit history via `git log`, incrementally store new commits (by hash, skip already-indexed) into a local SQLite database
- Deterministic decision-worthiness scorer: rates every commit 0–10 based on conventional-commit type, message body length/keywords ("because", "switch to", "migrate", "revert", "workaround", "breaking"), and change size (files/insertions/deletions) — pure function, fully unit-testable
- Deterministic fallback summary generator: always produces a one-line plain-English decision summary from commit metadata, with zero network calls
- Optional AI enrichment (`enrich` command): if `ANTHROPIC_API_KEY` is set at runtime, calls Claude Haiku to rewrite the summary for high-scoring commits into a clearer "what changed and why" sentence using the commit message/body/file list (never full diff content). Zero network calls when the key is absent — deterministic fallback is used unconditionally in that case
- `search` command: full-text-ish ranked search across summaries, messages, and tags, filterable by repo label, tag, and date, printed as a table
- `render` command: builds a single self-contained, dark-mode HTML dashboard — cross-repo timeline, live client-side search/filter (by repo, tag, min decision score), click-to-expand commit detail — from the SQLite data, with no external network calls at render or view time
- `list-repos` command: shows every indexed repo, commit count, decision-worthy count, and last-indexed timestamp
- Multi-repo aggregation: one shared database can hold commits from many repos, each identified by a user-supplied label
- Local SQLite storage, path configurable via `--db` (defaults to `~/.waymark/waymark.db` so it persists across projects, matching the tool's cross-project purpose)

### Out of Scope
- GitHub PR/issue enrichment via the GitHub API (noted in FutureFeatures.md)
- Editing/annotating commits with manual notes (this build's whole point is *zero* manual entry; a future build could add optional annotation)
- Semantic/embedding-based search (deterministic keyword ranking only tonight)
- Watching repos for live changes / background daemon — this is an on-demand CLI
- Any change to the repos it indexes (strictly read-only via `git log`; never writes to a target repo)

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `subprocess`, `argparse`, `json`, `re`, `urllib`, `html`, `datetime`, `pathlib`) — Anthropic API called directly via `urllib`, no `anthropic` package dependency
- **Runtime requirement:** `python3 main.py <command> ...` — no install step, no external services required for core functionality

## Data Structure

SQLite database (default `~/.waymark/waymark.db`, overridable with `--db`):

```sql
CREATE TABLE repos (
    label TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    last_indexed_at TEXT
);

CREATE TABLE commits (
    repo_label TEXT NOT NULL,
    commit_hash TEXT NOT NULL,
    author TEXT,
    committed_at TEXT,
    subject TEXT,
    body TEXT,
    files_changed INTEGER,
    insertions INTEGER,
    deletions INTEGER,
    decision_score INTEGER,
    tags TEXT,              -- JSON array, heuristically extracted
    summary TEXT,            -- deterministic fallback, always present
    ai_summary TEXT,         -- nullable, only set by `enrich`
    PRIMARY KEY (repo_label, commit_hash),
    FOREIGN KEY (repo_label) REFERENCES repos(label)
);
```

`render` reads this table and embeds it as a JSON payload inside a static HTML file for client-side search/filter — no server, no external calls at view time.

## Folder Structure

```
builds/2026-08-07-waymark/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── db.py
│   ├── git_reader.py
│   ├── scorer.py
│   ├── enrich.py
│   ├── render.py
│   └── cli.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_scorer.py
    ├── test_db.py
    ├── test_git_reader.py
    ├── test_enrich.py
    ├── test_render.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Decision scorer: conventional-commit type weighting, keyword detection, size-based scoring, edge cases (empty body, merge commits, huge diffs)
  - Deterministic summary generation: correct fallback text for various commit shapes
  - Git reader: parses real `git log` output from a temporary git repo created in a pytest fixture (real git, not mocked — git is a local tool, not an external network API); handles empty repos, single commits, non-git directories (error case)
  - DB layer: schema creation, incremental indexing (re-indexing a repo skips already-seen hashes), multi-repo isolation, search ranking/filtering
  - AI enrichment: mocked Anthropic HTTP calls only; verifies zero network calls when `ANTHROPIC_API_KEY` is unset (fallback used); verifies enrichment only targets un-enriched, high-scoring commits; handles API error gracefully by keeping the deterministic summary
  - HTML render: valid self-contained HTML produced, embedded JSON payload correctly escaped against script-injection in commit messages
  - CLI: argument parsing for each subcommand, error handling for a non-existent/non-git path

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. `index` correctly walks a real git repo's history, deterministically scores every commit, and re-running `index` on the same repo adds zero duplicate rows
3. `search` returns ranked, filterable results with no network calls
4. `render` produces a single self-contained dark-mode HTML file that is safe against injected script content in commit messages, browsable cross-repo, with no external network dependency at view time
5. `enrich` makes zero network calls when `ANTHROPIC_API_KEY` is unset and produces a usable AI-refined summary when it is set (verified via mock)

---

## Scope Changes

None — full scope as planned was delivered.
