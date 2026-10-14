"""Turn raw runs into metrics, flaky detection, step rankings, trends and findings."""
from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

from .models import Job, Run

RUNNER_MULTIPLIER = {"linux": 1, "windows": 2, "macos": 10}
INSTALL_PATTERN = re.compile(r"\b(install|npm ci|pip|poetry|bundle|yarn|pnpm|restore|flutter pub)", re.I)
CACHE_PATTERN = re.compile(r"cache|setup-(python|node|java)", re.I)
BORING_STEPS = {"Set up job", "Complete job", "Post Run actions/checkout@v4", "Run actions/checkout@v4"}

FAIL_RATE_WARN = 0.30
CANCEL_RATE_WARN = 0.25
VARIANCE_RATIO_WARN = 3.0
SLOW_INSTALL_SECONDS = 60


def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (pct in 0-100); 0.0 for empty input."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct / 100
    low, high = math.floor(rank), math.ceil(rank)
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def runner_multiplier(labels: list[str]) -> int:
    joined = " ".join(labels).lower()
    for key in ("macos", "windows"):
        if key in joined:
            return RUNNER_MULTIPLIER[key]
    return RUNNER_MULTIPLIER["linux"]


def job_billable_minutes(job: Job) -> int:
    """GitHub bills each job rounded up to a whole minute, times the runner multiplier."""
    if job.seconds <= 0:
        return 0
    return math.ceil(job.seconds / 60) * runner_multiplier(job.labels)


def _is_waste(run: Run) -> bool:
    return run.conclusion in ("failure", "cancelled", "timed_out")


def estimate_run_minutes(runs: list[Run]) -> dict[int, float]:
    """Billable minutes per run id: exact where jobs were fetched, otherwise the
    workflow's sampled average (or wall-clock minutes at 1x when nothing was sampled)."""
    exact: dict[int, float] = {run.id: float(sum(job_billable_minutes(j) for j in run.jobs)) for run in runs if run.jobs}
    sampled: dict[tuple[str, str], list[float]] = defaultdict(list)
    for run in runs:
        if run.id in exact:
            sampled[(run.repo, run.workflow)].append(exact[run.id])
    result = dict(exact)
    for run in runs:
        if run.id not in result:
            known = sampled.get((run.repo, run.workflow))
            result[run.id] = mean(known) if known else float(math.ceil(run.seconds / 60))
    return result


def find_flaky(runs: list[Run]) -> list[dict]:
    """Same SHA failed then later succeeded, or succeeded only on a re-run attempt."""
    by_sha: dict[tuple[str, str, str], list[Run]] = defaultdict(list)
    for run in runs:
        by_sha[(run.repo, run.workflow, run.sha)].append(run)
    flaky: dict[tuple[str, str], dict] = {}
    for (repo, workflow, _sha), group in by_sha.items():
        failed = any(r.conclusion == "failure" for r in group)
        passed = any(r.conclusion == "success" for r in group)
        rerun_pass = any(r.conclusion == "success" and r.attempt > 1 for r in group)
        if (failed and passed) or rerun_pass:
            entry = flaky.setdefault((repo, workflow), {"repo": repo, "workflow": workflow, "incidents": 0, "examples": []})
            entry["incidents"] += 1
            if len(entry["examples"]) < 3:
                entry["examples"].append(group[0].url)
    return sorted(flaky.values(), key=lambda e: -e["incidents"])


def aggregate_steps(runs: list[Run]) -> list[dict]:
    buckets: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for run in runs:
        for job in run.jobs:
            for step in job.steps:
                if step.name in BORING_STEPS or step.conclusion in ("skipped", None):
                    continue
                buckets[(run.repo, run.workflow, job.name, step.name)].append(step.seconds)
    rows = [
        {
            "repo": repo, "workflow": workflow, "job": job, "step": step,
            "count": len(secs), "mean_s": round(mean(secs), 1), "max_s": round(max(secs), 1),
            "total_s": round(sum(secs), 1),
        }
        for (repo, workflow, job, step), secs in buckets.items()
    ]
    return sorted(rows, key=lambda r: -r["total_s"])


