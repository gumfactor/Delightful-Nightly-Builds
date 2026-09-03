from pathlib import Path

from src.episode import build_episode, episode_bounds
from src.extract import extract_prompts, read_jsonl_lines
from tests.helpers import (
    bash_episode,
    edit_episode,
    tool_result_line,
    tool_use_line,
    user_prompt,
    write_jsonl,
)


def _build_and_get_episode(tmp_path: Path, session_lines: list[dict]) -> "object":
    path = tmp_path / "s.jsonl"
    write_jsonl(path, session_lines)
    lines = read_jsonl_lines(path)
    prompts = extract_prompts(lines)
    assert len(prompts) >= 1
    prompt = prompts[0]
    prompt_indices = [p.line_index for p in prompts]
    start, end = episode_bounds(prompt_indices, prompt.line_index, len(lines))
    return build_episode(lines, start, end)


def test_git_commit_detected(tmp_path: Path):
    session = [user_prompt("commit my changes")] + bash_episode("git commit -m 'fix'", "1 file changed")
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.git_commit is True


def test_test_run_with_pass_signal(tmp_path: Path):
    session = [user_prompt("run the tests")] + bash_episode(
        "python -m pytest tests/ -v", "12 passed in 0.4s"
    )
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.test_run is True
    assert episode.test_passed is True


def test_test_run_with_fail_signal(tmp_path: Path):
    session = [user_prompt("run the tests")] + bash_episode(
        "npm test", "3 passed, 2 failed"
    )
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.test_run is True
    assert episode.test_passed is False


def test_test_run_with_ambiguous_signal(tmp_path: Path):
    session = [user_prompt("run the tests")] + bash_episode("go test ./...", "some noisy output")
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.test_run is True
    assert episode.test_passed is None


def test_edit_with_no_error(tmp_path: Path):
    session = [user_prompt("fix the typo")] + edit_episode("/x/file.py")
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.files_edited == {"/x/file.py"}
    assert episode.unresolved_error is False


def test_error_followed_by_successful_edit_is_resolved(tmp_path: Path):
    use1, tid1 = tool_use_line("Bash", {"command": "python broken.py"})
    err = tool_result_line(tid1, "Traceback (most recent call last):\nValueError", is_error=True)
    session = [user_prompt("fix this")] + [use1, err] + edit_episode("/x/file.py")
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.had_error is True
    assert episode.unresolved_error is False


def test_error_with_nothing_after_is_unresolved(tmp_path: Path):
    use1, tid1 = tool_use_line("Bash", {"command": "python broken.py"})
    err = tool_result_line(tid1, "Error: something went wrong", is_error=True)
    session = [user_prompt("fix this")] + [use1, err]
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.had_error is True
    assert episode.unresolved_error is True


def test_error_followed_by_commit_is_resolved(tmp_path: Path):
    use1, tid1 = tool_use_line("Bash", {"command": "python broken.py"})
    err = tool_result_line(tid1, "Traceback (most recent call last):\nboom", is_error=True)
    session = [user_prompt("fix this")] + [use1, err] + bash_episode("git commit -m done", "ok")
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.unresolved_error is False


def test_tools_used_accumulates_across_episode(tmp_path: Path):
    session = [user_prompt("do several things")] + bash_episode("ls", "a b c") + edit_episode("/x/f.py")
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.tools_used == {"Bash", "Edit"}


def test_bash_commands_are_recorded(tmp_path: Path):
    session = [user_prompt("run stuff")] + bash_episode("echo hi", "hi")
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.bash_commands == ["echo hi"]


def test_episode_bounds_stops_at_next_prompt(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    session = (
        [user_prompt("first prompt", prompt_uuid="p1")]
        + edit_episode("/x/first.py")
        + [user_prompt("second prompt", prompt_uuid="p2")]
        + edit_episode("/x/second.py")
    )
    write_jsonl(path, session)
    lines = read_jsonl_lines(path)
    prompts = extract_prompts(lines)
    assert len(prompts) == 2
    prompt_indices = [p.line_index for p in prompts]

    start0, end0 = episode_bounds(prompt_indices, prompts[0].line_index, len(lines))
    episode0 = build_episode(lines, start0, end0)
    assert episode0.files_edited == {"/x/first.py"}

    start1, end1 = episode_bounds(prompt_indices, prompts[1].line_index, len(lines))
    episode1 = build_episode(lines, start1, end1)
    assert episode1.files_edited == {"/x/second.py"}


def test_episode_with_no_activity_is_all_zero(tmp_path: Path):
    session = [user_prompt("just a question, no tool calls")]
    episode = _build_and_get_episode(tmp_path, session)
    assert episode.tools_used == set()
    assert episode.files_edited == set()
    assert episode.git_commit is False
    assert episode.had_error is False
    assert episode.unresolved_error is False
