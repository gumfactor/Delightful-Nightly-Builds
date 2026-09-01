import base64
import json
import os

import pytest

from src import store
from src.cli import _sync, build_parser, main


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _fake_transport(repos, files):
    """repos: list of full_name strings. files: {(repo, path): text or None}."""

    def transport(url, headers, method="GET", data=None):
        if "/user/repos" in url:
            # Note: check "&page=1" (not "page=1"), since "per_page=100"
            # itself contains the substring "page=1" and would false-match.
            if "&page=1" in url:
                page = [{"full_name": name} for name in repos]
                return 200, json.dumps(page).encode("utf-8")
            return 200, b"[]"
        if "/contents/" in url:
            for (repo, path), text in files.items():
                if f"/repos/{repo}/contents/{path}" in url:
                    if text is None:
                        return 404, b"Not Found"
                    return 200, json.dumps({"content": _b64(text), "encoding": "base64"}).encode("utf-8")
            return 404, b"Not Found"
        if "pypi.org" in url:
            return 200, json.dumps({"info": {"version": "9.9.9"}}).encode("utf-8")
        if "registry.npmjs.org" in url:
            return 200, json.dumps({"dist-tags": {"latest": "9.9.9"}}).encode("utf-8")
        return 404, b""

    return transport


def test_build_parser_requires_subcommand():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_sync_end_to_end_persists_snapshots(tmp_path):
    db_path = str(tmp_path / "fleet.db")
    repos = ["user/repo-a", "user/repo-b"]
    files = {
        ("user/repo-a", "requirements.txt"): "requests==2.20.0\n",
        ("user/repo-a", "package.json"): None,
        ("user/repo-b", "requirements.txt"): "requests==2.31.0\n",
        ("user/repo-b", "package.json"): None,
    }
    transport = _fake_transport(repos, files)

    exit_code = _sync(db_path, "fake-token", transport=transport)
    assert exit_code == 0

    conn = store.connect(db_path)
    date = store.latest_snapshot_date(conn)
    rows = store.snapshots_for_date(conn, date)
    conn.close()
    assert len(rows) == 2
    versions = {row["repo"]: row["pinned_version"] for row in rows}
    assert versions == {"user/repo-a": "2.20.0", "user/repo-b": "2.31.0"}
    assert all(row["latest_version"] == "9.9.9" for row in rows)


def test_sync_missing_manifest_files_skipped_gracefully(tmp_path):
    db_path = str(tmp_path / "fleet.db")
    repos = ["user/empty-repo"]
    files = {("user/empty-repo", "requirements.txt"): None, ("user/empty-repo", "package.json"): None}
    transport = _fake_transport(repos, files)

    exit_code = _sync(db_path, "fake-token", transport=transport)
    assert exit_code == 0
    conn = store.connect(db_path)
    date = store.latest_snapshot_date(conn)
    conn.close()
    assert date is None


def test_cmd_sync_without_token_env_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    db_path = str(tmp_path / "fleet.db")
    exit_code = main(["--db", db_path, "sync"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "GITHUB_TOKEN" in captured.err


def test_cmd_render_without_prior_sync_fails(tmp_path, capsys):
    db_path = str(tmp_path / "fleet.db")
    output_path = str(tmp_path / "report.html")
    exit_code = main(["--db", db_path, "render", "--output", output_path])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "sync" in captured.out.lower()


def test_cmd_render_writes_html_file(tmp_path):
    db_path = str(tmp_path / "fleet.db")
    conn = store.connect(db_path)
    store.upsert_snapshot(conn, "user/a", "python", "requests", "2.20.0", "exact", "2.31.0", "2026-09-01")
    store.upsert_snapshot(conn, "user/b", "python", "requests", "2.31.0", "exact", "2.31.0", "2026-09-01")
    store.commit(conn)
    conn.close()

    output_path = str(tmp_path / "report.html")
    exit_code = main(["--db", db_path, "render", "--output", output_path])
    assert exit_code == 0
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as handle:
        contents = handle.read()
    assert "Fleet Drift" in contents


def test_cmd_list_prints_drift_summary(tmp_path, capsys):
    db_path = str(tmp_path / "fleet.db")
    conn = store.connect(db_path)
    store.upsert_snapshot(conn, "user/a", "python", "requests", "2.20.0", "exact", "2.31.0", "2026-09-01")
    store.upsert_snapshot(conn, "user/b", "python", "requests", "2.31.0", "exact", "2.31.0", "2026-09-01")
    store.commit(conn)
    conn.close()

    exit_code = main(["--db", db_path, "list"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "requests" in captured.out
    assert "Drifted dependencies: 1" in captured.out


def test_cmd_history_json_output(tmp_path, capsys):
    db_path = str(tmp_path / "fleet.db")
    conn = store.connect(db_path)
    store.upsert_snapshot(conn, "user/a", "python", "requests", "2.20.0", "exact", "2.31.0", "2026-09-01")
    store.commit(conn)
    conn.close()

    exit_code = main(["--db", db_path, "history", "python", "requests", "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1
    assert data[0]["repo"] == "user/a"


def test_cmd_history_no_data_message(tmp_path, capsys):
    db_path = str(tmp_path / "fleet.db")
    exit_code = main(["--db", db_path, "history", "python", "nonexistent"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No history" in captured.out
