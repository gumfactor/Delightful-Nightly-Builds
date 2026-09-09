from datetime import date

from src.rrsp import (
    Contribution,
    IncomeRecord,
    OpeningBalance,
    compute_rrsp,
    rrif_conversion_year,
)


def test_room_capped_at_dollar_limit_when_income_is_high():
    # 18% of $500,000 ($90,000) far exceeds the 2021 dollar limit ($27,830).
    result = compute_rrsp(
        birth_year=1980,
        contributions=[],
        income_history=[IncomeRecord(2020, 500_000)],
        as_of=date(2021, 12, 31),
    )
    year_2021 = next(s for s in result.year_snapshots if s.year == 2021)
    assert year_2021.room_generated == 27_830


def test_room_is_18_percent_when_below_dollar_limit():
    result = compute_rrsp(
        birth_year=1980,
        contributions=[],
        income_history=[IncomeRecord(2020, 80_000)],
        as_of=date(2021, 12, 31),
    )
    year_2021 = next(s for s in result.year_snapshots if s.year == 2021)
    assert year_2021.room_generated == 80_000 * 0.18


def test_pension_adjustment_reduces_room():
    result = compute_rrsp(
        birth_year=1980,
        contributions=[],
        income_history=[IncomeRecord(2020, 80_000, pension_adjustment=3_000)],
        as_of=date(2021, 12, 31),
    )
    year_2021 = next(s for s in result.year_snapshots if s.year == 2021)
    assert year_2021.room_generated == 80_000 * 0.18 - 3_000


def test_pension_adjustment_never_pushes_room_below_zero():
    result = compute_rrsp(
        birth_year=1980,
        contributions=[],
        income_history=[IncomeRecord(2020, 10_000, pension_adjustment=50_000)],
        as_of=date(2021, 12, 31),
    )
    year_2021 = next(s for s in result.year_snapshots if s.year == 2021)
    assert year_2021.room_generated == 0.0


def test_unused_room_carries_forward_indefinitely():
    result = compute_rrsp(
        birth_year=1980,
        contributions=[],
        income_history=[IncomeRecord(2020, 80_000), IncomeRecord(2021, 80_000)],
        as_of=date(2022, 12, 31),
    )
    year_2021 = next(s for s in result.year_snapshots if s.year == 2021)
    year_2022 = next(s for s in result.year_snapshots if s.year == 2022)
    # No contributions at all, so balance strictly accumulates.
    assert year_2022.ending_balance == year_2021.ending_balance + year_2022.room_generated


def test_contributions_reduce_balance_in_their_stated_tax_year():
    result = compute_rrsp(
        birth_year=1980,
        contributions=[Contribution(date(2021, 2, 1), 10_000, tax_year=2020)],
        income_history=[IncomeRecord(2019, 80_000)],
        as_of=date(2021, 12, 31),
    )
    year_2020 = next(s for s in result.year_snapshots if s.year == 2020)
    assert year_2020.contributions == 10_000
    assert year_2020.ending_balance == 80_000 * 0.18 - 10_000


def test_grace_buffer_absorbs_small_overcontribution():
    result = compute_rrsp(
        birth_year=1980,
        contributions=[Contribution(date(2021, 6, 1), 1_500, tax_year=2021)],
        income_history=[],  # no room generated at all
        as_of=date(2021, 12, 31),
    )
    assert not result.is_overcontributed
    assert result.overcontribution_amount == 0.0


def test_overcontribution_beyond_grace_buffer_triggers_penalty():
    result = compute_rrsp(
        birth_year=1980,
        contributions=[Contribution(date(2021, 6, 1), 5_000, tax_year=2021)],
        income_history=[],
        as_of=date(2021, 12, 31),
    )
    # Balance is -5,000; $2,000 is grace, so $3,000 is a real overcontribution.
    assert result.is_overcontributed
    assert result.overcontribution_amount == 3_000
    assert result.estimated_monthly_penalty == 30.0


def test_opening_balance_seeds_starting_room():
    result = compute_rrsp(
        birth_year=1980,
        contributions=[],
        income_history=[],
        as_of=date(2022, 12, 31),
        opening_balance=OpeningBalance(year=2022, amount=50_000),
    )
    year_2022 = next(s for s in result.year_snapshots if s.year == 2022)
    assert year_2022.ending_balance == 50_000


def test_no_new_room_after_rrif_conversion_year():
    birth_year = 1950  # turns 71 in 2021
    result = compute_rrsp(
        birth_year=birth_year,
        contributions=[],
        income_history=[IncomeRecord(2021, 80_000)],  # would generate 2022 room
        as_of=date(2022, 12, 31),
    )
    assert result.rrif_deadline_year == 2021
    year_2022 = next(s for s in result.year_snapshots if s.year == 2022)
    assert year_2022.room_generated == 0.0
    assert result.past_rrif_deadline


def test_rrif_conversion_year_is_71st_birthday_year():
    assert rrif_conversion_year(1955) == 2026


def test_full_worked_example_matches_sample_data():
    # Same scenario shipped in data/sample_headroom.json, hand-verified in
    # BUILD_LOG.md.
    contributions = [
        Contribution(date(2021, 2, 15), 10_000, tax_year=2020),
        Contribution(date(2023, 4, 1), 15_000, tax_year=2023),
    ]
    income = [
        IncomeRecord(2019, 80_000),
        IncomeRecord(2020, 82_000),
        IncomeRecord(2021, 85_000),
        IncomeRecord(2022, 90_000),
        IncomeRecord(2023, 95_000),
        IncomeRecord(2024, 100_000),
        IncomeRecord(2025, 105_000),
    ]
    result = compute_rrsp(1990, contributions, income, date(2026, 9, 9))
    assert result.available_room == 89_660
    assert not result.is_overcontributed
