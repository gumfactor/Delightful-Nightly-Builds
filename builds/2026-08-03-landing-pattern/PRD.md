# PRD — Landing Pattern

> **Build date:** 2026-08-03
> **Category:** H — Developer Tool
> **Complexity:** Ambitious Project
> **Day of week:** Monday (per rotation: day-of-year 215 → category index 7 → H)

---

## Goal

A Python CLI that pulls every open pull request on a GitHub repo, works out which ones are actually safe to merge right now versus which are silently blocking each other or CI, and hands back a concrete merge order instead of a flat list.

## User Story

As a solo founder/researcher who runs many simultaneous GitHub-backed projects (including this very nightly-build repo) and can't review every open PR the moment it lands, I want a tool that tells me — across a whole backlog of open PRs — which ones are safe to merge immediately, which will conflict with each other if merged out of order, and which are stuck on CI or review, so that I can clear a stale PR backlog in one focused pass instead of opening each PR individually to guess its state.

## Scope

### In Scope
- `sync` command: authenticates with `GITHUB_TOKEN` (env var or `--token`), fetches all open PRs for a given `owner/repo` via the GitHub REST API (list PRs, per-PR detail for `mergeable`/`mergeable_state`, per-PR changed-file list, combined commit status for CI state), and stores a timestamped snapshot in a local SQLite database.
- Pure analysis engine (`landing_pattern/analysis.py`), independent of any network call:
  - Classifies every PR into exactly one readiness label: `ready`, `conflict` (dirty against base), `ci_failing`, `changes_requested`, `ci_pending`, `awaiting_review`, `behind_base`, `draft`, or `unknown`.
  - Builds a changed-file overlap graph across all open PRs — flags any pair of PRs that touch at least one of the same files.
  - Produces a recommended merge order in two batches: **Batch 1** (ready PRs with no file overlap with an earlier PR in the batch — safe to merge back-to-back, oldest first) and **Batch 2** (ready PRs that overlap a Batch-1 PR's files — safe only after rebasing, listed with which PR(s) they'll conflict with).
  - Everything else is grouped under **Blocked**, sorted by how actionable the blocker is (CI failure → changes requested → CI pending → awaiting review → behind base → unknown), then by age (oldest first). **Drafts** are listed last, separately.
- `report` command: reads the latest stored snapshot (or a specific `--run-id`) and renders it as `text` (terminal), `json`, or a self-contained dark-mode HTML dashboard — no CDN dependency, table + batch view only, opens directly via `file://`.
- `history` command: shows how a single PR's readiness label has changed across stored snapshots, so a repeatedly-blocked PR is visible as a trend, not just a one-time snapshot.
- Optional AI layer (`--ai` flag on `report`): for every PR in Blocked, calls Claude Haiku (`ANTHROPIC_API_KEY` from the environment, direct `urllib` HTTPS call, no SDK dependency) with only the PR's title, blocking label, changed-file count, and age — never diff content or file bodies — to generate a one-sentence plain-English "what to do about this" note. Falls back to a deterministic template sentence per label when no key is set or the call fails; the tool makes zero network calls to Anthropic without a key present.
- Local SQLite persistence (`landing_pattern.db`, created alongside wherever the tool is run) so repeated `sync` runs build real history instead of overwriting.

