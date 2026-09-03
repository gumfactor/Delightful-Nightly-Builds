from pathlib import Path

from src.extract import extract_prompts, iter_session_files, read_jsonl_lines
from tests.helpers import (
    assistant_text_line,
    bookkeeping_line,
    tool_result_line,
    tool_use_line,
    user_prompt,
    write_jsonl,
)


def test_extracts_plain_string_prompt(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    write_jsonl(path, [user_prompt("fix the login bug", prompt_uuid="p1")])
    lines = read_jsonl_lines(path)
    prompts = extract_prompts(lines)
    assert len(prompts) == 1
    assert prompts[0].prompt_text == "fix the login bug"
    assert prompts[0].prompt_uuid == "p1"


def test_extracts_content_block_list_prompt(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    line = user_prompt("placeholder", prompt_uuid="p2")
    line["message"]["content"] = [{"type": "text", "text": "add a new feature"}]
    write_jsonl(path, [line])
    prompts = extract_prompts(read_jsonl_lines(path))
    assert len(prompts) == 1
    assert prompts[0].prompt_text == "add a new feature"


def test_excludes_pure_tool_result_user_turn(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    use_line, tid = tool_use_line("Bash", {"command": "ls"})
    result = tool_result_line(tid, "file1\nfile2")
    write_jsonl(path, [use_line, result])
    prompts = extract_prompts(read_jsonl_lines(path))
    assert prompts == []


def test_excludes_sidechain_turns(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    write_jsonl(path, [user_prompt("subagent internal prompt", is_sidechain=True)])
    prompts = extract_prompts(read_jsonl_lines(path))
    assert prompts == []


def test_excludes_assistant_turns(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    write_jsonl(path, [assistant_text_line("here is my plan")])
    prompts = extract_prompts(read_jsonl_lines(path))
    assert prompts == []


def test_skips_bookkeeping_line_types(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    write_jsonl(
        path,
        [
            bookkeeping_line("queue-operation"),
            bookkeeping_line("attachment"),
            bookkeeping_line("atis-latch"),
            user_prompt("real prompt", prompt_uuid="p3"),
        ],
    )
    prompts = extract_prompts(read_jsonl_lines(path))
    assert len(prompts) == 1
    assert prompts[0].prompt_uuid == "p3"


def test_skips_malformed_json_lines_without_crashing(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    path.write_text(
        '{"broken": \n'
        '{"type": "user", "message": {"role": "user", "content": "ok prompt"}, '
        '"uuid": "p4", "sessionId": "s1", "timestamp": "2026-09-01T00:00:00Z", "cwd": "/x"}\n'
        "\n"
        "not even json\n",
        encoding="utf-8",
    )
    lines = read_jsonl_lines(path)
    prompts = extract_prompts(lines)
    assert len(prompts) == 1
    assert prompts[0].prompt_uuid == "p4"


def test_skips_prompt_missing_required_fields(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    line = user_prompt("no uuid here")
    del line["uuid"]
    write_jsonl(path, [line])
    prompts = extract_prompts(read_jsonl_lines(path))
    assert prompts == []


def test_empty_text_content_excluded(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    write_jsonl(path, [user_prompt("   ")])
    prompts = extract_prompts(read_jsonl_lines(path))
    assert prompts == []


def test_iter_session_files_recurses_and_sorts(tmp_path: Path):
    (tmp_path / "proj-a").mkdir()
    (tmp_path / "proj-b").mkdir()
    write_jsonl(tmp_path / "proj-b" / "s2.jsonl", [user_prompt("second")])
    write_jsonl(tmp_path / "proj-a" / "s1.jsonl", [user_prompt("first")])
    files = list(iter_session_files(tmp_path))
    assert len(files) == 2
    assert files == sorted(files)


def test_iter_session_files_missing_dir_returns_empty(tmp_path: Path):
    files = list(iter_session_files(tmp_path / "does-not-exist"))
    assert files == []


def test_project_field_comes_from_cwd(tmp_path: Path):
    path = tmp_path / "s.jsonl"
    write_jsonl(path, [user_prompt("hi", cwd="/home/user/other-project")])
    prompts = extract_prompts(read_jsonl_lines(path))
    assert prompts[0].project == "/home/user/other-project"
