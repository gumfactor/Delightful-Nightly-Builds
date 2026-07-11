from parsing import Trial
from qc import (
    QCConfig,
    flag_trials,
    learning_curve,
    recommend_exclusions,
    summarize_conditions,
    summarize_subjects,
)


def make_trial(subject, condition="A", rt=400.0, correct=True, block=1, trial_num=1):
    return Trial(subject=subject, condition=condition, rt_ms=rt, correct=correct, block=block, trial_num=trial_num)


def test_fast_guess_flag_triggers_below_floor():
    trials = [make_trial("S1", rt=140.0, trial_num=1)]
    flags = flag_trials(trials, QCConfig(rt_floor_ms=150.0))
    assert flags[0].flag == "fast_guess"


def test_fast_guess_flag_does_not_trigger_at_floor_boundary():
    trials = [make_trial("S1", rt=150.0, trial_num=1)]
    flags = flag_trials(trials, QCConfig(rt_floor_ms=150.0))
    assert "fast_guess" not in flags[0].flag


def test_absolute_ceiling_outlier_flag_triggers_regardless_of_subject_distribution():
    # 9 tightly-clustered baseline trials plus one far above the absolute ceiling.
    baseline = [395, 397, 398, 399, 400, 401, 402, 403, 405]
    trials = [make_trial("S1", rt=r, trial_num=i) for i, r in enumerate(baseline, start=1)]
    trials.append(make_trial("S1", rt=5200.0, trial_num=10))
    flags = flag_trials(trials, QCConfig(rt_ceiling_ms=5000.0, sd_outlier=3.5))
    assert "outlier" in flags[-1].flag
    # baseline trials should not be flagged as outliers
    assert all("outlier" not in f.flag for f in flags[:-1])


def test_robust_outlier_flag_triggers_even_though_meansd_zscore_would_be_masked():
    # This reproduces the exact scenario that motivated switching from mean/SD to
    # median/MAD: with n=10 and one extreme outlier, a mean/SD z-score can never
    # exceed sqrt(n-1) == 3.0 no matter how large the outlier is, so a naive
    # "3 SD from the mean" rule could never flag it. Median/MAD does not have
    # this ceiling.
    baseline = [395, 397, 398, 399, 400, 401, 402, 403, 405]
    trials = [make_trial("S1", rt=r, trial_num=i) for i, r in enumerate(baseline, start=1)]
    trials.append(make_trial("S1", rt=900.0, trial_num=10))  # below the 5000ms absolute ceiling
    flags = flag_trials(trials, QCConfig(rt_ceiling_ms=5000.0, sd_outlier=3.5))
    assert "outlier" in flags[-1].flag


def test_no_outlier_flag_for_tightly_clustered_normal_trials():
    baseline = [395, 397, 398, 399, 400, 401, 402, 403, 405, 400]
    trials = [make_trial("S1", rt=r, trial_num=i) for i, r in enumerate(baseline, start=1)]
    flags = flag_trials(trials, QCConfig(rt_ceiling_ms=5000.0, sd_outlier=3.5))
    assert all(f.flag == "" for f in flags)


def test_outlier_detection_does_not_crash_with_single_correct_trial():
    trials = [make_trial("S1", rt=400.0, trial_num=1)]
    flags = flag_trials(trials, QCConfig())
    assert flags[0].flag == ""


def test_chance_level_flag_triggers_for_chance_performance():
    trials = [make_trial("S1", rt=400.0, correct=(i % 2 == 0), trial_num=i) for i in range(10)]
    subjects = summarize_subjects(trials, flag_trials(trials, QCConfig()), QCConfig(chance_rate=0.5))
    assert any("chance_level" in f for f in subjects[0].flags)


def test_chance_level_flag_absent_for_high_performance():
    trials = [make_trial("S1", rt=400.0, correct=(i < 9), trial_num=i) for i in range(10)]
    subjects = summarize_subjects(trials, flag_trials(trials, QCConfig()), QCConfig(chance_rate=0.5))
    assert not any("chance_level" in f for f in subjects[0].flags)


def test_incomplete_flag_triggers_below_min_completion():
    trials = [make_trial("S1", rt=400.0, trial_num=i) for i in range(3)]
    config = QCConfig(expected_trials=10, min_completion=0.8)
    subjects = summarize_subjects(trials, flag_trials(trials, config), config)
    assert any("incomplete" in f for f in subjects[0].flags)