### Out of Scope
- Actually merging, closing, or commenting on PRs (read-only tool — deliberately does not touch repo state)
- Rebasing or resolving conflicts automatically
- Cross-repo aggregation in a single run (one `owner/repo` per invocation; can be scripted in a loop by the user)
- Analyzing PR review comment *content* (only review state: approved / changes requested / pending)

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None
- **Dependencies:** stdlib only (`urllib.request` for both GitHub and Anthropic HTTP calls, `sqlite3`, `argparse`, `json`, `datetime`)
- **Runtime requirement:** `python3 main.py sync --repo owner/name`, then `python3 main.py report --repo owner/name`. Requires `GITHUB_TOKEN` in the environment (already available in this build container and in the user's local shell via `gh auth` or a personal access token).

## Data Structure

Each stored snapshot row in SQLite:

```sql
CREATE TABLE syncs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo TEXT NOT NULL,
    synced_at TEXT NOT NULL,      -- ISO 8601 UTC
    report_json TEXT NOT NULL     -- full computed report: PRs + batches + blocked + drafts
);
CREATE INDEX idx_syncs_repo_time ON syncs(repo, synced_at);
```

The `report_json` blob is the output of `analysis.build_report(prs, now)` — a plain dict of:
```json
{
  "repo": "owner/name",
  "synced_at": "2026-08-03T12:00:00+00:00",
  "prs": [ {"number": 59, "title": "...", "label": "ready", "age_days": 1, "files": ["a.py"], "url": "..."} ],
  "batch1": [59, 58],
  "batch2": [{"number": 57, "conflicts_with": [59]}],
  "batch2": [{"number": 57, "age_days": 3, "conflicts_with": [59]}],
  "blocked": [{"number": 44, "label": "ci_failing", "age_days": 17}],
  "drafts": [12]
}
```

## Folder Structure

```
builds/2026-08-03-landing-pattern/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── main.py
├── landing_pattern/
│   ├── __init__.py
│   ├── github_client.py    (GitHub REST calls, injectable HTTP function for testing)
│   ├── analysis.py         (pure readiness/overlap/ordering logic — no I/O)
│   ├── ai_summary.py       (optional Claude Haiku call + deterministic fallback)
│   ├── storage.py          (SQLite snapshot persistence + history queries)
│   ├── report.py           (text / JSON / HTML rendering)
│   └── cli.py              (argparse entry points: sync / report / history)
└── tests/
    ├── __init__.py
    ├── test_analysis.py
    ├── test_github_client.py
    ├── test_storage.py
    ├── test_report.py
    ├── test_ai_summary.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Readiness classification for every label (`ready`, `conflict`, `ci_failing`, `changes_requested`, `ci_pending`, `awaiting_review`, `behind_base`, `draft`, `unknown`) from representative PR fixtures
  - File-overlap graph detection (no overlap, single overlap, multi-way overlap, empty file lists)
  - Merge-order batching: pure Batch 1 with no overlaps; a PR correctly demoted to Batch 2 when it overlaps an earlier Batch-1 PR; overlap demotion is transitive-safe (doesn't crash on a 3-way overlap chain)
  - Blocked-list sort order (CI failure before awaiting-review before behind-base; ties broken by age)
  - `github_client` functions against a mocked HTTP layer (no live network calls) — pagination across multiple pages, and a simulated 403/404 raising a clear error
  - `storage.py`: snapshot round-trip (write then read latest), `history()` returns snapshots in chronological order, empty-repo query returns an empty list rather than raising
  - `ai_summary.py`: deterministic fallback with no `ANTHROPIC_API_KEY`, mocked successful API call, mocked API failure falling back to the template
  - `report.py`: HTML output contains no unescaped PR title (XSS check with a `<script>` payload in a fixture PR title), JSON output round-trips through `json.loads`, text output is non-empty and includes every PR number
  - CLI: `sync` with a mocked GitHub client writes a snapshot; `report` with no prior snapshot exits with a clear error instead of a traceback

## Success Criteria

1. All tests pass (zero failures)
2. Given a fixture set of PRs with deliberately overlapping changed files, the tool correctly splits them into Batch 1 / Batch 2 with the right overlap reasoning, verified by both a unit test and a manual run against this repo's own real (31+) open PRs
3. Every non-`ready`, non-`draft` PR in Blocked shows a specific, correct blocking label (not a generic "not ready")
4. The HTML report opens directly via `file://` with zero console errors and correctly escapes a `<script>`-payload PR title
5. Running `sync` twice against the same repo produces two distinct history rows (not an overwrite), and `history --pr N` shows both

---

## Scope Changes

None — full scope as planned was delivered.
