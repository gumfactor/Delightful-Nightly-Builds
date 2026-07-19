import io
import json

import pytest

from src import cli
from tests.factories import make_study_dict


def run_cli(argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    code = cli.main(argv, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


@pytest.fixture(autouse=True)
def _no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _write_study(path, **overrides):
    path.write_text(json.dumps(make_study_dict(**overrides)))
    return path


def test_init_creates_template(tmp_path):
    target = tmp_path / "study.json"
    code, out, _err = run_cli(["init", str(target)])
    assert code == 0
    assert target.exists()
    data = json.loads(target.read_text())
    assert "title" in data
    assert "Wrote study template" in out


def test_init_refuses_overwrite_without_force(tmp_path):
    target = tmp_path / "study.json"
    target.write_text("{}")
    code, _out, err = run_cli(["init", str(target)])
    assert code == 1
    assert "already exists" in err


def test_init_force_overwrites(tmp_path):
    target = tmp_path / "study.json"
    target.write_text("{}")
    code, _out, _err = run_cli(["init", str(target), "--force"])
    assert code == 0
    data = json.loads(target.read_text())
    assert "title" in data


def test_check_missing_file_errors(tmp_path):
    code, _out, err = run_cli(["check", str(tmp_path / "nope.json")])
    assert code == 1
    assert "Error" in err


def test_check_malformed_json_errors(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    code, _out, err = run_cli(["check", str(bad)])
    assert code == 1
    assert "Error" in err


def test_check_clean_study_exits_zero(tmp_path):
    study_file = _write_study(tmp_path / "study.json")
    code, out, _err = run_cli(["check", str(study_file)])
    assert code == 0
    assert "Completeness score: 100/100" in out
    assert "No compliance issues found." in out


def test_check_flagged_study_exits_nonzero_and_reports_json(tmp_path):
    study_file = _write_study(tmp_path / "study.json", deception=True, deception_debrief="")
    code, out, _err = run_cli(["check", str(study_file), "--json"])
    assert code == 1
    payload = json.loads(out)
    codes = {f["code"] for f in payload["findings"]}
    assert "deception_without_debrief" in codes


def test_draft_end_to_end_no_api_key(tmp_path):
    study_file = _write_study(tmp_path / "study.json")
    out_md = tmp_path / "draft.md"
    db_path = tmp_path / "lib.db"

    code, out, _err = run_cli(
        ["draft", str(study_file), "--out", str(out_md), "--db", str(db_path)]
    )
    assert code == 0
    assert out_md.exists()
    content = out_md.read_text()
    assert "Compliance Check Summary" in content
    assert "Completeness score: 100/100" in out
    assert "Saved protocol #1" in out


def test_draft_defaults_output_filename_from_title(tmp_path, monkeypatch):
    study_file = _write_study(tmp_path / "study.json", title="A Totally New Study!")
    db_path = tmp_path / "lib.db"
    monkeypatch.chdir(tmp_path)

    code, _out, _err = run_cli(["draft", str(study_file), "--db", str(db_path)])
    assert code == 0
    assert (tmp_path / "a-totally-new-study.md").exists()


def test_list_empty_library(tmp_path):
    db_path = tmp_path / "lib.db"
    code, out, _err = run_cli(["list", "--db", str(db_path)])
    assert code == 0
    assert "No protocols" in out


def test_list_shows_saved_protocols(tmp_path):
    study_file = _write_study(tmp_path / "study.json")
    db_path = tmp_path / "lib.db"
    run_cli(["draft", str(study_file), "--out", str(tmp_path / "d.md"), "--db", str(db_path)])

    code, out, _err = run_cli(["list", "--db", str(db_path)])
    assert code == 0
    assert "#1" in out
    assert "[draft]" in out


def test_show_unknown_id_errors(tmp_path):
    db_path = tmp_path / "lib.db"
    code, _out, err = run_cli(["show", "999", "--db", str(db_path)])
    assert code == 1
    assert "Error" in err


def test_show_known_id_prints_content(tmp_path):
    study_file = _write_study(tmp_path / "study.json")
    db_path = tmp_path / "lib.db"
    run_cli(["draft", str(study_file), "--out", str(tmp_path / "d.md"), "--db", str(db_path)])

    code, out, _err = run_cli(["show", "1", "--db", str(db_path)])
    assert code == 0
    assert "Effects of Time Pressure" in out
    assert "source:" in out


def test_approve_unknown_id_errors(tmp_path):
    db_path = tmp_path / "lib.db"
    code, _out, err = run_cli(["approve", "999", "--db", str(db_path)])
    assert code == 1
    assert "Error" in err


def test_approve_then_reuse_across_protocols(tmp_path):
    db_path = tmp_path / "lib.db"

    study_a_file = _write_study(tmp_path / "study_a.json")
    (tmp_path / "study_a.json").write_text(
        json.dumps(
            {
                **make_study_dict(),
                "population": {
                    "description": "Adults 18-65",
                    "vulnerable_groups": ["minors"],
                },
                "procedures": "Task with minor participants; assent and parental consent obtained.",
            }
        )
    )
    code, _out, _err = run_cli(
        ["draft", str(study_a_file), "--out", str(tmp_path / "a.md"), "--db", str(db_path)]
    )
    assert code == 0

    approve_code, _out, _err = run_cli(["approve", "1", "--db", str(db_path)])
    assert approve_code == 0

    study_b_file = tmp_path / "study_b.json"
    study_b_file.write_text(
        json.dumps(
            {
                **make_study_dict(title="A Second, Similar Study"),
                "population": {
                    "description": "Adults 18-65, second cohort",
                    "vulnerable_groups": ["minors"],
                },
                "procedures": "Task with minor participants; assent and parental consent obtained.",
            }
        )
    )
    out_b = tmp_path / "b.md"
    code_b, out_b_stdout, _err = run_cli(
        ["draft", str(study_b_file), "--out", str(out_b), "--db", str(db_path)]
    )
    assert code_b == 0
    assert "Saved protocol #2" in out_b_stdout

    content_b = out_b.read_text()
    assert "reused from protocol #1" in content_b
