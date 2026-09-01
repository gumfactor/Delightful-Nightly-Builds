import base64
import json

from src.gh_client import fetch_file_content, list_owned_repos


def test_list_owned_repos_single_page():
    def transport(url, headers, method="GET", data=None):
        assert "Authorization" in headers
        page = [{"full_name": "user/repo-a"}, {"full_name": "user/repo-b"}]
        return 200, json.dumps(page).encode("utf-8")

    repos = list_owned_repos("fake-token", transport=transport)
    assert repos == ["user/repo-a", "user/repo-b"]


def test_list_owned_repos_paginates_until_short_page():
    calls = []

    def transport(url, headers, method="GET", data=None):
        calls.append(url)
        # Note: check "&page=" (not "page=") since "per_page=100" itself
        # contains the substring "page=1" and would otherwise false-match.
        if "&page=1" in url:
            page = [{"full_name": f"user/repo-{i}"} for i in range(100)]
            return 200, json.dumps(page).encode("utf-8")
        if "&page=2" in url:
            page = [{"full_name": "user/repo-100"}]
            return 200, json.dumps(page).encode("utf-8")
        return 200, b"[]"

    repos = list_owned_repos("fake-token", transport=transport)
    assert len(repos) == 101
    assert repos[-1] == "user/repo-100"
    assert len(calls) == 2


def test_list_owned_repos_stops_on_empty_page():
    def transport(url, headers, method="GET", data=None):
        return 200, b"[]"

    assert list_owned_repos("fake-token", transport=transport) == []


def test_list_owned_repos_non_200_returns_empty():
    def transport(url, headers, method="GET", data=None):
        return 401, b"Unauthorized"

    assert list_owned_repos("bad-token", transport=transport) == []


def test_fetch_file_content_decodes_base64():
    content = "requests==2.31.0\n"
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    def transport(url, headers, method="GET", data=None):
        assert "requirements.txt" in url
        return 200, json.dumps({"content": encoded, "encoding": "base64"}).encode("utf-8")

    result = fetch_file_content("fake-token", "user/repo", "requirements.txt", transport=transport)
    assert result == content


def test_fetch_file_content_missing_file_returns_none():
    def transport(url, headers, method="GET", data=None):
        return 404, b"Not Found"

    result = fetch_file_content("fake-token", "user/repo", "requirements.txt", transport=transport)
    assert result is None


def test_fetch_file_content_non_base64_encoding_returns_none():
    def transport(url, headers, method="GET", data=None):
        return 200, json.dumps({"content": "abc", "encoding": "none"}).encode("utf-8")

    result = fetch_file_content("fake-token", "user/repo", "requirements.txt", transport=transport)
    assert result is None
