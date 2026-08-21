from src import db


def _sample_finding(**overrides):
    base = {
        "repo_path": "/repos/example",
        "repo_name": "example",
        "scope": "working-tree",
        "file_path": "config.py",
        "line_number": 3,
        "commit_sha": "",
        "pattern_name": "AWS Access Key ID",
        "severity": "critical",
        "entropy": 4.1,
        "masked_preview": "AKIA••••••••••••WXYZ",
        "match_hash": "abc123",
        "ai_verdict": None,
        "ai_rationale": None,
    }
    base.update(overrides)
    return base


def test_upsert_and_get_findings_roundtrip(tmp_path):
    conn = db.connect(str(tmp_path / "findings.db"))
    db.upsert_finding(conn, _sample_finding())

    rows = db.get_findings(conn)
    assert len(rows) == 1
    assert rows[0]["pattern_name"] == "AWS Access Key ID"
    assert rows[0]["status"] == "new"


def test_rescanning_same_finding_does_not_duplicate(tmp_path):
    conn = db.connect(str(tmp_path / "findings.db"))
    db.upsert_finding(conn, _sample_finding())
    db.upsert_finding(conn, _sample_finding())  # identical re-scan

    rows = db.get_findings(conn)
    assert len(rows) == 1


def test_working_tree_findings_dedup_despite_empty_commit_sha(tmp_path):
    """Regression guard: commit_sha must be '' not NULL, or SQLite's UNIQUE
    constraint would treat every NULL as distinct and duplicates would slip through."""
    conn = db.connect(str(tmp_path / "findings.db"))
    db.upsert_finding(conn, _sample_finding(commit_sha=None))
    db.upsert_finding(conn, _sample_finding(commit_sha=None))

    rows = db.get_findings(conn)
    assert len(rows) == 1


def test_ack_finding_marks_acknowledged_and_excludes_from_new_count(tmp_path):
    conn = db.connect(str(tmp_path / "findings.db"))
    db.upsert_finding(conn, _sample_finding())
    finding_id = db.get_findings(conn)[0]["id"]

    assert db.count_new(conn) == 1
    ok = db.ack_finding(conn, finding_id)
    assert ok is True
    assert db.count_new(conn) == 0

    all_rows = db.get_findings(conn)
    assert len(all_rows) == 1
    assert all_rows[0]["status"] == "acknowledged"


def test_ack_unknown_finding_id_returns_false(tmp_path):
    conn = db.connect(str(tmp_path / "findings.db"))
    assert db.ack_finding(conn, 9999) is False


def test_get_findings_filters_by_repo_and_status(tmp_path):
    conn = db.connect(str(tmp_path / "findings.db"))
    db.upsert_finding(conn, _sample_finding(repo_path="/repos/a", match_hash="hash-a"))
    db.upsert_finding(conn, _sample_finding(repo_path="/repos/b", match_hash="hash-b"))
    finding_id = db.get_findings(conn, repo_path="/repos/a")[0]["id"]
    db.ack_finding(conn, finding_id)

    assert len(db.get_findings(conn, repo_path="/repos/a")) == 1
    assert len(db.get_findings(conn, repo_path="/repos/b")) == 1
    assert len(db.get_findings(conn, status="acknowledged")) == 1
    assert len(db.get_findings(conn, status="new")) == 1
