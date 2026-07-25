# PRD — BugTrace: Personal Bug-Pattern Miner

> **Build date:** 2026-07-25
> **Category:** H — Developer Tool
> **Complexity:** Ambitious Project
> **Day of week:** Saturday

---

## Goal

A Python CLI that mines a developer's own git/GitHub commit history for bug-fix commits, classifies each fix into a recurring root-cause category (null handling, off-by-one, race condition, type mismatch, etc.) using deterministic keyword rules with an optional Claude Haiku second-opinion pass, and renders a persistent dashboard showing which mistake patterns recur most often across their own projects — a self-improvement feedback loop no existing linter or GitHub analytics tool provides.

## User Story

As an intermediate-to-advanced developer who codes daily with AI assistance across many simultaneous projects (research tooling, The Canada List, Kwyeter, this nightly-build repo) but isn't formally trained as a software engineer, I want to see which *kinds* of bugs I actually introduce and fix most often across all my repos, so that I can target my learning at my real, evidence-based weak spots instead of guessing.

## Scope

### In Scope
- `sync` command: fetch commits from one or more GitHub repos via `GITHUB_TOKEN` (or a local `--repo-path` git log fallback requiring no token), filter to "fix-like" commits via message heuristics (excludes merges/reverts), fetch each fix commit's diff.
- Deterministic keyword-based root-cause classifier (12-category taxonomy) — always available, works with zero configuration.
- Optional Claude Haiku classification pass (`--ai` flag) that re-classifies a capped batch of fix commits using the same taxonomy for a more nuanced read; any failure (no key, network error, malformed response, rate limit) falls back to the keyword classification for that commit — the tool is fully functional with no API key.
- Secret redaction pass on every diff excerpt before it is stored, displayed, or sent to any AI call (strips common credential/token patterns).
- Local SQLite persistence, deduplicated by `(repo, sha)` so re-running `sync` never double-counts or re-classifies a commit, and history accumulates across runs over time.
- `report` command producing three output formats from the accumulated data:
  - Terminal summary (category counts, top 3 patterns)
  - JSON export
  - Self-contained dark-mode HTML dashboard (Chart.js category-frequency bar chart + monthly trend line, per-category drill-down list linking to the commit on GitHub, client-side search/filter, an AI-or-template "coaching" paragraph on the top recurring patterns) — degrades gracefully to a text table if the Chart.js CDN is unreachable.
- `show <category>` command to list the underlying fix commits for one category in the terminal.
- CLI flags for scope control: `--repos`, `--since-months`, `--limit-per-repo`, `--ai`, `--ai-limit`, `--db`.

### Out of Scope
- JS/TS or non-Python/generic language-specific diff parsing beyond plain text — the classifier works on commit message + raw diff text for any language, but no language-aware AST analysis.
- Real-time/webhook-triggered classification (this is an on-demand CLI, not a Routine/Hook, matching the established pattern of prior H-category builds in this catalog).
- Multi-user / team analytics — this is a personal, single-token tool.
- Automatic PR comment posting or any write access to GitHub — read-only.

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`urllib.request` for GitHub + Anthropic HTTP calls, `sqlite3`, `argparse`, `re`, `json`, `subprocess` for the local git-log fallback, `dataclasses`, `pathlib`)
- **Runtime requirement:** `python3 main.py sync ...` then `python3 main.py report ...`; GITHUB_TOKEN and ANTHROPIC_API_KEY are both optional runtime environment variables (local `--repo-path` mode needs neither)

## Data Structure

SQLite table `fixes` (one row per classified fix commit, primary key prevents re-classification):

```sql
CREATE TABLE fixes (
    repo            TEXT NOT NULL,
    sha             TEXT NOT NULL,
    message         TEXT NOT NULL,
    author_date     TEXT NOT NULL,   -- ISO 8601
    category        TEXT NOT NULL,   -- one of the 12 taxonomy categories
    source          TEXT NOT NULL,   -- 'ai' or 'keyword'
    explanation     TEXT NOT NULL,   -- one-line rationale
    diff_excerpt    TEXT NOT NULL,   -- redacted, truncated
    PRIMARY KEY (repo, sha)
);
```

Fixed classification taxonomy (shared by keyword and AI classifiers, so results are directly comparable):
`null_none_handling`, `off_by_one_index`, `type_mismatch`, `async_race_condition`, `logic_operator_error`, `error_handling_missing`, `config_env_credentials`, `api_integration_misuse`, `dependency_version`, `typo_naming`, `test_only_fix`, `other`.

## Folder Structure

```
builds/2026-07-25-bugtrace/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── src/
│   ├── __init__.py
│   ├── fix_detector.py      # fix-like commit message heuristics
│   ├── redact.py             # secret redaction
│   ├── classify.py           # deterministic keyword taxonomy classifier
│   ├── ai_classify.py        # optional Claude Haiku classification + fallback
│   ├── github_client.py      # GitHub REST API via urllib (mocked in tests)
│   ├── local_git.py          # local `git log`/`git show` fallback (no token needed)
│   ├── store.py               # SQLite persistence + aggregation
│   ├── report_text.py        # terminal report
│   ├── report_html.py        # self-contained HTML dashboard
│   └── cli.py                 # argparse subcommands, wires everything together
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   └── sample_commits.json
    ├── test_fix_detector.py
    ├── test_redact.py
    ├── test_classify.py
    ├── test_ai_classify.py
    ├── test_github_client.py
    ├── test_local_git.py
    ├── test_store.py
    ├── test_report_text.py
    ├── test_report_html.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Fix-commit detection: positive keywords (fix, bug, patch, resolve, crash), negatives (merge commits, reverts, unrelated feature commits)
  - Secret redaction: API keys, bearer tokens, AWS-style keys, generic long hex/base64 secrets stripped; normal code untouched
  - Keyword classifier: one case per taxonomy category, plus the `other` fallback and priority-order tie-breaking
  - AI classifier: successful batch classification (mocked HTTP), malformed JSON response falls back to keyword, network error falls back to keyword, no API key skips AI entirely
  - GitHub client: paginated repo/commit listing (mocked), diff/patch retrieval (mocked), auth header construction, HTTP error handling — never a live network call
  - Local git fallback: parsing `git log` output from a real throwaway git repo created in a pytest tmp_path fixture (no network involved, safe to run for real)
  - SQLite store: dedupe on re-sync (same repo+sha not double counted or reclassified), aggregation math (per-category and per-month counts), empty-database edge case
  - Report generation: terminal summary formatting, JSON structure, HTML report contains expected category data and is safe against a script-injection payload in a commit message (asserts it lands as escaped text, not executed markup)
  - CLI: argument parsing for all subcommands and flags, end-to-end `sync` → `report` flow against a fully mocked/local backend

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. `sync` against a local git repo (no token required) correctly identifies fix-like commits, classifies them via the deterministic taxonomy, and persists them without duplication on a second run
3. `--ai` classification path is exercised in tests with a mocked Anthropic response and independently falls back cleanly to the keyword classifier on a simulated network error or malformed response
4. `report --format html` produces a self-contained dashboard file that renders correctly in headless Chromium with zero page errors, degrades gracefully with the Chart.js CDN blocked, and safely escapes a commit message containing an HTML/script injection payload
5. The tool runs end-to-end with zero configuration (no GITHUB_TOKEN, no ANTHROPIC_API_KEY) against a local repo path, using pure keyword classification

---

## Scope Changes

(none yet — filled in during build if scope changes)
