# FutureFeatures.md — ci-pulse

## 1. Per-job step-level timing

Currently uses run-level timestamps. Adding per-job fetches (`/actions/runs/{id}/jobs`) would surface which specific steps (install deps, test, build, deploy) consume the most time. The main cost is 1 extra API call per run, but sampling the 5 most-recent runs per workflow (rather than all) keeps it tractable. This would change "CI is slow" into "your `npm install` step is slow — consider caching node_modules."

## 2. Claude Code Routine packaging

Package ci-pulse as a Claude Code Routine that runs weekly and emails or Slacks the report. The user already has a Morning Briefing Routine; ci-pulse could be a Monday-morning CI health summary delivered automatically. Add a `--format json` flag so the Routine can pass structured data downstream.

## 3. Flakiness detection

Identify workflows whose failure rate is high but not consistently high — i.e., they fail in bursts, which suggests an environment issue rather than a code issue. Compute variance in the success/failure streak to distinguish "consistently bad" from "flaky." Flag flaky workflows differently in the dashboard with a separate badge color.

## 4. Workflow comparison across time windows

Add `--compare` mode: run the analysis for two time windows (e.g., last 30 days vs previous 30 days) and display a delta view — which workflows got faster, which got slower, which failure rate changed. This answers "did my recent CI changes help or hurt?"

## 5. Branch-level breakdowns

Currently aggregates across all branches. Add optional filtering by branch (`--branch main`) and a breakdown showing: main-branch runs vs PR runs vs scheduled runs. PR-triggered runs often have different performance characteristics and failure causes than pushes to main.

## 6. Cost estimation

If the user knows their GitHub Actions pricing tier (public free, private at $0.008/minute for Linux), add a `--cost-estimate` mode that projects monthly CI spend from the 30-day data. For private repos, "271 CI minutes = $2.17 this month" is actionable in a way that "271 minutes" alone isn't.

## 7. Export to CSV / JSON

Add `--format csv` and `--format json` for scripting and integration with spreadsheet tools. The per-workflow stats dict is already structured — this is purely an output format option.
