from conftest import assistant, user, write_jsonl
from atlas.parser import parse_session_file, project_label


def test_basic_session_fields(basic_log):
    s = parse_session_file(basic_log)
    assert s.id == "s1" and s.project == "/work/proj" and s.branch == "main"
    assert [p[1] for p in s.prompts] == ["Fix the <b>parser</b> bug"]
    assert s.assistant_msgs == 2 and s.last_assistant == "Fixed it."


def test_tool_result_turns_are_not_prompts_but_errors_are_counted(basic_log):
    s = parse_session_file(basic_log)
    assert len(s.prompts) == 1 and s.tool_errors == 1


def test_edit_tools_track_files_and_tool_counts(basic_log):
    s = parse_session_file(basic_log)
    assert s.files["/work/proj/a.py"] == 1 and s.tools["Edit"] == 1


def test_streamed_duplicate_message_ids_count_usage_once(tmp_path):
    first = {"input_tokens": 100, "output_tokens": 5}
    final = {"input_tokens": 100, "output_tokens": 80}
    path = write_jsonl(tmp_path / "s.jsonl", [
        user("2026-09-01T10:00:00Z", "hi"),
        assistant("2026-09-01T10:00:01Z", [{"type": "text", "text": "a"}], "dup", usage=first),
        assistant("2026-09-01T10:00:02Z", [{"type": "text", "text": "ab"}], "dup", usage=final),
    ])
    s = parse_session_file(path)
    assert s.total("input") == 100 and s.total("output") == 80


def test_malformed_and_blank_lines_are_skipped(tmp_path):
    path = write_jsonl(tmp_path / "s.jsonl", ["{not json", "", "[1,2]", user("2026-09-01T10:00:00Z", "ok")])
    s = parse_session_file(path)
    assert len(s.prompts) == 1


def test_file_without_turns_returns_none(tmp_path):
    path = write_jsonl(tmp_path / "s.jsonl", [{"type": "summary", "summary": "x"}, {"type": "system"}])
    assert parse_session_file(path) is None


def test_idle_gaps_are_not_counted_as_active_time(tmp_path):
    path = write_jsonl(tmp_path / "s.jsonl", [
        user("2026-09-01T10:00:00Z", "a"),
        assistant("2026-09-01T10:01:00Z", [{"type": "text", "text": "b"}]),
        user("2026-09-01T12:00:00Z", "c"),  # two hours idle
        assistant("2026-09-01T12:00:30Z", [{"type": "text", "text": "d"}], "m2"),
    ])
    s = parse_session_file(path, idle_gap_seconds=300)
    assert s.active_seconds == 90
    assert s.start.startswith("2026-09-01T10:00") and s.end.startswith("2026-09-01T12:00:30")


def test_meta_sidechain_and_command_noise_excluded_from_prompts(tmp_path):
    path = write_jsonl(tmp_path / "s.jsonl", [
        user("2026-09-01T10:00:00Z", "real prompt"),
        user("2026-09-01T10:00:01Z", "meta text", isMeta=True),
        user("2026-09-01T10:00:02Z", "<command-name>/clear</command-name>"),
        user("2026-09-01T10:00:03Z", "subagent prompt", isSidechain=True),
        user("2026-09-01T10:00:04Z", "Caveat: injected"),
    ])
    s = parse_session_file(path)
    assert [p[1] for p in s.prompts] == ["real prompt"] and s.sidechain_msgs == 1


def test_sidechain_assistant_messages_do_not_become_last_assistant(tmp_path):
    path = write_jsonl(tmp_path / "s.jsonl", [
        user("2026-09-01T10:00:00Z", "go"),
        assistant("2026-09-01T10:00:05Z", [{"type": "text", "text": "main answer"}], "m1"),
        assistant("2026-09-01T10:00:06Z", [{"type": "text", "text": "subagent chatter"}], "m2", isSidechain=True),
    ])
    s = parse_session_file(path)
    assert s.last_assistant == "main answer" and s.assistant_msgs == 1 and s.sidechain_msgs == 1


def test_summary_record_sets_title(tmp_path):
    path = write_jsonl(tmp_path / "s.jsonl", [{"type": "summary", "summary": "Parser rework"},
                                              user("2026-09-01T10:00:00Z", "x")])
    assert parse_session_file(path).title == "Parser rework"


def test_bad_timestamps_do_not_crash(tmp_path):
    path = write_jsonl(tmp_path / "s.jsonl", [user("garbage", "x"), user(None, "y")])
    s = parse_session_file(path)
    assert len(s.prompts) == 2 and s.start == "" and s.active_seconds == 0


def test_project_label_handles_windows_and_trailing_slash():
    assert project_label("C:\\work\\lab-stats\\") == "lab-stats"
    assert project_label("") == "(unknown)"
