# PRD — gha-perf: GitHub Actions Performance Analyzer

> **Build date:** 2026-10-14
> **Category:** H — Developer Tool
> **Complexity:** Ambitious
> **Day of week:** Wednesday

## Goal

A Python CLI that pulls workflow runs, jobs and steps for all of a user's repos via the GitHub API and produces a self-contained HTML report showing where CI time, billable minutes and reliability are being lost, with concrete fix suggestions.

## User Story

As a solo founder and lab developer who maintains many repos with GitHub Actions, I want one report that shows slow steps, flaky workflows and wasted CI minutes across all repos, so that I can fix the biggest CI costs first without clicking through each repo's Actions tab.

## Idea Brief Traceability

Backlog idea #9 (no linked brief). Row text: fetch workflow run times across all repos; report slow steps, frequent failures, wasted CI minutes; trend charts; per-job breakdown. All covered in scope.

## Scope

### In Scope
- Fetch repos (`/user/repos`, or `--repos owner/name,...`), workflow runs in a `--days` window, and jobs/steps for a sampled number of runs per workflow
- Metrics per workflow: run count, success/failure/cancelled rates, p50/p95 wall-clock duration, billable minutes (OS multipliers Linux 1x, Windows 2x, macOS 10x, rounded up per job), wasted minutes (failed + cancelled runs)
- Flaky detection: same SHA fails then passes, or success on re-run attempt >1
- Slowest steps aggregate across runs (workflow / job / step)
- Weekly trend series (runs, failure rate, billable minutes)
- Rule-based findings with severity (slow dependency install, high failure rate, flaky, cancelled-run waste, expensive runners, high duration variance)
- Self-contained HTML report (Chart.js 4.4.4 pinned CDN, dark/light, mobile-friendly) plus JSON export
- Optional Claude summary when `ANTHROPIC_API_KEY` is set (`--ai`); degrades silently without it
- Rate-limit aware HTTP client with pagination; graceful per-repo failure

### Out of Scope
- Billing-API exact minutes; estimate used and labelled as estimate
- Modifying workflows or opening PRs
- Persistent cache between runs

## Tech Stack

- **Language:** Python 3.11
- **Dependencies:** stdlib only at runtime (urllib); pytest for tests; Chart.js via CDN in output
- **Runtime requirement:** `GITHUB_TOKEN=... python main.py --days 30 -o report.html`

## Data Structure

Run: id, repo, workflow name/path, event, branch, sha, attempt, conclusion, start, end. Job: run id, name, runner labels, start, end, steps[name, start, end, conclusion]. Analysis output is a plain dict (JSON-serialisable): `summary`, `workflows[]`, `steps[]`, `flaky[]`, `trend[]`, `repos[]`, `findings[]`.

## Folder Structure

```
builds/2026-10-14-gha-perf/
├── PRD.md  WhyThis.md  BUILD_LOG.md  FutureFeatures.md  Manual.md
├── main.py
├── requirements.txt
├── src/gha_perf/__init__.py
├── src/gha_perf/api.py        (HTTP client, pagination, rate limit)
├── src/gha_perf/collect.py    (fetch repos/runs/jobs into models)
├── src/gha_perf/models.py     (dataclasses, time parsing)
├── src/gha_perf/analyze.py    (metrics, flaky, trends, findings)
├── src/gha_perf/render.py     (HTML report)
├── src/gha_perf/ai.py         (optional Anthropic summary)
├── src/gha_perf/cli.py
└── tests/test_api.py test_analyze.py test_collect.py test_render.py test_cli.py
```

## Testing Strategy

pytest. All network is injected (`transport` callable) and mocked with fixtures; Anthropic calls mocked. Tests cover pagination, rate-limit error, time parsing, percentile, billing multipliers/rounding, wasted minutes, flaky detection, step aggregation, trend bucketing, finding rules, HTML escaping, CLI end-to-end with fake transport, AI fallback.

## Success Criteria

1. The CLI with a fake transport produces a valid self-contained HTML report and JSON.
2. Billable minutes, wasted minutes, p95 and flaky detection are verified by unit tests with hand-computed values.
3. A failure in one repo or a missing API key does not abort the run.
4. HTML output escapes all repo-controlled strings.
5. At least 15 tests pass.
