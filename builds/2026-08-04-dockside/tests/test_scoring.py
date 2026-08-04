from datetime import date

import scoring


def make_obs(day, temp_min=10.0, temp_max=20.0, precip=0.0, wind=10.0, wave=None, water_temp=None):
    return scoring.Observation(
        obs_date=date(2026, 8, day),
        temp_min_c=temp_min,
        temp_max_c=temp_max,
        precip_mm=precip,
        wind_speed_max_kmh=wind,
        wave_height_max_m=wave,
        water_temp_c=water_temp,
    )


def make_task(**overrides):
    defaults = dict(
        id=1, name="Test Task", category="dock",
        window_start_month=1, window_end_month=12,
        max_wind_kmh=None, min_water_temp_c=None,
        dry_days_required=None, frost_free_required=False,
    )
    defaults.update(overrides)
    return scoring.Task(**defaults)


# --- Dry-day streak ---

def test_dry_streak_present():
    task = make_task(dry_days_required=2)
    obs = [make_obs(1, precip=0.0), make_obs(2, precip=0.5), make_obs(3, precip=5.0)]
    result = scoring.evaluate_dry_streak(task, obs)
    assert result[date(2026, 8, 1)] == "fail"   # streak = 1, need 2
    assert result[date(2026, 8, 2)] == "pass"   # streak = 2, satisfies
    assert result[date(2026, 8, 3)] == "fail"   # rain resets streak


def test_dry_streak_too_short_never_passes():
    task = make_task(dry_days_required=5)
    obs = [make_obs(d, precip=0.0) for d in range(1, 4)]  # only 3 dry days available
    result = scoring.evaluate_dry_streak(task, obs)
    assert all(v == "fail" for v in result.values())


def test_dry_streak_unknown_precip_resets_and_reports_unknown():
    task = make_task(dry_days_required=2)
    obs = [make_obs(1, precip=0.0), make_obs(2, precip=None), make_obs(3, precip=0.0), make_obs(4, precip=0.0)]
    result = scoring.evaluate_dry_streak(task, obs)
    assert result[date(2026, 8, 2)] == "unknown"
    assert result[date(2026, 8, 3)] == "fail"   # streak restarted at day 3
    assert result[date(2026, 8, 4)] == "pass"   # 2-day streak: days 3-4


def test_dry_streak_not_required_is_not_applicable():
    task = make_task(dry_days_required=None)
    obs = [make_obs(1, precip=100.0)]
    result = scoring.evaluate_dry_streak(task, obs)
    assert result[date(2026, 8, 1)] == "n/a"


# --- Individual constraint evaluation ---

def test_wind_constraint_pass_and_fail():
    task = make_task(max_wind_kmh=20.0)
    calm = make_obs(1, wind=10.0)
    windy = make_obs(2, wind=30.0)
    evals = scoring.evaluate_days(task, [calm, windy])
    assert evals[0].constraints["wind"] == "pass"
    assert evals[1].constraints["wind"] == "fail"


def test_wind_constraint_unknown_when_no_data():
    task = make_task(max_wind_kmh=20.0)
    obs = make_obs(1, wind=None)
    evals = scoring.evaluate_days(task, [obs])
    assert evals[0].constraints["wind"] == "unknown"


def test_frost_free_constraint():
    task = make_task(frost_free_required=True)
    frosty = make_obs(1, temp_min=-2.0)
    warm = make_obs(2, temp_min=5.0)
    evals = scoring.evaluate_days(task, [frosty, warm])
    assert evals[0].constraints["frost_free"] == "fail"
    assert evals[1].constraints["frost_free"] == "pass"


def test_water_temp_constraint_unknown_when_marine_unavailable():
    task = make_task(min_water_temp_c=15.0)
    obs = make_obs(1, water_temp=None)
    evals = scoring.evaluate_days(task, [obs])
    assert evals[0].constraints["water_temp"] == "unknown"


def test_water_temp_constraint_pass_and_fail():
    task = make_task(min_water_temp_c=15.0)
    cold = make_obs(1, water_temp=10.0)
    warm = make_obs(2, water_temp=18.0)
    evals = scoring.evaluate_days(task, [cold, warm])
    assert evals[0].constraints["water_temp"] == "fail"
    assert evals[1].constraints["water_temp"] == "pass"


def test_day_with_no_constraints_is_always_satisfied():
    task = make_task()  # no constraints at all
    obs = make_obs(1)
    evals = scoring.evaluate_days(task, [obs])
    assert evals[0].all_satisfied is True


