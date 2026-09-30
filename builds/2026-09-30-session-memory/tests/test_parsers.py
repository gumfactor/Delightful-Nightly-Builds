import json

from conftest import EXAMPLES, cc_record, write_jsonl
from sessionmemory import parsers


def test_claude_code_extracts_text_files_and_project(tmp_path):
    path = write_jsonl(tmp_path / "a.jsonl", [
        cc_record("user", "Fix the loader"),
        cc_record("assistant", [{"type": "text", "text": "Done"},
                                {"type": "tool_use", "name": "Edit", "input": {"file_path": "src/load.py"}},
                                {"type": "tool_use", "name": "Read", "input": {"file_path": "src/other.py"}}]),
    ])
    session = parsers.parse_claude_code(path)
    assert session.project == "demo" and session.branch == "main"
    assert [m.role for m in session.messages] == ["user", "assistant"]
    assert session.files == ["src/load.py"]  # Read is not an edit
    assert session.title == "Fix the loader"


def test_tool_result_only_turns_are_skipped(tmp_path):
    path = write_jsonl(tmp_path / "a.jsonl", [
        cc_record("user", "hello"),
        cc_record("user", [{"type": "tool_result", "content": "huge output"}]),
    ])
    assert len(parsers.parse_claude_code(path).messages) == 1


def test_system_reminders_and_meta_records_are_stripped(tmp_path):
    path = write_jsonl(tmp_path / "a.jsonl", [
        cc_record("user", "real question <system-reminder>secret injected text</system-reminder>"),
        cc_record("user", "meta noise", isMeta=True),
    ])
    session = parsers.parse_claude_code(path)
    assert session.messages[0].text == "real question"
    assert len(session.messages) == 1


def test_malformed_lines_are_ignored(tmp_path):
    path = write_jsonl(tmp_path / "a.jsonl", ["{not json", "[1,2]", cc_record("user", "ok")])
    assert len(parsers.parse_claude_code(path).messages) == 1


def test_empty_or_unreadable_transcript_returns_none(tmp_path):
    empty = write_jsonl(tmp_path / "e.jsonl", [{"type": "queue-operation"}])
    assert parsers.parse_claude_code(empty) is None
    assert parsers.parse_claude_code(tmp_path / "missing.jsonl") is None


def test_summary_record_becomes_title(tmp_path):
    path = write_jsonl(tmp_path / "a.jsonl", [{"type": "summary", "summary": "Named session"}, cc_record("user", "x")])
    assert parsers.parse_claude_code(path).title == "Named session"


def test_project_falls_back_to_directory_name(tmp_path):
    record = cc_record("user", "hi")
    del record["cwd"]
    folder = tmp_path / "-home-me-labwork"
    folder.mkdir()
    session = parsers.parse_claude_code(write_jsonl(folder / "a.jsonl", [record]))
    assert session.project == "labwork"


def test_claude_ai_export_roles_and_project():
    sessions = parsers.parse_claude_ai(EXAMPLES / "claude_ai_export.json")
    assert len(sessions) == 1
    assert [m.role for m in sessions[0].messages] == ["user", "assistant"]
    assert sessions[0].source == "claude-ai" and sessions[0].project == "claude.ai chats"


def test_chatgpt_tree_is_linearised_in_order():
    session = parsers.parse_chatgpt(EXAMPLES / "chatgpt_export.json")[0]
    assert [m.role for m in session.messages] == ["user", "assistant"]
    assert session.messages[0].ts.startswith("2026")


def test_chatgpt_branch_follows_current_node(tmp_path):
    def node(i, parent, role, text):
        return {"id": i, "parent": parent, "message": {"author": {"role": role}, "content": {"parts": [text]}}}
    mapping = {"r": {"id": "r", "parent": None, "message": None}, "a": node("a", "r", "user", "q"),
               "b1": node("b1", "a", "assistant", "abandoned"), "b2": node("b2", "a", "assistant", "kept")}
    path = tmp_path / "c.json"
    path.write_text(json.dumps([{"id": "x", "title": "t", "current_node": "b2", "mapping": mapping}]))
    texts = [m.text for m in parsers.parse_chatgpt(path)[0].messages]
    assert texts == ["q", "kept"]


def test_parse_file_dispatches_and_rejects_unknown_json(tmp_path):
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"hello": "world"}))
    assert parsers.parse_file(other) == []
    assert len(parsers.parse_file(EXAMPLES / "chatgpt_export.json")) == 1


def test_discover_walks_folder_for_all_three_sources():
    sources = {s.source for s in parsers.discover([EXAMPLES])}
    assert sources == {"claude-code", "claude-ai", "chatgpt"}
