# WhyThis.md — ci-pulse

## Selection method

**Lottery draw.** Roll: 20 (computed as (179×7 + 6×11) % 100 + 1). Lottery chance: 25% (R=0, no rated H ideas). 20 ≤ 25 → lottery fires.

Pool: 1 pending H-category idea (ID 9, GitHub Actions Performance Analyzer, rating blank = 5 tickets). Single entry wins by default.

## Why this idea is right for tonight

The last H build (dep-check, 2026-06-19) audited *external* Python dependencies. This build audits *CI pipeline performance* — a completely different problem and data source. The only surface-level overlap is "developer tool with HTML output."

GitHub's own UI shows you Actions runs per-repo per-workflow, but never:
- Aggregated across all your repos at once
- Trended over 30 days to show whether CI is getting faster or slower
- Ranked by improvement opportunity (duration × failure rate × frequency)
- Explained in plain English by an AI that knows which specific workflow is your worst bottleneck

The Anthropic API is the differentiating layer that turns raw aggregated metrics into actionable guidance. Without it, this is a decent dashboard; with it, the "CI Insights" section names the specific workflow you should optimize first and why.

## Why this approach won't score low

Previous low-scoring patterns to avoid:
- (a) Lack of visual interface → build ships a full Chart.js HTML dashboard (3 chart types + sortable table)
- (b) Mock data instead of live API → uses `GITHUB_TOKEN` to fetch real workflow run history from the user's actual repos
- (c) Duplicates existing tools → GitHub has no cross-repo CI aggregator with trend analysis; the AI insights layer is unique

The Qualtrics Survey Data Inspector (9/10) is the reference build: a specific, real pain point, specialized parsing of an awkward data format, research-quality derived metrics, and clear output. This build follows the same pattern: a specific developer pain point (understanding CI performance), specialized aggregation across the GitHub API, and meaningful derived metrics (avg duration, p95, failure rate, trend, improvement opportunity score).

## GitHub saturation check

Last 10 builds include 3 GitHub-adjacent builds (Dev Activity Explorer, Repository Health Scorecard, Morning Briefing). However:
- None of those touched the GitHub Actions API
- The data domain is different (CI performance vs commit patterns vs repo health)
- The audience use case is different (CI optimization vs daily digest vs health overview)

Proceeding with confidence that domain diversity is maintained.
