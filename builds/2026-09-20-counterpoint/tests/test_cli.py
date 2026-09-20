import pytest

from src import main as main_module
from src.main import main


COMMENTS = """
Reviewer 1
1. Please clarify construct X.
2. Please add a power analysis.

Reviewer 2
1. Fix Figure 3's axis labels.
"""

COMPLETE_RESPONSES = """
[R1C1]
We clarified construct X in Section 2.1.

[R1C2]
We added a post-hoc power analysis.

[R2C1]
Figure 3 has been redrawn with larger labels.
"""

INCOMPLETE_RESPONSES = """
[R1C1]
We clarified construct X in Section 2.1.
"""


def write_inputs(tmp_path, responses_text):
    comments_path = tmp_path / "comments.md"
    responses_path = tmp_path / "responses.txt"
    comments_path.write_text(COMMENTS, encoding="utf-8")
    responses_path.write_text(responses_text, encoding="utf-8")
    return str(comments_path), str(responses_path)


def test_check_exits_zero_when_complete(tmp_path, capsys):
    comments_path, responses_path = write_inputs(tmp_path, COMPLETE_RESPONSES)
    code = main(["check", "--comments", comments_path, "--responses", responses_path])
    out = capsys.readouterr().out
    assert code == 0
    assert "3/3 comments addressed" in out


def test_check_exits_one_when_incomplete(tmp_path, capsys):
    comments_path, responses_path = write_inputs(tmp_path, INCOMPLETE_RESPONSES)
    code = main(["check", "--comments", comments_path, "--responses", responses_path])
    out = capsys.readouterr().out
    assert code == 1
    assert "R1C2" in out
    assert "R2C1" in out


def test_check_raises_system_exit_on_missing_file(tmp_path):
    _, responses_path = write_inputs(tmp_path, COMPLETE_RESPONSES)
    with pytest.raises(SystemExit):
        main(["check", "--comments", str(tmp_path / "nonexistent.md"), "--responses", responses_path])


def test_build_writes_all_three_output_files(tmp_path):
    comments_path, responses_path = write_inputs(tmp_path, COMPLETE_RESPONSES)
    out_dir = tmp_path / "out"
    code = main(
        [
            "build",
            "--comments",
            comments_path,
            "--responses",
            responses_path,
            "--out-dir",
            str(out_dir),
        ]
    )
    assert code == 0
    assert (out_dir / "letter.md").exists()
    assert (out_dir / "letter.html").exists()
    assert (out_dir / "letter.txt").exists()

    markdown = (out_dir / "letter.md").read_text(encoding="utf-8")
    assert "We clarified construct X in Section 2.1." in markdown
    assert "3/3 comments addressed" in markdown


def test_build_refuses_when_incomplete_without_force(tmp_path):
    comments_path, responses_path = write_inputs(tmp_path, INCOMPLETE_RESPONSES)
    out_dir = tmp_path / "out"
    code = main(
        [
            "build",
            "--comments",
            comments_path,
            "--responses",
            responses_path,
            "--out-dir",
            str(out_dir),
        ]
    )
    assert code == 1
    assert not out_dir.exists()


def test_build_with_force_flags_missing_but_still_writes(tmp_path):
    comments_path, responses_path = write_inputs(tmp_path, INCOMPLETE_RESPONSES)
    out_dir = tmp_path / "out"
    code = main(
        [
            "build",
            "--comments",
            comments_path,
            "--responses",
            responses_path,
            "--out-dir",
            str(out_dir),
            "--force",
        ]
    )
    assert code == 0
    markdown = (out_dir / "letter.md").read_text(encoding="utf-8")
    assert "MISSING" in markdown


def test_build_without_ai_flag_never_invokes_polish_with_use_ai_true(tmp_path, monkeypatch):
    calls = []
    real_polish_response = main_module.polish_response

    def spying_polish_response(*args, **kwargs):
        calls.append(kwargs.get("use_ai"))
        return real_polish_response(*args, **kwargs)

    monkeypatch.setattr(main_module, "polish_response", spying_polish_response)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-present-but-unused")

    comments_path, responses_path = write_inputs(tmp_path, COMPLETE_RESPONSES)
    out_dir = tmp_path / "out"
    code = main(
        [
            "build",
            "--comments",
            comments_path,
            "--responses",
            responses_path,
            "--out-dir",
            str(out_dir),
        ]
    )
    assert code == 0
    # Every call must have use_ai=False even though an API key is present in
    # the environment — --ai must be explicitly passed to opt in.
    assert calls == [False, False, False]
