# PRD — Pipeline Pulse

> **Build date:** 2026-07-09
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Ambitious
> **Day of week:** Thursday

---

## Goal

A dark-mode HTML dashboard that reconciles `builds/index.md` against the actual git history of this repository to show, at a glance, which nightly builds have actually landed on `main` versus which are still sitting unreviewed in open branches/PRs, ranked by how long they've been waiting.

## User Story

As the operator of this nightly-build system — someone who runs many simultaneous projects and has explicitly named "managing many simultaneous projects" and "context loss between AI sessions" as recurring friction points — I want a single dashboard that tells me how much of my AI-generated nightly output has actually been merged versus abandoned in limbo, and which builds need my review most urgently, so that the backlog doesn't silently grow unbounded and good builds don't get lost.

This is not a hypothetical problem: a repo inspection performed while orienting for tonight's build found `main` is still at the `2026-06-18` build (Regex Dojo) while `builds/index.md` on the most recent open branch lists 32 completed builds through `2026-07-08` — meaning roughly three weeks of nightly builds (14+ separate branches) have never been merged.

## Scope

### In Scope
- Parse `builds/index.md`'s Full Catalog table into structured records (date, category, complexity, title, description, tech, status, rating, notes).
- Inspect the local git repository (read-only) to determine, for every build folder listed in the catalog, whether that folder exists in `origin/main`'s tree (merged) or only in another branch (unmerged/backlog).
- For unmerged builds: identify the originating remote branch (via `git diff --name-only` between main and each candidate branch) and compute backlog age in days using the build's own catalog date.
- Compute aggregate stats: total builds, merged count/%, backlog count/%, oldest unmerged build, rating coverage (% of merged builds rated), average rating, category distribution, complexity distribution, status distribution (complete/partial/aborted/discarded).
- Compute a rating trend over time (chronological list of rated builds).
- Optional AI-generated 2-4 sentence "what needs attention" briefing via the Anthropic API (Claude Haiku), summarizing backlog size, oldest stuck build, and rating coverage — with a deterministic template fallback when `ANTHROPIC_API_KEY` is not set or the call fails.
- Render a self-contained dark-mode HTML dashboard: hero stat tiles, a merged-vs-backlog doughnut chart, a rating-trend line chart, category and complexity bar charts, a sortable/searchable table of every build (with merged state and backlog age), and a "Needs Attention" panel listing the oldest unmerged builds with a clickable GitHub compare link (`.../compare/main...<branch>`) that resolves to the open PR if one exists.
- CLI entry point (`main.py`) with `--repo-path`, `--index-path`, `--owner`, `--repo`, `--output`, and `--no-ai` flags; auto-detects the git root and the `owner/repo` from `git remote get-url origin` when not passed explicitly.
- Text-mode summary printed to the terminal in addition to the HTML file (so the dashboard's key numbers are visible without opening a browser).

### Out of Scope
- Actually opening/merging PRs, posting comments, or writing to the GitHub API — this tool is read-only/observational.
- Fetching PR review state, CI status, or comment threads from the GitHub REST/GraphQL API — that requires authenticated API access this session's sandbox cannot reach reliably; branch/merge state is derived entirely from local git instead, which is fully reliable and requires no token.
- Automatically running `git fetch` on every invocation (would be a surprising network side effect for a read-only reporting tool) — an explicit `--fetch` flag runs `git fetch origin` first when the user wants fresh branch data.
- Editing `builds/index.md` or `builds/ideas.md` from within the tool.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None (stdlib only for logic; Chart.js 4.4.4 via CDN inside the generated HTML)
- **Dependencies:** stdlib only (`subprocess`, `re`, `json`, `urllib`, `datetime`, `argparse`, `html`). `pytest` for tests.
- **Runtime requirement:** `python3 src/main.py` run from anywhere inside the target git repo (or with `--repo-path`); opens the generated HTML file directly in a browser, no server needed.

## Data Structure

**Catalog record** (parsed from one `builds/index.md` table row):
```python
{
  "date": "2026-07-08",          # ISO date string
  "category": "I",               # single letter A-I
  "complexity": "ambitious",     # focused | solid | ambitious
  "title": "Ledger Lens",
  "description": "...",
  "tech": "...",
  "status": "complete",          # complete | partial | aborted | discarded
  "rating": 6,                   # int 1-10 or None
  "notes": "...",
}
```

**Build status record** (catalog record + git reconciliation):
```python
{
  ...catalog record fields...,
  "folder_prefix": "2026-07-08", # used to match against git tree entries
  "merged": False,
  "branch": "claude/cool-sagan-5axlxd",  # None if merged or no matching branch found
  "backlog_days": 1,             # None if merged
}
```

No persistent storage — the tool is stateless; every run re-derives everything from `builds/index.md` and the current git state.

## Folder Structure

```
builds/2026-07-09-pipeline-pulse/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── git_inspector.py
│   ├── catalog_parser.py
│   ├── pipeline_stats.py
│   ├── ai_brief.py
│   ├── report_html.py
│   └── main.py
├── tests/
│   ├── test_git_inspector.py
│   ├── test_catalog_parser.py
│   ├── test_pipeline_stats.py
│   ├── test_ai_brief.py
│   └── test_report_html.py
└── sample_index.md          (fixture used by tests)
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - `catalog_parser`: parses a well-formed table into records; handles blank rating (`—`) as `None`; handles a numeric rating; skips the header/separator rows; handles a table with only one data row; raises a clear error on a missing file.
  - `git_inspector`: `run_git` is fully injectable (a fake runner is passed in every test — no real subprocess/network calls in the test suite); `list_builds_folders_at_ref` parses `git ls-tree` output into a folder-name set; `folder_added_by_branch` parses `git diff --name-only` output and extracts the top-level `builds/<folder>` prefix; `is_folder_merged` returns True/False correctly against a fake merged-folder set; branch discovery returns `None` when no branch introduces a given folder (edge case — e.g. a build merged directly to main with no tracked branch).
  - `pipeline_stats`: merged/unmerged counts and percentages are correct on a mixed fixture; backlog age is computed correctly from a fixed "today" date injected into the function (no `datetime.now()` inside the tested logic); oldest-unmerged sorting is correct; rating coverage and average rating ignore `None` ratings; category/complexity/status distributions tally correctly; empty catalog does not crash and returns zeroed stats.
  - `ai_brief`: deterministic fallback template produces a non-empty string referencing backlog count and oldest build when no API key/fetch is available; when a fake successful API response is injected, its text is used verbatim; a fake failing/erroring API call falls back to the deterministic template without raising.
  - `report_html`: output contains no unescaped user-controlled HTML (title/notes text is escaped — regression test with a title containing `<script>`); output is valid enough to contain the expected hero numbers and chart data as embedded JSON; empty catalog still renders a valid (non-crashing) page.
  - End-to-end smoke test: running `main.py`'s core pipeline against the fixture repo/index end-to-end (parser → stats → HTML) produces a file with the correct total-build count baked in.

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests.
2. Running the tool against this actual repository correctly identifies that `main` is behind the catalog and reports a non-zero backlog count with the correct oldest-unmerged build.
3. The generated HTML dashboard opens standalone (no dev server) and renders hero stats, all four charts, the sortable table, and the "Needs Attention" list with working GitHub compare links.
4. The tool runs correctly with zero network access and zero `ANTHROPIC_API_KEY` (fully offline mode) via the deterministic AI-brief fallback — this is the mode this build was actually verified in, given this session's sandboxed egress policy.
5. No writes occur outside `builds/2026-07-09-pipeline-pulse/` by default, and no other build folder's source is imported or modified.

---

## Scope Changes

While probing this session's own network policy during orientation, direct calls to the GitHub REST API (even with `GITHUB_TOKEN` set) returned `403 GitHub access is not enabled for this session` — the env var present here is a proxy placeholder, not a usable PAT, and the broader "GITHUB_TOKEN is always available" assumption in PROFILE.md/CLAUDE.md does not hold inside this particular sandboxed session (only `api.github.com` via the pre-authorized `mcp__github__*` MCP tools, `pypi.org`, `raw.githubusercontent.com`, and `api.anthropic.com` — reachable but unauthenticated here — passed connectivity checks; `query1.finance.yahoo.com`, `api.open-meteo.com`, `www150.statcan.gc.ca`, `en.wikipedia.org`, `data.sec.gov`, and `eutils.ncbi.nlm.nih.gov` all returned `403` at the proxy).

Rather than build a tool whose core data path I could not exercise end-to-end tonight, I redesigned the data source around local `git` plumbing instead of the GitHub REST API — it answers the same "what's stuck unmerged" question using data this repository already has (its own git history), needs no token, and is something I *could* fully verify live tonight. The AI-briefing layer still uses the Anthropic API pattern established by prior builds (optional, deterministic fallback), consistent with the rest of the catalog, even though `ANTHROPIC_API_KEY` was not set in this session either.
