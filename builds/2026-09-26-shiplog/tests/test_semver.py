from classify import Commit
from semver import suggest_bump


def _commit(**overrides):
    base = dict(
        sha="abc1234", subject="x", body="", author_date="2026-09-01",
        type="chore", scope=None, breaking=False, pr_number=None, source="keyword",
    )
    base.update(overrides)
    return Commit(**base)


def test_breaking_change_forces_major_even_with_features_present():
    sections = {
        "Breaking Changes": [_commit(type="feat", breaking=True)],
        "Features": [_commit(type="feat")],
    }
    assert suggest_bump(sections) == "major"


def test_feature_without_breaking_is_minor():
    sections = {"Features": [_commit(type="feat")]}
    assert suggest_bump(sections) == "minor"


def test_fix_only_is_patch():
    sections = {"Fixes": [_commit(type="fix")]}
    assert suggest_bump(sections) == "patch"


def test_no_commits_is_none():
    assert suggest_bump({}) == "none"


def test_maintenance_only_is_none():
    sections = {"Maintenance": [_commit(type="chore")]}
    assert suggest_bump(sections) == "none"
