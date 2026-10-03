from atlas.stats import build_stats, cache_hit_ratio, resume_prompt


def make(**over):
    base = {"id": "s", "project": "p", "project_path": "/w/p", "branch": "main", "start": "2026-09-07T14:30:00+00:00",
            "active_seconds": 3600, "prompts": 5, "cost_usd": 1.5, "unpriced": False, "input_tokens": 10,
            "output_tokens": 20, "cache_write_tokens": 0, "cache_read_tokens": 70, "tool_errors": 1,
            "tools": {"Edit": 3}, "files": {"/w/p/a.py": 5, "/w/p/b.py": 1}, "models": {"claude-sonnet-4-5": {"input": 10}},
            "title": "", "summary": "", "first_prompt": "start here", "last_prompt": "finish there",
            "last_assistant": "all done"}
    base.update(over)
    return base


def test_totals_and_cache_ratio():
    stats = build_stats([make(), make(id="t")])
    assert stats["totals"]["sessions"] == 2 and stats["totals"]["hours"] == 2.0
    assert stats["totals"]["cache_hit"] == 0.875 and stats["totals"]["cost"] == 3.0


def test_heatmap_uses_timezone_offset():
    # Monday 2026-09-07 14:30 UTC is 10:30 in UTC-4
    stats = build_stats([make()], tz_offset_hours=-4)
    assert stats["heatmap"][0][10] == 5 and stats["daily"][0]["date"] == "2026-09-07"


def test_timezone_can_shift_the_calendar_day():
    stats = build_stats([make(start="2026-09-07T01:00:00+00:00")], tz_offset_hours=-4)
    assert stats["daily"][0]["date"] == "2026-09-06"


def test_project_rollup_sorted_by_hours():
    stats = build_stats([make(project="a", active_seconds=100), make(project="b", active_seconds=9000)])
    assert [p["project"] for p in stats["projects"]] == ["b", "a"]


def test_churn_detects_only_files_edited_repeatedly():
    churn = build_stats([make()])["churn"]
    assert [c["file"] for c in churn] == ["/w/p/a.py"]


def test_unpriced_flag_propagates_and_empty_input_is_safe():
    assert build_stats([make(unpriced=True)])["totals"]["unpriced"] is True
    empty = build_stats([])
    assert empty["totals"]["sessions"] == 0 and empty["daily"] == [] and empty["totals"]["cache_hit"] == 0


def test_sessions_with_blank_start_are_counted_but_not_bucketed():
    stats = build_stats([make(start="")])
    assert stats["totals"]["sessions"] == 1 and stats["daily"] == []


def test_cache_hit_ratio_zero_denominator():
    assert cache_hit_ratio(0, 0, 0) == 0.0


def test_resume_prompt_contains_real_context():
    text = resume_prompt(make(summary="Parser half done"))
    for needle in ("/w/p", "main", "start here", "finish there", "a.py (5x)", "all done", "Parser half done"):
        assert needle in text


def test_resume_prompt_omits_duplicate_last_prompt():
    assert "My last request" not in resume_prompt(make(last_prompt="start here"))
