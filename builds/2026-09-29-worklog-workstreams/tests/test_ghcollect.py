import pytest

from conftest import make_fake_github
from worklog import ghcollect
from worklog.project import discover


def _collect(gh_repo, **kw):
    project = discover(gh_repo.root)
    head = gh_repo.git("rev-parse", "feature/41-csv-validation")
    return ghcollect.collect(project, fetch=make_fake_github(head, **kw)), head


def test_issue_pr_review_and_ci_events_are_produced(gh_repo):
    events, _ = _collect(gh_repo, merged=True)
    refs = {e["ref"] for e in events}
    assert {"issue:41:opened", "issue:41:closed", "pr:52:opened", "pr:52:merged", "review:9001", "check:777"} <= refs


def test_pull_requests_are_not_double_counted_from_issues_feed(gh_repo):
    events, _ = _collect(gh_repo, merged=False)
    assert not [e for e in events if e["ref"].startswith("issue:52")]


def test_pr_event_links_head_sha_branch_and_closing_issue(gh_repo):
    events, head = _collect(gh_repo, merged=False)
    pr = next(e for e in events if e["ref"] == "pr:52:opened")
    assert {f"sha:{head}", "branch:feature/41-csv-validation", "gh:52", "gh:41"} <= set(pr["keys"])


def test_failed_ci_and_changes_requested_are_flagged(gh_repo):
    events, _ = _collect(gh_repo, merged=False, changes_requested=True)
    assert next(e for e in events if e["type"] == "ci")["status"] == "failed"
    assert next(e for e in events if e["type"] == "review")["status"] == "blocked"


def test_non_github_remote_raises_unavailable(scenario):
    scenario.git("remote", "add", "origin", "https://gitlab.com/acme/lab.git")
    with pytest.raises(ghcollect.GitHubUnavailable):
        ghcollect.collect(discover(scenario.root), fetch=lambda url: [])


def test_http_failure_propagates_as_unavailable_not_crash(gh_repo):
    def broken(url):
        raise ghcollect.GitHubUnavailable("GitHub returned HTTP 403")
    with pytest.raises(ghcollect.GitHubUnavailable, match="403"):
        ghcollect.collect(discover(gh_repo.root), fetch=broken)


def test_remote_token_never_reaches_events(gh_repo):
    events, _ = _collect(gh_repo, merged=True)
    assert "ghp_" not in str(events)


def test_bot_authors_are_classified_as_agents():
    assert ghcollect._actor({"login": "dependabot[bot]", "type": "Bot"}) == ("agent", "dependabot[bot]")
    assert ghcollect._actor(None) == ("human", "unknown")
