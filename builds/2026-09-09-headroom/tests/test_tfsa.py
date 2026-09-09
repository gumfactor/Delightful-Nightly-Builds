from datetime import date

from src.tfsa import Transaction, compute_tfsa, tfsa_start_year


def test_start_year_defaults_to_2009_for_someone_already_18():
    assert tfsa_start_year(birth_year=1980) == 2009


def test_start_year_is_18th_birthday_year_when_after_2009():
    # Born 2000 -> turns 18 in 2018, after the 2009 program start.
    assert tfsa_start_year(birth_year=2000) == 2018


def test_start_year_respects_later_residency_date():
    assert tfsa_start_year(birth_year=1980, resident_since_year=2016) == 2016


def test_no_activity_matches_cumulative_published_total():
    result = compute_tfsa(
        birth_year=1980,
        contributions=[],
        withdrawals=[],
        as_of=date(2026, 6, 1),
    )
    assert result.available_room == 109_000
    assert not result.is_overcontributed


def test_before_eligible_returns_zero_room():
    result = compute_tfsa(
        birth_year=2015,  # turns 18 in 2033, not yet tabulated/reached
        contributions=[],
        withdrawals=[],
        as_of=date(2026, 6, 1),
    )
    assert result.available_room == 0.0
    assert result.year_snapshots == []


def test_contributions_reduce_available_room():
    result = compute_tfsa(
        birth_year=1980,
        contributions=[Transaction(date(2020, 6, 1), 6_000)],
        withdrawals=[],
        as_of=date(2020, 12, 31),
    )
    # Cumulative room through 2020 with no contributions would be 69,500
    # (63,500 through 2019 plus the 2020 annual limit of 6,000).
    assert result.available_room == 69_500 - 6_000


def test_withdrawal_is_not_readded_same_year():
    result = compute_tfsa(
        birth_year=1980,
        contributions=[],
        withdrawals=[Transaction(date(2023, 11, 1), 3_000)],
        as_of=date(2023, 12, 31),
    )
    without_withdrawal = compute_tfsa(
        birth_year=1980, contributions=[], withdrawals=[], as_of=date(2023, 12, 31)
    )
    # A withdrawal doesn't change room in the year it happens.
    assert result.available_room == without_withdrawal.available_room


def test_withdrawal_is_readded_the_following_january():
    as_of_before = date(2023, 12, 31)
    as_of_after = date(2024, 1, 1)
    withdrawals = [Transaction(date(2023, 11, 1), 3_000)]

    before = compute_tfsa(1980, [], withdrawals, as_of_before)
    after = compute_tfsa(1980, [], withdrawals, as_of_after)

    # Room jumps by the 2024 annual limit (7,000) plus the readded 3,000.
    assert after.available_room - before.available_room == 7_000 + 3_000


def test_overcontribution_detected_with_penalty_estimate():
    result = compute_tfsa(
        birth_year=1980,
        contributions=[Transaction(date(2009, 6, 1), 5_500)],  # only 5,000 was available in 2009
        withdrawals=[],
        as_of=date(2009, 12, 31),
    )
    assert result.is_overcontributed
    assert result.overcontribution_amount == 500
    assert result.estimated_monthly_penalty == 5.0  # 1% of 500
    assert result.available_room == 0.0


def test_future_dated_transactions_are_ignored():
    result = compute_tfsa(
        birth_year=1980,
        contributions=[Transaction(date(2030, 1, 1), 5_000)],
        withdrawals=[],
        as_of=date(2026, 6, 1),
    )
    assert result.available_room == 109_000


def test_full_worked_example_matches_sample_data():
    # Same scenario shipped in data/sample_headroom.json, hand-verified in
    # BUILD_LOG.md: born 1990 (start year 2009), $6,000 contributed in 2020
    # and $6,000 in 2022, a $3,000 withdrawal in Nov 2023 re-added Jan 2024.
    contributions = [Transaction(date(2020, 6, 1), 6_000), Transaction(date(2022, 1, 15), 6_000)]
    withdrawals = [Transaction(date(2023, 11, 1), 3_000)]
    result = compute_tfsa(1990, contributions, withdrawals, date(2026, 9, 9))
    assert result.available_room == 100_000
    assert not result.is_overcontributed
