from pathlib import Path

import secretsweep
from src import db

AWS_KEY = "AKIAABCDEFGHIJKLMNOP"


def test_scan_command_persists_finding_to_db(git_repo, tmp_path):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add key")
    db_path = str(tmp_path / "findings.db")

    exit_code = secretsweep.main(["--db", db_path, "scan", git_repo.as_posix()])

    assert exit_code == 0
    conn = db.connect(db_path)
    rows = db.get_findings(conn)
    assert len(rows) == 1
    assert rows[0]["severity"] == "critical"


def test_scan_command_on_non_git_directory_returns_exit_code_1(tmp_path):
    not_a_repo = tmp_path / "plain_dir"
    not_a_repo.mkdir()
    db_path = str(tmp_path / "findings.db")

    exit_code = secretsweep.main(["--db", db_path, "scan", str(not_a_repo)])

    assert exit_code == 1


def test_rescanning_repo_via_cli_does_not_duplicate_findings(git_repo, tmp_path):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add key")
    db_path = str(tmp_path / "findings.db")

    secretsweep.main(["--db", db_path, "scan", git_repo.as_posix()])
    secretsweep.main(["--db", db_path, "scan", git_repo.as_posix()])

    conn = db.connect(db_path)
    assert len(db.get_findings(conn)) == 1


def test_ack_command_marks_finding_acknowledged(git_repo, tmp_path):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add key")
    db_path = str(tmp_path / "findings.db")
    secretsweep.main(["--db", db_path, "scan", git_repo.as_posix()])

    conn = db.connect(db_path)
    finding_id = db.get_findings(conn)[0]["id"]

    exit_code = secretsweep.main(["--db", db_path, "ack", str(finding_id)])

    assert exit_code == 0
    assert db.get_findings(conn, status="acknowledged")[0]["id"] == finding_id


def test_ack_command_on_unknown_id_returns_exit_code_1(tmp_path):
    db_path = str(tmp_path / "findings.db")
    db.connect(db_path)  # create empty db
    exit_code = secretsweep.main(["--db", db_path, "ack", "12345"])
    assert exit_code == 1


def test_report_command_writes_html_file(git_repo, tmp_path):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add key")
    db_path = str(tmp_path / "findings.db")
    secretsweep.main(["--db", db_path, "scan", git_repo.as_posix()])

    output_path = tmp_path / "report.html"
    exit_code = secretsweep.main(
        ["--db", db_path, "report", "--format", "html", "--output", str(output_path)]
    )

    assert exit_code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "Secret Sweep Report" in html
    assert AWS_KEY not in html


def test_report_command_json_format(git_repo, tmp_path):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add key")
    db_path = str(tmp_path / "findings.db")
    secretsweep.main(["--db", db_path, "scan", git_repo.as_posix()])

    output_path = tmp_path / "report.json"
    secretsweep.main(["--db", db_path, "report", "--format", "json", "--output", str(output_path)])

    content = output_path.read_text(encoding="utf-8")
    assert '"pattern_name": "AWS Access Key ID"' in content
    assert AWS_KEY not in content


def test_list_command_filters_by_severity(git_repo, tmp_path, capsys):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add key")
    db_path = str(tmp_path / "findings.db")
    secretsweep.main(["--db", db_path, "scan", git_repo.as_posix()])
    capsys.readouterr()  # discard scan output

    secretsweep.main(["--db", db_path, "list", "--severity", "high"])
    out = capsys.readouterr().out
    assert "No findings" in out

    secretsweep.main(["--db", db_path, "list", "--severity", "critical"])
    out = capsys.readouterr().out
    assert "AWS Access Key ID" in out
