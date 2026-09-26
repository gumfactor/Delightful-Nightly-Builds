from classify import Commit
from github_enrich import enrich_with_github


def _merge_commit(pr_number=42):
    return Commit(
        sha="abc1234", subject=f"Merge pull request #{pr_number} from user/branch",
        body="", author_date="2026-09-01", type="other", scope=None,
        breaking=False, pr_number=pr_number, source="keyword",
    )


def test_no_repo_or_token_makes_zero_calls():
    calls = []

    def spy_http_get(url, headers):
        calls.append(url)
        return 200, {"title": "should not be reached"}

    commits = [_merge_commit()]
    result = enrich_with_github(commits, repo=None, token=None, http_get=spy_http_get)

    assert calls == []
    assert result[0].subject == commits[0].subject


def test_successful_enrichment_uses_pr_title_and_label():
    def fake_http_get(url, headers):
        assert url == "https://api.github.com/repos/acme/widgets/pulls/42"
        assert headers["Authorization"] == "Bearer test-token"
        return 200, {"title": "Fix crash on empty upload", "labels": [{"name": "bug"}]}

    commits = [_merge_commit(42)]
    result = enrich_with_github(commits, repo="acme/widgets", token="test-token", http_get=fake_http_get)

    assert result[0].subject == "Fix crash on empty upload"
    assert result[0].type == "fix"
    assert result[0].source == "github-pr"


def test_breaking_label_sets_breaking_flag():
    def fake_http_get(url, headers):
        return 200, {"title": "Remove deprecated field", "labels": [{"name": "breaking"}]}

    commits = [_merge_commit(7)]
    result = enrich_with_github(commits, repo="acme/widgets", token="tok", http_get=fake_http_get)

    assert result[0].breaking is True


def test_failed_request_falls_back_to_original_commit():
    def failing_http_get(url, headers):
        return 404, None

    original = _merge_commit(99)
    result = enrich_with_github([original], repo="acme/widgets", token="tok", http_get=failing_http_get)

    assert result[0].subject == original.subject
    assert result[0].source == "keyword"


def test_commits_without_pr_number_are_left_untouched():
    def spy_http_get(url, headers):
        raise AssertionError("should not be called for non-PR commits")

    commit = Commit(
        sha="zzz", subject="fix: direct commit, no PR", body="", author_date="2026-09-01",
        type="fix", scope=None, breaking=False, pr_number=None, source="conventional",
    )
    result = enrich_with_github([commit], repo="acme/widgets", token="tok", http_get=spy_http_get)
    assert result[0] is commit
