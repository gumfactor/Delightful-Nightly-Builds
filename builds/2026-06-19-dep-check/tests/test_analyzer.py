"""Tests for src/analyzer.py — all pure logic, no network calls."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from src.analyzer import compare_versions, classify_staleness, compute_summary, build_result
from src.models import Requirement, PackageResult


def _req(name="requests", pinned="2.28.0"):
    return Requirement(name=name, pinned_version=pinned, specifier=f"=={pinned}", source_file="requirements.txt")


def _result(status="up-to-date", yanked=False, pinned="2.28.0"):
    return PackageResult(
        req=_req(pinned=pinned),
        latest_version="2.28.0",
        pinned_upload_date=None,
        days_since_pinned=None,
        status=status,
        yanked=yanked,
    )


# ---------------------------------------------------------------------------
# compare_versions
# ---------------------------------------------------------------------------

class TestCompareVersions:
    def test_same_version_is_up_to_date(self):
        assert compare_versions("2.28.0", "2.28.0") == "up-to-date"

    def test_pinned_ahead_of_latest_is_up_to_date(self):
        # Shouldn't happen in practice but should not crash
        assert compare_versions("3.0.0", "2.28.0") == "up-to-date"

    def test_patch_update_detected(self):
        assert compare_versions("2.28.0", "2.28.1") == "patch"

    def test_minor_update_detected(self):
        assert compare_versions("2.28.0", "2.29.0") == "minor"

    def test_major_update_detected(self):
        assert compare_versions("2.28.0", "3.0.0") == "major"

    def test_no_pinned_version_is_unpinned(self):
        assert compare_versions(None, "2.28.0") == "unpinned"

    def test_no_latest_version_is_unknown(self):
        assert compare_versions("2.28.0", None) == "unknown"

    def test_both_none_is_unpinned(self):
        # pinned=None takes priority
        assert compare_versions(None, None) == "unpinned"

    def test_single_component_versions(self):
        assert compare_versions("1", "2") == "major"

    def test_pre_release_suffix_stripped_for_comparison(self):
        # "2.28.0a1" → (2,28,0) which equals (2,28,0) → up-to-date
        assert compare_versions("2.28.0a1", "2.28.0") == "up-to-date"

    def test_multi_component_minor_update(self):
        assert compare_versions("1.2.3", "1.3.0") == "minor"


# ---------------------------------------------------------------------------
# classify_staleness
# ---------------------------------------------------------------------------

class TestClassifyStaleness:
    def test_zero_days_is_fresh(self):
        assert classify_staleness(0) == "fresh"

    def test_thirty_days_is_fresh(self):
        assert classify_staleness(30) == "fresh"

    def test_thirty_one_days_is_aging(self):
        assert classify_staleness(31) == "aging"

    def test_one_eighty_days_is_aging(self):
        assert classify_staleness(180) == "aging"

    def test_one_eighty_one_days_is_old(self):
        assert classify_staleness(181) == "old"

    def test_three_sixty_five_days_is_old(self):
        assert classify_staleness(365) == "old"

    def test_three_sixty_six_days_is_very_old(self):
        assert classify_staleness(366) == "very-old"

    def test_none_days_is_unknown(self):
        assert classify_staleness(None) == "unknown"


# ---------------------------------------------------------------------------
# compute_summary
# ---------------------------------------------------------------------------

class TestComputeSummary:
    def test_all_up_to_date(self):
        results = [_result("up-to-date"), _result("up-to-date")]
        s = compute_summary(results)
        assert s.total == 2
        assert s.up_to_date == 2
        assert s.needs_update == 0
        assert s.yanked == 0

    def test_mixed_statuses_counted_correctly(self):
        results = [
            _result("up-to-date"),
            _result("patch"),
            _result("minor"),
            _result("major"),
            _result("unpinned"),
            _result("unknown"),
        ]
        s = compute_summary(results)
        assert s.total == 6
        assert s.up_to_date == 1
        assert s.patch == 1
        assert s.minor == 1
        assert s.major == 1
        assert s.unpinned == 1
        assert s.unknown == 1
        assert s.needs_update == 3

    def test_yanked_counted_separately(self):
        results = [
            _result("up-to-date", yanked=True),
            _result("patch", yanked=False),
        ]
        s = compute_summary(results)
        assert s.yanked == 1

    def test_empty_results_returns_zero_summary(self):
        s = compute_summary([])
        assert s.total == 0
        assert s.needs_update == 0

    def test_all_unknown(self):
        results = [_result("unknown"), _result("unknown"), _result("unknown")]
        s = compute_summary(results)
        assert s.unknown == 3
        assert s.needs_update == 0