def weekly_trend(runs: list[Run], minutes: dict[int, float], now: datetime, weeks: int) -> list[dict]:
    """Buckets are 7-day windows ending at ``now``; oldest first."""
    buckets = [{"week_start": (now - timedelta(days=7 * (i + 1))).strftime("%Y-%m-%d"), "runs": 0, "failed": 0, "minutes": 0.0}
               for i in range(weeks)][::-1]
    for run in runs:
        if run.started is None:
            continue
        age_weeks = int((now - run.started).total_seconds() // (7 * 86400))
        if not 0 <= age_weeks < weeks:
            continue
        bucket = buckets[weeks - 1 - age_weeks]
        bucket["runs"] += 1
        bucket["failed"] += run.conclusion == "failure"
        bucket["minutes"] += minutes[run.id]
    for bucket in buckets:
        bucket["fail_rate"] = round(bucket["failed"] / bucket["runs"], 3) if bucket["runs"] else 0.0
        bucket["minutes"] = round(bucket["minutes"], 1)
    return buckets


def _workflow_rows(runs: list[Run], minutes: dict[int, float], flaky: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[Run]] = defaultdict(list)
    for run in runs:
        groups[(run.repo, run.workflow)].append(run)
    flaky_counts = {(f["repo"], f["workflow"]): f["incidents"] for f in flaky}
    rows = []
    for (repo, workflow), group in groups.items():
        durations = [r.seconds for r in group if r.seconds > 0]
        total = len(group)
        failures = sum(r.conclusion == "failure" for r in group)
        cancelled = sum(r.conclusion == "cancelled" for r in group)
        rows.append({
            "repo": repo, "workflow": workflow, "runs": total,
            "success": sum(r.conclusion == "success" for r in group),
            "failure": failures, "cancelled": cancelled,
            "fail_rate": round(failures / total, 3), "cancel_rate": round(cancelled / total, 3),
            "p50_s": round(percentile(durations, 50), 1), "p95_s": round(percentile(durations, 95), 1),
            "billable_min": round(sum(minutes[r.id] for r in group), 1),
            "wasted_min": round(sum(minutes[r.id] for r in group if _is_waste(r)), 1),
            "flaky_incidents": flaky_counts.get((repo, workflow), 0),
            "sampled_jobs": sum(1 for r in group if r.jobs),
            "events": sorted({r.event for r in group}),
        })
    return sorted(rows, key=lambda r: -r["billable_min"])


def _runner_label_cost(runs: list[Run]) -> dict[tuple[str, str], int]:
    """Billable minutes spent on 2x/10x runners, per (repo, workflow)."""
    expensive: dict[tuple[str, str], int] = defaultdict(int)
    for run in runs:
        for job in run.jobs:
            if runner_multiplier(job.labels) > 1:
                expensive[(run.repo, run.workflow)] += job_billable_minutes(job)
    return expensive


def build_findings(workflows: list[dict], steps: list[dict], runs: list[Run]) -> list[dict]:
    findings: list[dict] = []

    def add(severity: str, wf: dict, title: str, advice: str) -> None:
        findings.append({"severity": severity, "repo": wf["repo"], "workflow": wf["workflow"], "title": title, "advice": advice})

    for wf in workflows:
        if wf["runs"] >= 5 and wf["fail_rate"] >= FAIL_RATE_WARN:
            add("high", wf, f"{wf['fail_rate']:.0%} of runs fail",
                f"{wf['failure']} of {wf['runs']} runs failed, wasting about {wf['wasted_min']:.0f} billable min. Fix or gate the workflow to run on fewer triggers.")
        if wf["flaky_incidents"]:
            add("high", wf, f"Flaky: {wf['flaky_incidents']} fail-then-pass incident(s)",
                "The same commit failed and later passed. Find the nondeterministic step (network, timing, shared state) rather than re-running.")
        if wf["runs"] >= 5 and wf["cancel_rate"] >= CANCEL_RATE_WARN:
            add("medium", wf, f"{wf['cancel_rate']:.0%} of runs cancelled",
                "Many cancelled runs usually mean pushes outpace CI. Use `concurrency` with `cancel-in-progress` and `paths` filters so you pay only for runs that matter.")
        if wf["p50_s"] > 0 and wf["p95_s"] / wf["p50_s"] >= VARIANCE_RATIO_WARN and wf["runs"] >= 8:
            add("medium", wf, f"Duration is erratic (p95 {wf['p95_s'] / 60:.1f} min vs p50 {wf['p50_s'] / 60:.1f} min)",
                "Large spread points to cold caches, queueing or hung steps. Add `timeout-minutes` and check the slowest steps below.")
    expensive = _runner_label_cost(runs)
    for wf in workflows:
        cost = expensive.get((wf["repo"], wf["workflow"]), 0)
        if cost >= 30:
            add("medium", wf, f"{cost} billable min on Windows/macOS runners (sampled runs)",
                "Windows bills 2x and macOS 10x. Move tests that do not need the OS to ubuntu and keep one matrix leg on the expensive runner.")
    workflow_lookup = {(w["repo"], w["workflow"]): w for w in workflows}
    cache_workflows = {
        (r.repo, r.workflow) for r in runs for j in r.jobs for s in j.steps if CACHE_PATTERN.search(s.name)
    }
    for step in steps:
        if INSTALL_PATTERN.search(step["step"]) and step["mean_s"] >= SLOW_INSTALL_SECONDS and step["count"] >= 3:
            wf = workflow_lookup[(step["repo"], step["workflow"])]
            cached = (step["repo"], step["workflow"]) in cache_workflows
            hint = "A cache step exists; check hit rate and cache key." if cached else "No cache step seen; add dependency caching (e.g. `cache:` on setup-python/setup-node)."
            add("medium", wf, f"Slow install step '{step['step']}' averages {step['mean_s']:.0f}s",
                f"Across {step['count']} runs this step used {step['total_s'] / 60:.1f} min in job '{step['job']}'. {hint}")
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(findings, key=lambda f: order[f["severity"]])


def analyze(runs: list[Run], days: int, now: datetime | None = None, errors: dict[str, str] | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    minutes = estimate_run_minutes(runs)
    flaky = find_flaky(runs)
    workflows = _workflow_rows(runs, minutes, flaky)
    steps = aggregate_steps(runs)
    repos: dict[str, dict] = defaultdict(lambda: {"runs": 0, "failed": 0, "billable_min": 0.0, "wasted_min": 0.0})
    for run in runs:
        entry = repos[run.repo]
        entry["runs"] += 1
        entry["failed"] += run.conclusion == "failure"
        entry["billable_min"] += minutes[run.id]
        entry["wasted_min"] += minutes[run.id] if _is_waste(run) else 0
    repo_rows = sorted(
        ({"repo": name, **{k: round(v, 1) if isinstance(v, float) else v for k, v in data.items()}} for name, data in repos.items()),
        key=lambda r: -r["billable_min"],
    )
    total_billable = sum(minutes.values())
    total_wasted = sum(minutes[r.id] for r in runs if _is_waste(r))
    return {
        "generated": now.strftime("%Y-%m-%d %H:%M UTC"),
        "summary": {
            "days": days, "runs": len(runs), "repos": len(repo_rows), "workflows": len(workflows),
            "billable_min": round(total_billable, 1), "wasted_min": round(total_wasted, 1),
            "wasted_pct": round(total_wasted / total_billable, 3) if total_billable else 0.0,
            "fail_rate": round(sum(r.conclusion == "failure" for r in runs) / len(runs), 3) if runs else 0.0,
            "jobs_sampled_runs": sum(1 for r in runs if r.jobs),
            "errors": errors or {},
        },
        "workflows": workflows,
        "steps": steps[:50],
        "flaky": flaky,
        "trend": weekly_trend(runs, minutes, now, max(1, math.ceil(days / 7))),
        "repos": repo_rows,
        "findings": build_findings(workflows, steps, runs),
    }
