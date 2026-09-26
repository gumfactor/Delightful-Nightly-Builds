from classify import Commit, cancel_reverts, classify_commit, group_sections
from git_log import RawCommit


def _raw(sha="abc1234", subject="", body=""):
    return RawCommit(sha=sha, author_date="2026-09-01T00:00:00-04:00", subject=subject, body=body)


def test_conventional_feat_with_scope():
    commit = classify_commit(_raw(subject="feat(auth): add login flow"))
    assert commit.type == "feat"
    assert commit.scope == "auth"
    assert commit.breaking is False
    assert commit.subject == "add login flow"
    assert commit.source == "conventional"


def test_conventional_breaking_bang():
    commit = classify_commit(_raw(subject="feat(api)!: remove legacy endpoint"))
    assert commit.breaking is True
    assert commit.type == "feat"


def test_conventional_breaking_footer():
    commit = classify_commit(_raw(subject="fix: change default timeout", body="BREAKING CHANGE: default timeout is now 30s"))
    assert commit.breaking is True
    assert commit.type == "fix"


def test_conventional_no_scope():
    commit = classify_commit(_raw(subject="chore: bump lockfile"))
    assert commit.type == "chore"
    assert commit.scope is None


def test_unknown_conventional_looking_type_falls_back_to_keyword():
    # "wip:" is not a known conventional type — should fall through to keyword classification
    commit = classify_commit(_raw(subject="wip: fix broken login button"))
    assert commit.source == "keyword"
    assert commit.type == "fix"


def test_keyword_fallback_feat():
    commit = classify_commit(_raw(subject="Add CSV export button to dashboard"))
    assert commit.type == "feat"
    assert commit.source == "keyword"


def test_keyword_fallback_docs():
    commit = classify_commit(_raw(subject="Update README with install steps"))
    assert commit.type == "docs"


def test_keyword_fallback_truly_unclassifiable_is_other():
    commit = classify_commit(_raw(subject="asdkjbasd zzz qqq"))
    assert commit.type == "other"


def test_merge_commit_pr_number_extracted():
    commit = classify_commit(_raw(subject="Merge pull request #42 from user/feature-branch"))
    assert commit.pr_number == 42


def test_non_merge_commit_has_no_pr_number():
    commit = classify_commit(_raw(subject="fix: correct off-by-one error"))
    assert commit.pr_number is None


def test_revert_commit_classified_as_revert_type():
    commit = classify_commit(_raw(subject='Revert "feat: add risky experiment"'))
    assert commit.type == "revert"


def test_cancel_reverts_removes_matched_pair():
    original = classify_commit(_raw(sha="aaa1111", subject="feat: add risky experiment"))
    revert = classify_commit(_raw(sha="bbb2222", subject='Revert "feat: add risky experiment"'))
    unrelated = classify_commit(_raw(sha="ccc3333", subject="fix: unrelated bug"))

    surviving, cancelled = cancel_reverts([original, revert, unrelated])

    assert len(cancelled) == 1
    assert cancelled[0][0].sha == "aaa1111"
    assert cancelled[0][1].sha == "bbb2222"
    assert [c.sha for c in surviving] == ["ccc3333"]


def test_cancel_reverts_leaves_unmatched_revert_when_original_not_in_range():
    # Original commit is outside the fetched range — revert has nothing to cancel against.
    revert = classify_commit(_raw(sha="bbb2222", subject='Revert "feat: something from before the range"'))
    surviving, cancelled = cancel_reverts([revert])

    assert cancelled == []
    assert [c.sha for c in surviving] == ["bbb2222"]


def test_group_sections_breaking_takes_priority_over_type():
    breaking_fix = classify_commit(_raw(subject="fix!: remove old field"))
    sections = group_sections([breaking_fix])
    assert "Breaking Changes" in sections
    assert "Fixes" not in sections


def test_group_sections_omits_empty_sections():
    feat = classify_commit(_raw(subject="feat: add widget"))
    sections = group_sections([feat])
    assert list(sections.keys()) == ["Features"]