def test_incomplete_flag_absent_when_expected_trials_not_set():
    trials = [make_trial("S1", rt=400.0, trial_num=i) for i in range(3)]
    config = QCConfig(expected_trials=None)
    subjects = summarize_subjects(trials, flag_trials(trials, config), config)
    assert not any("incomplete" in f for f in subjects[0].flags)


def test_ceiling_implausible_flag_triggers_on_perfect_and_fast():
    trials = [make_trial("S1", rt=180.0, correct=True, trial_num=i) for i in range(10)]
    config = QCConfig(rt_floor_ms=150.0, ceiling_fast_multiplier=1.5)  # floor*1.5 = 225
    subjects = summarize_subjects(trials, flag_trials(trials, config), config)
    assert any("ceiling_implausible" in f for f in subjects[0].flags)


def test_ceiling_implausible_flag_absent_for_perfect_but_normal_speed():
    trials = [make_trial("S1", rt=500.0, correct=True, trial_num=i) for i in range(10)]
    config = QCConfig(rt_floor_ms=150.0, ceiling_fast_multiplier=1.5)
    subjects = summarize_subjects(trials, flag_trials(trials, config), config)
    assert not any("ceiling_implausible" in f for f in subjects[0].flags)


def test_high_fast_guess_rate_flag_triggers_at_threshold():
    # 3 of 10 trials (30%) below the RT floor.
    trials = [make_trial("S1", rt=(100.0 if i < 3 else 400.0), correct=True, trial_num=i) for i in range(10)]
    config = QCConfig(rt_floor_ms=150.0)
    subjects = summarize_subjects(trials, flag_trials(trials, config), config)
    assert any("high_fast_guess_rate" in f for f in subjects[0].flags)


def test_recommend_exclusions_respects_flag_count_threshold():
    trials = []
    # S1: chance-level AND incomplete -> 2 flags, should be excluded at threshold=2
    trials += [make_trial("S1", rt=400.0, correct=(i % 2 == 0), trial_num=i) for i in range(4)]
    # S2: clean, high performance, full completion -> 0 flags, should not be excluded
    trials += [make_trial("S2", rt=400.0, correct=True, trial_num=i) for i in range(10)]
    config = QCConfig(expected_trials=10, min_completion=0.8, exclude_threshold=2)
    subjects = summarize_subjects(trials, flag_trials(trials, config), config)
    excluded = recommend_exclusions(subjects, config)
    excluded_ids = {s.subject for s in excluded}
    assert "S1" in excluded_ids
    assert "S2" not in excluded_ids


def test_summarize_conditions_aggregates_across_subjects():
    trials = [
        make_trial("S1", condition="A", rt=400.0, correct=True, trial_num=1),
        make_trial("S1", condition="A", rt=600.0, correct=False, trial_num=2),
        make_trial("S2", condition="A", rt=500.0, correct=True, trial_num=1),
    ]
    conditions = summarize_conditions(trials)
    assert len(conditions) == 1
    cond = conditions[0]
    assert cond.condition == "A"
    assert cond.n_subjects == 2
    assert cond.n_trials == 3
    assert round(cond.accuracy, 4) == round(2 / 3, 4)
    assert round(cond.mean_rt, 2) == 450.0  # mean of the two *correct* trials: 400, 500


def test_learning_curve_bins_trials_by_position():
    trials = [make_trial("S1", condition="A", rt=400.0, correct=True, block=1, trial_num=i) for i in range(10)]
    curves = learning_curve(trials, n_bins=5)
    assert "A" in curves
    assert len(curves["A"]) == 5
    assert sum(p["n"] for p in curves["A"]) == 10


def test_learning_curve_handles_empty_condition_gracefully():
    curves = learning_curve([], n_bins=5)
    assert curves == {}


def test_subject_summary_handles_all_malformed_trials_without_crashing():
    trials = [Trial(subject="S1", condition="A", rt_ms=None, correct=None, block=1, trial_num=i) for i in range(3)]
    config = QCConfig()
    subjects = summarize_subjects(trials, flag_trials(trials, config), config)
    assert subjects[0].n_trials == 3
    assert subjects[0].accuracy == 0.0
    assert subjects[0].mean_rt is None
