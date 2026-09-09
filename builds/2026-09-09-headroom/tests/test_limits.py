import pytest

from src.limits import (
    LimitTableError,
    RRSP_ANNUAL_LIMITS,
    TFSA_ANNUAL_LIMITS,
    rrsp_limit,
    tfsa_limit,
)


def test_tfsa_limit_known_year():
    assert tfsa_limit(2015) == 10_000
    assert tfsa_limit(2024) == 7_000


def test_rrsp_limit_known_year():
    assert rrsp_limit(2023) == 30_780
    assert rrsp_limit(2026) == 33_810


def test_tfsa_limit_out_of_range_raises():
    with pytest.raises(LimitTableError):
        tfsa_limit(2008)
    with pytest.raises(LimitTableError):
        tfsa_limit(2030)


def test_rrsp_limit_out_of_range_raises():
    with pytest.raises(LimitTableError):
        rrsp_limit(2008)


def test_tfsa_cumulative_total_matches_published_figure():
    # Widely-cited public figure: $102,000 cumulative TFSA room by 2025,
    # $109,000 by 2026, for someone eligible since program inception in 2009.
    total_2025 = sum(v for y, v in TFSA_ANNUAL_LIMITS.items() if y <= 2025)
    total_2026 = sum(v for y, v in TFSA_ANNUAL_LIMITS.items() if y <= 2026)
    assert total_2025 == 102_000
    assert total_2026 == 109_000


def test_rrsp_limits_strictly_increase_or_hold_year_over_year():
    years = sorted(RRSP_ANNUAL_LIMITS)
    for a, b in zip(years, years[1:]):
        assert RRSP_ANNUAL_LIMITS[b] >= RRSP_ANNUAL_LIMITS[a]
