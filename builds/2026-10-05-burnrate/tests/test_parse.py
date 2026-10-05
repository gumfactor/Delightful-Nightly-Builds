from burnrate.parse import ScanStats, load_sessions, parse_ts, tool_key

from conftest import assistant, at, result


def test_streamed_duplicates_counted_once_with_max_usage(write_transcript):
    root = write_transcript([
        assistant(msg_id="m1", usage=(100, 5, 0, 0)),
        assistant(msg_id="m1", usage=(100, 80, 0, 0)),
    ])
    sessions, stats = load_sessions(root)
    assert len(sessions[0].turns) == 1
    assert sessions[0].turns[0].output == 80
    assert stats.assistant_entries == 2


def test_malformed_lines_are_counted_not_fatal(write_transcript):
    root = write_transcript([assistant()], raw_lines=["{broken", "[1,2]", ""])
    sessions, stats = load_sessions(root)
    assert len(sessions) == 1
    assert stats.bad_lines == 2


def test_assistant_without_usage_is_skipped(write_transcript):
    entry = assistant()
    del entry["message"]["usage"]
    sessions, stats = load_sessions(write_transcript([entry]))
    assert sessions == [] and stats.no_usage == 1


def test_sidechain_flag_and_project_from_cwd(write_transcript):
    sessions, _ = load_sessions(write_transcript([assistant(sidechain=True, cwd="/home/x/kwyeter/")]))
    assert sessions[0].turns[0].sidechain and sessions[0].project == "kwyeter"


def test_tool_results_link_to_tool_use(write_transcript):
    rows = [assistant(tools=[("t1", "Bash", {"command": "ls"})]), result("t1", True)]
    sessions, _ = load_sessions(write_transcript(rows))
    assert sessions[0].results == {"t1": True}


def test_turns_sorted_by_time_across_files(write_transcript):
    root = write_transcript([assistant(msg_id="late", ts=at(10))], name="a.jsonl")
    write_transcript([assistant(msg_id="early", ts=at(1))], name="b.jsonl")
    sessions, _ = load_sessions(root)
    assert [t.ts for t in sessions[0].turns] == sorted(t.ts for t in sessions[0].turns)


def test_negative_and_non_integer_usage_ignored(write_transcript):
    entry = assistant()
    entry["message"]["usage"] = {"input_tokens": -5, "output_tokens": "x", "cache_read_input_tokens": True}
    sessions, _ = load_sessions(write_transcript([entry]))
    turn = sessions[0].turns[0]
    assert (turn.input, turn.output, turn.cache_read) == (0, 0, 0)


def test_missing_root_returns_nothing(tmp_path):
    sessions, stats = load_sessions(tmp_path / "nope")
    assert sessions == [] and stats.files == 0


def test_parse_ts_handles_z_suffix_and_garbage():
    assert parse_ts("2026-10-01T12:00:00Z").hour == 12
    assert parse_ts("yesterday") is None and parse_ts(None) is None


def test_tool_key_prefers_path_then_command():
    assert tool_key("Read", {"file_path": "/a"}) == "/a"
    assert tool_key("Bash", {"command": "ls"}) == "ls"
    assert tool_key("X", {"b": 1, "a": 2}) == '{"a": 2, "b": 1}'