def test_unknown_constraint_blocks_all_satisfied():
    task = make_task(min_water_temp_c=15.0, max_wind_kmh=20.0)
    obs = make_obs(1, wind=10.0, water_temp=None)  # wind passes, water temp unknown
    evals = scoring.evaluate_days(task, [obs])
    assert evals[0].all_satisfied is False


# --- classify_task_status across all six states ---

def test_status_off_season():
    task = make_task(window_start_month=10, window_end_month=11)  # October-November, still upcoming
    obs = [make_obs(1)]
    status, best, _ = scoring.classify_task_status(task, obs, date(2026, 8, 15), None)
    assert status == "off_season"
    assert best is None


def test_status_overdue():
    task = make_task(window_start_month=4, window_end_month=5, max_wind_kmh=20.0)
    obs = [make_obs(1, wind=30.0)]  # windy, doesn't satisfy
    status, best, _ = scoring.classify_task_status(task, obs, date(2026, 8, 15), None)
    assert status == "overdue"


def test_status_not_ready():
    task = make_task(window_start_month=8, window_end_month=9, max_wind_kmh=10.0)
    obs = [make_obs(15, wind=30.0)]  # in window but too windy
    status, best, _ = scoring.classify_task_status(task, obs, date(2026, 8, 15), None)
    assert status == "not_ready"
    assert best is None


def test_status_ready_now():
    task = make_task(window_start_month=8, window_end_month=9, max_wind_kmh=20.0)
    obs = [make_obs(15, wind=5.0)]
    status, best, _ = scoring.classify_task_status(task, obs, date(2026, 8, 15), None)
    assert status == "ready_now"
    assert best.obs_date == date(2026, 8, 15)


def test_status_ready_soon():
    task = make_task(window_start_month=8, window_end_month=9, max_wind_kmh=20.0)
    obs = [make_obs(15, wind=40.0), make_obs(17, wind=5.0)]
    status, best, _ = scoring.classify_task_status(task, obs, date(2026, 8, 15), None)
    assert status == "ready_soon"
    assert best.obs_date == date(2026, 8, 17)


def test_status_done_this_season():
    task = make_task(window_start_month=8, window_end_month=9)
    status, best, evals = scoring.classify_task_status(task, [], date(2026, 8, 15), 2026)
    assert status == "done_this_season"
    assert best is None
    assert evals == []


def test_status_wrapping_window_in_window():
    # Winterizing task with a Nov-Feb wrapping window
    task = make_task(window_start_month=11, window_end_month=2, frost_free_required=True)
    obs = [make_obs(1, temp_min=2.0)]
    status, best, _ = scoring.classify_task_status(task, obs, date(2026, 12, 15), None)
    # December falls inside the wrapping window (Nov-Feb) -> should be evaluated, not off_season
    assert status in ("ready_now", "ready_soon", "not_ready")


# --- add_one_year ---

def test_add_one_year_normal():
    assert scoring.add_one_year(date(2026, 8, 15)) == date(2027, 8, 15)


def test_add_one_year_leap_day_rolls_back():
    # 2028 is a leap year; 2029 is not
    assert scoring.add_one_year(date(2028, 2, 29)) == date(2029, 2, 28)


# --- boating_comfort_score ---

def test_boating_comfort_score_bounds():
    obs = make_obs(1, wind=0.0, precip=0.0, temp_max=25.0)
    score = scoring.boating_comfort_score(obs)
    assert 0.0 <= score <= 100.0


def test_boating_comfort_score_higher_for_calmer_day():
    calm = make_obs(1, wind=0.0, precip=0.0, temp_max=25.0)
    windy = make_obs(2, wind=40.0, precip=0.0, temp_max=25.0)
    assert scoring.boating_comfort_score(calm) > scoring.boating_comfort_score(windy)


def test_boating_comfort_score_missing_data_uses_neutral_value():
    obs = make_obs(1, wind=None, precip=None, temp_max=None)
    score = scoring.boating_comfort_score(obs)
    assert score == 50.0


def test_boating_comfort_score_wave_height_not_forced_when_absent():
    without_wave = make_obs(1, wind=10.0, precip=0.0, temp_max=25.0, wave=None)
    with_calm_wave = make_obs(2, wind=10.0, precip=0.0, temp_max=25.0, wave=0.0)
    # Adding a calm (0m) wave reading should not lower the score below the
    # no-wave-data baseline, since 0m contributes a perfect 100.
    assert scoring.boating_comfort_score(with_calm_wave) >= scoring.boating_comfort_score(without_wave)
