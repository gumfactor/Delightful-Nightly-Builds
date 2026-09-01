from src.drift import compute_drift, compute_staleness, repo_staleness_summary


def _snap(repo, ecosystem, dependency, pinned, latest=None):
    return {
        "repo": repo,
        "ecosystem": ecosystem,
        "dependency": dependency,
        "pinned_version": pinned,
        "latest_version": latest,
    }


def test_identical_pins_across_repos_not_flagged():
    snapshots = [
        _snap("user/a", "python", "requests", "2.31.0"),
        _snap("user/b", "python", "requests", "2.31.0"),
    ]
    assert compute_drift(snapshots) == []


def test_single_repo_never_flagged():
    snapshots = [_snap("user/a", "python", "requests", "2.31.0")]
    assert compute_drift(snapshots) == []


def test_two_repos_different_versions_flagged_with_severity():
    snapshots = [
        _snap("user/a", "python", "requests", "2.31.0"),
        _snap("user/b", "python", "requests", "2.20.0"),
    ]
    entries = compute_drift(snapshots)
    assert len(entries) == 1
    assert entries[0]["dependency"] == "requests"
    assert entries[0]["severity"] == "minor"
    assert entries[0]["min_version"] == "2.20.0"
    assert entries[0]["max_version"] == "2.31.0"


def test_major_version_drift_classified_major():
    snapshots = [
        _snap("user/a", "python", "django", "3.2.0"),
        _snap("user/b", "python", "django", "5.0.0"),
    ]
    entries = compute_drift(snapshots)
    assert entries[0]["severity"] == "major"


def test_three_repos_uses_min_max_span():
    snapshots = [
        _snap("user/a", "npm", "react", "18.0.0"),
        _snap("user/b", "npm", "react", "18.2.0"),
        _snap("user/c", "npm", "react", "17.0.0"),
    ]
    entries = compute_drift(snapshots)
    assert len(entries) == 1
    assert entries[0]["min_version"] == "17.0.0"
    assert entries[0]["max_version"] == "18.2.0"
    assert entries[0]["severity"] == "major"


def test_entries_sorted_by_severity_then_name():
    snapshots = [
        _snap("user/a", "python", "zeta", "1.0.0"),
        _snap("user/b", "python", "zeta", "1.0.1"),
        _snap("user/a", "python", "alpha", "1.0.0"),
        _snap("user/b", "python", "alpha", "2.0.0"),
    ]
    entries = compute_drift(snapshots)
    assert [e["dependency"] for e in entries] == ["alpha", "zeta"]


def test_unparseable_pinned_version_excluded_from_drift():
    snapshots = [
        _snap("user/a", "python", "numpy", None),
        _snap("user/b", "python", "numpy", None),
    ]
    assert compute_drift(snapshots) == []


def test_staleness_current_when_matches_latest():
    snapshots = [_snap("user/a", "python", "requests", "2.31.0", "2.31.0")]
    entries = compute_staleness(snapshots)
    assert entries[0]["classification"] == "current"


def test_staleness_classifies_behind_by_severity():
    snapshots = [_snap("user/a", "python", "requests", "2.20.0", "2.31.0")]
    entries = compute_staleness(snapshots)
    assert entries[0]["classification"] == "minor-behind"


def test_staleness_major_behind():
    snapshots = [_snap("user/a", "python", "django", "3.2.0", "5.0.0")]
    entries = compute_staleness(snapshots)
    assert entries[0]["classification"] == "major-behind"


def test_staleness_unknown_when_latest_missing():
    snapshots = [_snap("user/a", "python", "internal-tool", "1.0.0", None)]
    entries = compute_staleness(snapshots)
    assert entries[0]["classification"] == "unknown"


def test_staleness_unknown_when_pinned_missing():
    snapshots = [_snap("user/a", "python", "numpy", None, "2.0.0")]
    entries = compute_staleness(snapshots)
    assert entries[0]["classification"] == "unknown"


def test_repo_staleness_summary_counts_behind_and_major():
    staleness_entries = compute_staleness([
        _snap("user/a", "python", "requests", "2.20.0", "2.31.0"),   # minor-behind
        _snap("user/a", "python", "django", "3.2.0", "5.0.0"),        # major-behind
        _snap("user/a", "python", "flask", "3.0.0", "3.0.0"),          # current
        _snap("user/b", "python", "requests", "2.31.0", "2.31.0"),    # current
    ])
    summary = repo_staleness_summary(staleness_entries)
    assert summary["user/a"]["total"] == 3
    assert summary["user/a"]["behind_count"] == 2
    assert summary["user/a"]["major_count"] == 1
    assert summary["user/b"]["behind_count"] == 0
