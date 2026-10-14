from conftest import NOW, FakeTransport, json_response
from gha_perf.api import GitHubClient
from gha_perf.collect import collect, job_from_api, list_repos, run_from_api

RUN = {"id": 11, "name": "CI", "path": ".github/workflows/ci.yml", "event": "push", "head_branch": "main", "head_sha": "abc",
       "run_attempt": 2, "conclusion": "failure", "run_started_at": "2026-10-13T10:00:00Z", "updated_at": "2026-10-13T10:03:00Z",
       "html_url": "https://github.com/me/app/actions/runs/11"}
JOB = {"name": "test", "labels": ["windows-latest"], "started_at": "2026-10-13T10:00:00Z", "completed_at": "2026-10-13T10:02:00Z",
       "conclusion": "failure", "steps": [{"name": "Run tests", "started_at": "2026-10-13T10:00:10Z",
                                           "completed_at": "2026-10-13T10:01:40Z", "conclusion": "failure"}]}


def test_run_from_api_computes_duration_and_attempt():
    run = run_from_api("me/app", RUN)
    assert run.seconds == 180 and run.attempt == 2 and run.workflow == "CI"


def test_job_from_api_parses_steps_and_labels():
    job = job_from_api(11, JOB)
    assert job.seconds == 120 and job.labels == ["windows-latest"] and job.steps[0].seconds == 90


def test_job_from_api_tolerates_missing_steps_and_times():
    job = job_from_api(1, {"name": "x"})
    assert job.seconds == 0 and job.steps == []


def test_list_repos_skips_forks_and_archived():
    repos = [{"full_name": "me/a"}, {"full_name": "me/f", "fork": True}, {"full_name": "me/old", "archived": True}]
    client = GitHubClient("t", FakeTransport([("/user/repos", json_response(repos))]))
    assert list_repos(client) == ["me/a"]
    assert list_repos(client, include_forks=True, include_archived=True) == ["me/a", "me/f", "me/old"]


def test_collect_fetches_runs_and_jobs_and_survives_repo_failure():
    transport = FakeTransport([
        ("me/bad/actions/runs", (500, {}, b"{}")),
        ("me/app/actions/runs/11/jobs", json_response({"jobs": [JOB]})),
        ("me/app/actions/runs", json_response({"workflow_runs": [RUN]})),
    ])
    runs, errors = collect(GitHubClient("t", transport), ["me/bad", "me/app"], days=30, now=NOW)
    assert len(runs) == 1 and runs[0].jobs[0].steps[0].name == "Run tests"
    assert "me/bad" in errors and "me/app" not in errors


def test_collect_stops_on_rate_limit_and_keeps_partial_data():
    transport = FakeTransport([
        ("me/a/actions/runs/11/jobs", json_response({"jobs": [JOB]})),
        ("me/a/actions/runs", json_response({"workflow_runs": [RUN]})),
        ("me/b/", (403, {"x-ratelimit-remaining": "0"}, b"{}")),
    ])
    runs, errors = collect(GitHubClient("t", transport), ["me/a", "me/b", "me/c"], days=7, now=NOW)
    assert len(runs) == 1 and "me/b" in errors
    assert not any("me/c" in url for url in transport.calls)


def test_collect_limits_job_fetches_per_workflow():
    many = [{**RUN, "id": i} for i in range(1, 6)]
    transport = FakeTransport([("/jobs", json_response({"jobs": [JOB]})), ("/actions/runs", json_response({"workflow_runs": many}))])
    runs, _ = collect(GitHubClient("t", transport), ["me/app"], days=7, jobs_per_workflow=2, now=NOW)
    assert sum(1 for r in runs if r.jobs) == 2
