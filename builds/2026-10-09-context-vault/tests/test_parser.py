from conftest import write_jsonl

from ctxvault.parser import parse_session, project_name


def rec(role, content, **extra):
    base = {"type": role, "sessionId": "s1", "cwd": "/w/proj", "timestamp": "2026-01-01T10:00:00Z",
            "message": {"role": role, "content": content}}
    base.update(extra)
    return base


def test_string_and_block_content_are_both_extracted(tmp_path):
    f = tmp_path / "-w-proj" / "s1.jsonl"
    write_jsonl(f, [rec("user", "hello there"),
                    rec("assistant", [{"type": "text", "text": "hi back"}])])
    s = parse_session(f)
    assert [m.text for m in s.messages] == ["hello there", "hi back"]
    assert s.project == "proj" and s.cwd == "/w/proj"


def test_malformed_lines_and_non_objects_are_skipped(tmp_path):
    f = tmp_path / "d" / "s.jsonl"
    write_jsonl(f, ["{not json", "[1,2]", "", rec("user", "real")])
    assert len(parse_session(f).messages) == 1


def test_tool_use_file_paths_counted_and_tool_results_not_indexed(tmp_path):
    f = tmp_path / "d" / "s.jsonl"
    write_jsonl(f, [
        rec("user", "go"),
        rec("assistant", [{"type": "text", "text": "editing"},
                          {"type": "tool_use", "name": "Edit", "input": {"file_path": "/a/b.py"}},
                          {"type": "tool_use", "name": "Edit", "input": {"file_path": "/a/b.py"}},
                          {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]),
        rec("user", [{"type": "tool_result", "content": "SECRET OUTPUT"}]),
    ])
    s = parse_session(f)
    assert s.files == {"/a/b.py": 2}
    assert all("SECRET" not in m.text for m in s.messages)


def test_meta_sidechain_and_command_noise_skipped(tmp_path):
    f = tmp_path / "d" / "s.jsonl"
    write_jsonl(f, [rec("user", "meta", isMeta=True), rec("user", "side", isSidechain=True),
                    rec("user", "<command-name>/clear</command-name>"), rec("user", "kept")])
    assert [m.text for m in parse_session(f).messages] == ["kept"]


def test_summary_line_becomes_hint_title(tmp_path):
    f = tmp_path / "d" / "s.jsonl"
    write_jsonl(f, [{"type": "summary", "summary": "Fix the dedupe bug"}, rec("user", "x")])
    assert parse_session(f).hint_title == "Fix the dedupe bug"


def test_file_without_conversation_returns_none(tmp_path):
    f = tmp_path / "d" / "s.jsonl"
    write_jsonl(f, [{"type": "summary", "summary": "only"}])
    assert parse_session(f) is None


def test_project_name_handles_windows_paths_and_fallback():
    assert project_name("C:\\Users\\me\\lab-tools", "x") == "lab-tools"
    assert project_name("", "-home-user-thing") == "thing"
