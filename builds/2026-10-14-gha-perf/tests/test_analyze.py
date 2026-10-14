import pytest

from conftest import NOW, make_job, make_run, make_step
from gha_perf.analyze import (aggregate_steps, analyze, estimate_run_minutes, find_flaky, job_billable_minutes,
                              percentile, runner_multiplier, weekly_trend)


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([1, 2, 3, 4], 95) == pytest.approx(3.85)
    assert percentile([], 50) == 0.0
    assert percentile([7], 95) == 7


@pytest.mark.parametrize("labels,seconds,expected", [
    (["ubuntu-latest"], 61, 2),
    (["windows-latest"], 59, 2),
    (["macos-14"], 100, 20),
    (["ubuntu-latest"], 0, 0),
    (["self-hosted", "Windows"], 60, 2),
])
def test_job_billable_minutes_rounds_up_and_applies_multiplier(labels, seconds, expected):
    assert job_billable_minutes(make_job(labels=labels, seconds=seconds)) == expected


def test_runner_multiplier_defaults_to_linux():
    assert runner_multiplier([]) == 1


def test_estimate_uses_exact_jobs_then_workflow_average_then_wallclock():
    exact = make_run(1, jobs=[make_job(1, seconds=61), make_job(1, labels=["macos-14"], seconds=30)])  # 2 + 10
    unsampled_same_wf = make_run(2, seconds=300)
    other_wf = make_run(3, workflow="Lint", seconds=125)  # 3 wall minutes
    minutes = estimate_run_minutes([exact, unsampled_same_wf, other_wf])
    assert minutes == {1: 12.0, 2: 12.0, 3: 3.0}


def test_flaky_detects_fail_then_pass_on_same_sha_and_rerun_success():
    runs = [
        make_run(1, conclusion="failure", sha="aaa"), make_run(2, conclusion="success", sha="aaa"),
        make_run(3, conclusion="success", sha="bbb", attempt=2),
        make_run(4, conclusion="failure", sha="ccc"),  # plain failure, not flaky
        make_run(5, conclusion="success", sha="ddd"),
    ]
    flaky = find_flaky(runs)
    assert len(flaky) == 1 and flaky[0]["incidents"] == 2


def test_aggregate_steps_ranks_by_total_and_skips_boring_and_skipped():
    steps = [make_step("Set up job", 5), make_step("npm ci", 80), make_step("Run tests", 20), make_step("Deploy", 99, "skipped")]
    runs = [make_run(i, jobs=[make_job(i, steps=list(steps))]) for i in (1, 2)]
    rows = aggregate_steps(runs)
    assert [r["step"] for r in rows] == ["npm ci", "Run tests"]
    assert rows[0]["total_s"] == 160 and rows[0]["count"] == 2 and rows[0]["mean_s"] == 80


def test_weekly_trend_buckets_runs_and_ignores_out_of_window():
    runs = [make_run(1, days_ago=1), make_run(2, days_ago=2, conclusion="failure"), make_run(3, days_ago=9), make_run(4, days_ago=100)]
    minutes = {1: 2.0, 2: 3.0, 3: 4.0, 4: 99.0}
    trend = weekly_trend(runs, minutes, NOW, 2)
    assert [b["runs"] for b in trend] == [1, 2]
    assert trend[1]["failed"] == 1 and trend[1]["fail_rate"] == 0.5 and trend[1]["minutes"] == 5.0


def test_analyze_totals_wasted_minutes_and_rates():
    runs = [make_run(1, seconds=120), make_run(2, conclusion="failure", seconds=180), make_run(3, conclusion="cancelled", seconds=60)]
    report = analyze(runs, 30, NOW)
    summary = report["summary"]
    assert summary["billable_min"] == 6 and summary["wasted_min"] == 4  # 2 + 3 + 1, waste = 3 + 1
    assert summary["fail_rate"] == pytest.approx(0.333, abs=0.001)
    assert report["workflows"][0]["p50_s"] == 120


def test_findings_flag_high_failure_rate_and_cancelled_runs():
    runs = [make_run(i, conclusion="failure") for i in range(1, 5)] + [make_run(5), make_run(6, conclusion="cancelled"),
                                                                       make_run(7, conclusion="cancelled")]
    titles = [f["title"] for f in analyze(runs, 30, NOW)["findings"]]
    assert any("of runs fail" in t for t in titles) and any("cancelled" in t for t in titles)


def test_findings_flag_slow_install_step_with_cache_hint_depending_on_cache_step():
    slow = [make_step("Install dependencies", 120)]
    uncached = [make_run(i, jobs=[make_job(i, steps=list(slow))]) for i in (1, 2, 3)]
    advice = [f["advice"] for f in analyze(uncached, 30, NOW)["findings"] if "Slow install" in f["title"]]
    assert advice and "No cache step seen" in advice[0]
    cached = [make_run(i, jobs=[make_job(i, steps=slow + [make_step("Cache deps", 2)])]) for i in (1, 2, 3)]
    advice = [f["advice"] for f in analyze(cached, 30, NOW)["findings"] if "Slow install" in f["title"]]
    assert "cache step exists" in advice[0]


def test_findings_flag_expensive_runners_and_erratic_duration():
    mac = [make_run(i, jobs=[make_job(i, labels=["macos-14"], seconds=300)]) for i in range(1, 3)]  # 50 min each
    assert any("Windows/macOS" in f["title"] for f in analyze(mac, 30, NOW)["findings"])
    erratic = [make_run(i, seconds=60) for i in range(1, 8)] + [make_run(8, seconds=900), make_run(9, seconds=900)]
    assert any("erratic" in f["title"] for f in analyze(erratic, 30, NOW)["findings"])


def test_analyze_empty_input_is_safe():
    report = analyze([], 30, NOW)
    assert report["summary"]["runs"] == 0 and report["summary"]["wasted_pct"] == 0.0 and report["findings"] == []
