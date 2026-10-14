import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gha_perf.models import Job, Run, Step  # noqa: E402

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)


def make_run(run_id=1, repo="me/app", workflow="CI", conclusion="success", seconds=120.0, days_ago=1.0,
             sha=None, attempt=1, jobs=None, event="push") -> Run:
    return Run(id=run_id, repo=repo, workflow=workflow, path=".github/workflows/ci.yml", event=event, branch="main",
               sha=sha or f"sha{run_id}", attempt=attempt, conclusion=conclusion,
               started=NOW - timedelta(days=days_ago), seconds=seconds, url=f"https://github.com/{repo}/actions/runs/{run_id}",
               jobs=jobs or [])


def make_job(run_id=1, name="test", labels=("ubuntu-latest",), seconds=90.0, steps=None) -> Job:
    return Job(run_id=run_id, name=name, labels=list(labels), seconds=seconds, conclusion="success", steps=steps or [])


def make_step(name="Run tests", seconds=30.0, conclusion="success") -> Step:
    return Step(name=name, seconds=seconds, conclusion=conclusion)


def json_response(payload, headers=None, status=200):
    return status, {k.lower(): v for k, v in (headers or {}).items()}, json.dumps(payload).encode()


class FakeTransport:
    """Maps URL substrings to canned responses; records every URL requested."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url, headers):
        self.calls.append(url)
        for fragment, response in self.routes:
            if fragment in url:
                return response(url) if callable(response) else response
        return 404, {}, b"{}"
