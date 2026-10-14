"""Fetch repos, workflow runs and job/step detail into model objects."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Callable

from .api import GitHubClient, GitHubError, NotFoundError, RateLimitError
from .models import Job, Run, Step, parse_ts, seconds_between

Log = Callable[[str], None]


def list_repos(client: GitHubClient, include_forks: bool = False, include_archived: bool = False) -> list[str]:
    """Full names of repos the token owner can see (owner/collaborator/org member)."""
    names = []
    for repo in client.paginate("/user/repos?per_page=100&sort=pushed", max_items=500):
        if repo.get("fork") and not include_forks:
            continue
        if repo.get("archived") and not include_archived:
            continue
        names.append(repo["full_name"])
    return names


def run_from_api(repo: str, raw: dict) -> Run:
    started = parse_ts(raw.get("run_started_at")) or parse_ts(raw.get("created_at"))
    ended = parse_ts(raw.get("updated_at"))
    return Run(
        id=raw["id"],
        repo=repo,
        workflow=raw.get("name") or raw.get("path", "unknown"),
        path=raw.get("path", ""),
        event=raw.get("event", ""),
        branch=raw.get("head_branch") or "",
        sha=raw.get("head_sha", ""),
        attempt=raw.get("run_attempt") or 1,
        conclusion=raw.get("conclusion"),
        started=started,
        seconds=seconds_between(started, ended),
        url=raw.get("html_url", ""),
    )


def job_from_api(run_id: int, raw: dict) -> Job:
    steps = [
        Step(
            name=step.get("name", ""),
            seconds=seconds_between(parse_ts(step.get("started_at")), parse_ts(step.get("completed_at"))),
            conclusion=step.get("conclusion"),
        )
        for step in raw.get("steps") or []
    ]
    return Job(
        run_id=run_id,
        name=raw.get("name", ""),
        labels=list(raw.get("labels") or []),
        seconds=seconds_between(parse_ts(raw.get("started_at")), parse_ts(raw.get("completed_at"))),
        conclusion=raw.get("conclusion"),
        steps=steps,
    )


def fetch_runs(client: GitHubClient, repo: str, since: datetime, max_runs: int) -> list[Run]:
    """Completed runs created on/after ``since`` (newest first)."""
    date = since.strftime("%Y-%m-%d")
    path = f"/repos/{repo}/actions/runs?per_page=100&status=completed&created=%3E%3D{date}"
    return [run_from_api(repo, raw) for raw in client.paginate(path, "workflow_runs", max_items=max_runs)]


def fetch_jobs(client: GitHubClient, repo: str, run_id: int) -> list[Job]:
    path = f"/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100&filter=latest"
    return [job_from_api(run_id, raw) for raw in client.paginate(path, "jobs", max_items=200)]


def attach_jobs(client: GitHubClient, runs: list[Run], per_workflow: int, log: Log = lambda _m: None) -> None:
    """Fetch job detail for the newest ``per_workflow`` runs of each workflow (API budget control)."""
    by_workflow: dict[tuple[str, str], list[Run]] = defaultdict(list)
    for run in runs:
        by_workflow[(run.repo, run.workflow)].append(run)
    for group in by_workflow.values():
        for run in group[:per_workflow]:
            try:
                run.jobs = fetch_jobs(client, run.repo, run.id)
            except NotFoundError:
                continue
            except RateLimitError:
                raise
            except GitHubError as error:
                log(f"  jobs for run {run.id} skipped: {error}")


def collect(
    client: GitHubClient,
    repos: list[str],
    days: int,
    max_runs: int = 300,
    jobs_per_workflow: int = 15,
    now: datetime | None = None,
    log: Log = lambda _m: None,
) -> tuple[list[Run], dict[str, str]]:
    """Collect runs for all repos. Per-repo failures are recorded, not raised (except rate limit)."""
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    all_runs: list[Run] = []
    errors: dict[str, str] = {}
    for repo in repos:
        try:
            runs = fetch_runs(client, repo, since, max_runs)
            if runs:
                log(f"{repo}: {len(runs)} runs")
                attach_jobs(client, runs, jobs_per_workflow, log)
            all_runs.extend(runs)
        except RateLimitError as error:
            errors[repo] = str(error)
            log(f"{repo}: {error}; stopping early with partial data")
            break
        except GitHubError as error:
            errors[repo] = str(error)
            log(f"{repo}: skipped ({error})")
    return all_runs, errors
