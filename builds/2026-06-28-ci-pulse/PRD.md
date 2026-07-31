# PRD — ci-pulse: GitHub Actions Performance Analyzer

## Goal

A Python CLI that fetches all GitHub Actions workflow runs across every repo the user owns, computes CI health metrics (avg duration, failure rate, trend), and renders a self-contained dark-mode HTML dashboard with interactive charts and an AI-generated bottleneck summary.

## User Story

As a developer with 15+ GitHub repos each running CI, I open ci-pulse each morning and immediately see which workflows are slow, which are failing most, and how my CI health has trended over the last 30 days — without clicking through each repo's Actions tab individually.

## Scope

### In
- Fetch all repos via `GITHUB_TOKEN`
- For each repo with recent GitHub Actions runs: fetch last 30 days of run history
- Compute per-workflow metrics: avg duration (seconds), p95 duration, failure rate, run count
- Compute global stats: total runs, total CI minutes burned, overall failure rate, # repos with CI
- 30-day trend: weekly grouped average duration and success rate
- HTML dashboard: 4 stat cards, top-10-slowest bar chart, 30-day trend line chart, failure-rate bar chart, per-workflow sortable table
- AI insights panel: 3–5 Claude Haiku bullet points naming specific bottlenecks and improvement paths
- Graceful fallback for missing `ANTHROPIC_API_KEY` (insights panel shows a note)
- `--days N` flag (default 30) to control lookback window
- `--output PATH` flag (default `ci-pulse-YYYY-MM-DD.html`)
- `--no-ai` flag to skip Claude call
- Terminal summary printed after HTML generation

### Out
- Step-level job timing (too many API calls; deferred to FutureFeatures)
- Self-hosted runner tracking
- PR-triggered vs push-triggered breakdown
- Automated scheduling / Routine packaging (noted in FutureFeatures)

## Tech Stack

- Python 3.8+, stdlib only at runtime (`urllib.request`, `urllib.parse`, `json`, `html`, `argparse`, `pathlib`, `datetime`, `os`, `sys`, `collections`, `statistics`)
- `anthropic>=0.52.0` for Claude Haiku AI insights (optional runtime dep — graceful fallback if absent or API key missing)
- Chart.js 4.4.4 via CDN for interactive charts
- `pytest` for tests

## Data Structure

### WorkflowRun (from GitHub API)

```python
{
    "id": int,
    "name": str,                  # workflow name
    "workflow_id": int,
    "status": str,                # "completed", "in_progress", "queued"
    "conclusion": str | None,     # "success", "failure", "cancelled", "skipped", None
    "created_at": str,            # ISO 8601
    "run_started_at": str | None, # ISO 8601 (may be absent, fall back to created_at)
    "updated_at": str,            # ISO 8601
    "head_branch": str,
    "event": str,                 # "push", "pull_request", "schedule", etc.
}
```

### WorkflowStats (computed)

```python
{
    "repo": str,
    "workflow_name": str,
    "total_runs": int,
    "success_count": int,
    "failure_count": int,
    "failure_rate": float,        # 0.0–1.0
    "avg_duration_s": float,
    "p95_duration_s": float,
    "durations": list[float],     # raw seconds, for trend use
}
```

### GlobalStats (computed)

```python
{
    "total_runs": int,
    "total_failures": int,
    "repos_with_ci": int,
    "total_ci_minutes": float,
    "overall_failure_rate": float,
    "slowest_workflow": str,
    "most_failed_workflow": str,
}
```

## Folder Structure

```
builds/2026-06-28-ci-pulse/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── main.py          ← CLI entry point and orchestration
│   ├── fetcher.py       ← GitHub API client (repos, runs)
│   ├── analyzer.py      ← Pure analysis functions (no I/O)
│   ├── renderer.py      ← Self-contained HTML generator
│   └── ai_insights.py   ← Anthropic API integration with fallback
└── tests/
    ├── test_analyzer.py ← 10 tests for analysis logic
    ├── test_fetcher.py  ← 5 tests for fetcher parsing
    └── test_renderer.py ← 5 tests for HTML output
```

## Testing Strategy

All tests use `pytest`. No live API calls in tests — GitHub API responses mocked with fixture dicts. Anthropic API stubbed with a mock that returns a canned response.

- `test_analyzer.py`: test pure functions with deterministic inputs; cover empty/edge cases
- `test_fetcher.py`: test response parsing and duration computation from timestamps; mock urllib at the urllib.request level
- `test_renderer.py`: test HTML output structure, XSS safety, and empty-state handling

## Success Criteria

1. **Real data**: The CLI successfully fetches workflow run data from at least one real GitHub repo via `GITHUB_TOKEN` and produces a non-empty HTML dashboard.
2. **Duration accuracy**: `compute_workflow_stats()` correctly computes avg and p95 duration from a list of run timestamps; verified by pytest.
3. **Failure rate**: Per-workflow failure rate (0.0–1.0) computed correctly from conclusion field; verified by pytest.
4. **HTML renders**: Output HTML opens in a browser without errors and displays Chart.js charts with real data.
5. **AI insights**: When `ANTHROPIC_API_KEY` is set, the dashboard includes an AI insights panel naming specific slow/flaky workflows; when the key is absent, the panel shows a graceful fallback message.

## Idea Brief Traceability

Selected from backlog (ID 9, added 2026-06-17). No Idea Brief linked — backlog description treated as spec intent. Build fulfils the core requirement: workflow run times across all repos, HTML report, trend charts, per-job breakdown at the run level (step-level breakdown deferred — per-job requires additional API calls that would be prohibitive at scale; deferred to FutureFeatures).
