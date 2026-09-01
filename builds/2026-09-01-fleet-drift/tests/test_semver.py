from src.semver import classify, compare, max_severity, parse_version


def test_parse_full_version():
    assert parse_version("1.2.3") == (1, 2, 3, "")


def test_parse_missing_patch_defaults_zero():
    assert parse_version("1.2") == (1, 2, 0, "")


def test_parse_major_only():
    assert parse_version("2") == (2, 0, 0, "")


def test_parse_prerelease_suffix_captured_separately():
    version = parse_version("1.2.3rc1")
    assert (version.major, version.minor, version.patch) == (1, 2, 3)
    assert version.rest == "rc1"


def test_parse_invalid_returns_none():
    assert parse_version("not-a-version") is None
    assert parse_version("") is None


def test_compare_orders_correctly():
    assert compare("1.0.0", "2.0.0") == -1
    assert compare("2.0.0", "1.0.0") == 1
    assert compare("1.2.3", "1.2.3") == 0


def test_compare_ignores_prerelease_tag_for_ordering():
    assert compare("1.2.3rc1", "1.2.3") == 0


def test_compare_returns_none_on_unparseable_input():
    assert compare("garbage", "1.0.0") is None
    assert compare("1.0.0", "garbage") is None


def test_classify_identical_is_none():
    assert classify("1.2.3", "1.2.3") == "none"


def test_classify_patch_difference():
    assert classify("1.2.3", "1.2.9") == "patch"


def test_classify_minor_difference():
    assert classify("1.2.3", "1.5.0") == "minor"


def test_classify_major_difference():
    assert classify("1.2.3", "2.0.0") == "major"


def test_classify_major_wins_even_with_minor_patch_diff_too():
    assert classify("1.9.9", "2.0.1") == "major"


def test_classify_unparseable_input():
    assert classify("garbage", "1.0.0") == "unknown"


def test_max_severity_picks_worst():
    assert max_severity(["patch", "major", "minor"]) == "major"
    assert max_severity(["none", "patch"]) == "patch"
    assert max_severity([]) == "none"
