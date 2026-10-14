import pytest

from conftest import FakeTransport, json_response
from gha_perf.api import GitHubClient, GitHubError, NotFoundError, RateLimitError
from gha_perf.models import parse_ts, seconds_between


def test_paginate_follows_link_header_across_pages():
    transport = FakeTransport([
        ("page=2", json_response({"items": [{"n": 3}]})),
        ("/things", json_response({"items": [{"n": 1}, {"n": 2}]},
                                  {"Link": '<https://api.github.com/things?page=2>; rel="next"'})),
    ])
    client = GitHubClient("t", transport)
    assert [i["n"] for i in client.paginate("/things", "items")] == [1, 2, 3]
    assert client.requests_made == 2


def test_paginate_respects_max_items():
    transport = FakeTransport([("/things", json_response([{"n": i} for i in range(10)]))])
    assert len(list(GitHubClient("t", transport).paginate("/things", max_items=4))) == 4


def test_rate_limit_raises_specific_error():
    transport = FakeTransport([("/x", (403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "123"}, b"{}"))])
    with pytest.raises(RateLimitError, match="123"):
        GitHubClient("t", transport).get("/x")


def test_forbidden_without_rate_limit_is_not_found_error():
    transport = FakeTransport([("/x", (403, {}, b"{}"))])
    with pytest.raises(NotFoundError):
        GitHubClient("t", transport).get("/x")


def test_unauthorized_mentions_token():
    transport = FakeTransport([("/x", (401, {}, b"{}"))])
    with pytest.raises(GitHubError, match="GITHUB_TOKEN"):
        GitHubClient("t", transport).get("/x")


def test_authorization_header_only_sent_with_token():
    seen = []

    def transport(url, headers):
        seen.append(headers)
        return json_response({})

    GitHubClient("abc", transport).get("/x")
    GitHubClient(None, transport).get("/x")
    assert seen[0]["Authorization"] == "Bearer abc"
    assert "Authorization" not in seen[1]


def test_parse_ts_handles_z_suffix_and_garbage():
    assert parse_ts("2026-10-14T12:00:00Z").hour == 12
    assert parse_ts(None) is None
    assert parse_ts("not a date") is None


def test_seconds_between_never_negative_or_none():
    a, b = parse_ts("2026-10-14T12:00:00Z"), parse_ts("2026-10-14T12:01:30Z")
    assert seconds_between(a, b) == 90
    assert seconds_between(b, a) == 0
    assert seconds_between(None, b) == 0
