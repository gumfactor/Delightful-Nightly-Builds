import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import github_client  # noqa: E402


FIXTURE_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "starred_page.json"


def _load_fixture():
    return json.loads(FIXTURE_PATH.read_text())


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def read(self):
        return self._body


def make_opener(pages):
    """pages: list of lists of star entries, one list per page in order."""
    calls = {"n": 0}

    def opener(request):
        idx = calls["n"]
        calls["n"] += 1
        if idx >= len(pages):
            return FakeResponse(200, json.dumps([]).encode("utf-8"))
        return FakeResponse(200, json.dumps(pages[idx]).encode("utf-8"))

    opener.calls = calls
    return opener


def test_missing_token_raises():
    with pytest.raises(github_client.MissingTokenError):
        github_client.fetch_starred(None)


def test_fetch_starred_parses_all_fields():
    entries = _load_fixture()
    opener = make_opener([entries])
    repos = github_client.fetch_starred("tok", opener=opener)
    assert len(repos) == 5
    first = repos[0]
    assert first.full_name == "acme/llm-agent-toolkit"
    assert first.language == "Python"
    assert first.topics == ["llm", "agent", "ai"]
    assert first.stargazers_count == 4200
    assert first.starred_at == "2026-09-15T12:00:00Z"


def test_fetch_starred_stops_on_empty_page():
    entries = _load_fixture()
    opener = make_opener([entries, []])
    repos = github_client.fetch_starred("tok", opener=opener, per_page=100)
    assert len(repos) == 5
    # Only one real page fetched since len(body) < per_page triggers stop.
    assert opener.calls["n"] == 1


def test_fetch_starred_incremental_since_cutoff():
    entries = _load_fixture()
    # Pretend we already have everything at or before 2026-09-05T18:15:00Z.
    since = "2026-09-05T18:15:00Z"
    opener = make_opener([entries])
    repos = github_client.fetch_starred("tok", since=since, opener=opener)
    names = {r.full_name for r in repos}
    assert names == {"acme/llm-agent-toolkit", "dataworks/etl-pipeline"}


def test_fetch_starred_paginates_across_pages():
    entries = _load_fixture()
    page1 = entries[:3]
    page2 = entries[3:]
    # Force per_page smaller than page1 length is not needed; simulate via
    # per_page=3 so the client keeps requesting until a short page appears.
    opener = make_opener([page1, page2])
    repos = github_client.fetch_starred("tok", opener=opener, per_page=3)
    assert len(repos) == 5
    assert opener.calls["n"] == 2


def test_fetch_starred_raises_on_http_error():
    def opener(request):
        return FakeResponse(403, b"[]")

    with pytest.raises(github_client.GitHubAPIError) as exc_info:
        github_client.fetch_starred("tok", opener=opener)
    assert exc_info.value.status == 403


def test_fetch_starred_empty_result_when_no_stars():
    opener = make_opener([[]])
    repos = github_client.fetch_starred("tok", opener=opener)
    assert repos == []
