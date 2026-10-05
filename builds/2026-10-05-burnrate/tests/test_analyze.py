from datetime import timedelta

import pytest

from burnrate.analyze import active_seconds, analyze
from burnrate.parse import load_sessions
from burnrate.pricing import PriceTable

from conftest import BASE, assistant, at, result

PRICES = PriceTable({"sonnet": {"input": 3, "output": 15}})


def run(root, **kwargs):
    sessions, stats = load_sessions(root)
    return analyze(sessions, stats, PRICES, **kwargs)


def kinds(res):
    return {f["kind"] for f in res["findings"]}


def test_cost_and_cache_savings(write_transcript):
    res = run(write_transcript([assistant(usage=(0, 0, 0, 1_000_000))]))
    assert res["totals"]["cost"] == pytest.approx(0.3)
    assert res["totals"]["saved_by_cache"] == pytest.approx(2.7)
    assert res["totals"]["cache_hit"] == 1.0


def test_day_bucket_respects_timezone(write_transcript):
    rows = [assistant(ts=BASE.replace(day=2, hour=2))]  # 02:00 UTC = 22:00 previous day in Toronto
    assert run(write_transcript(rows), tz_name="America/Toronto")["by_day"][0]["day"] == "2026-10-01"
    assert run(write_transcript(rows), tz_name="UTC")["by_day"][0]["day"] == "2026-10-02"


def test_read_thrash_fires_at_three_not_two(write_transcript):
    def reads(n):
        return [assistant(msg_id=f"m{i}", ts=at(i), tools=[(f"t{i}", "Read", {"file_path": "/a.py"})]) for i in range(n)]
    assert "read_thrash" in kinds(run(write_transcript(reads(3))))
    assert "read_thrash" not in kinds(run(write_transcript(reads(2))))


def test_retry_loop_requires_repeated_failures(write_transcript):
    rows = []
    for i in range(3):
        rows += [assistant(msg_id=f"m{i}", ts=at(i), tools=[(f"t{i}", "Bash", {"command": "make"})]), result(f"t{i}", True)]
    assert "retry_loop" in kinds(run(write_transcript(rows)))
    ok = [r if r["type"] == "assistant" else result(r["message"]["content"][0]["tool_use_id"], False) for r in rows]
    assert "retry_loop" not in kinds(run(write_transcript(ok)))


def test_low_cache_needs_volume_and_low_ratio(write_transcript):
    cold = [assistant(msg_id="m", usage=(250_000, 10, 0, 1000))]
    assert "low_cache" in kinds(run(write_transcript(cold)))
    tiny = [assistant(msg_id="m", usage=(2000, 10, 0, 0))]
    assert "low_cache" not in kinds(run(write_transcript(tiny)))
    warm = [assistant(msg_id="m", usage=(10_000, 10, 0, 300_000))]
    assert "low_cache" not in kinds(run(write_transcript(warm)))


def test_big_context_threshold(write_transcript):
    assert "big_context" in kinds(run(write_transcript([assistant(usage=(1, 1, 0, 160_000))])))
    assert "big_context" not in kinds(run(write_transcript([assistant(usage=(1, 1, 0, 100_000))])))


def test_high_error_rate_needs_minimum_calls(write_transcript):
    def build(n):
        rows = []
        for i in range(n):
            rows += [assistant(msg_id=f"m{i}", ts=at(i), tools=[(f"t{i}", "Grep", {"pattern": str(i)})]), result(f"t{i}", True)]
        return rows
    assert "high_error_rate" in kinds(run(write_transcript(build(10))))
    assert "high_error_rate" not in kinds(run(write_transcript(build(5))))


def test_unknown_model_reported_and_not_costed(write_transcript):
    res = run(write_transcript([assistant(model="mystery-1", usage=(1_000_000, 0, 0, 0))]))
    assert res["unpriced_models"] == ["mystery-1"] and res["totals"]["cost"] == 0
    assert "unpriced_model" in kinds(res)


def test_since_filters_old_turns(write_transcript):
    root = write_transcript([assistant(msg_id="old", ts=BASE - timedelta(days=30)), assistant(msg_id="new", ts=BASE)])
    sessions, stats = load_sessions(root)
    res = analyze(sessions, stats, PRICES, since=BASE - timedelta(days=1))
    assert res["totals"]["turns"] == 1


def test_active_time_ignores_long_gaps(write_transcript):
    sessions, _ = load_sessions(write_transcript([
        assistant(msg_id="a", ts=at(0)), assistant(msg_id="b", ts=at(3)), assistant(msg_id="c", ts=at(120))]))
    assert active_seconds(sessions[0].turns) == 180


def test_sidechain_share(write_transcript):
    rows = [assistant(msg_id="a", usage=(100, 0, 0, 0), sidechain=True), assistant(msg_id="b", ts=at(1), usage=(300, 0, 0, 0))]
    assert run(write_transcript(rows))["totals"]["sidechain_share"] == pytest.approx(0.25)
