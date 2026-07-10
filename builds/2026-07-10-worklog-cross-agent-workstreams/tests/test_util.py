from datetime import timedelta

from worklog import util


def test_event_id_is_deterministic():
    a = util.event_id("proj", "git", "abc123", "commit")
    b = util.event_id("proj", "git", "abc123", "commit")
    assert a == b


def test_event_id_differs_by_input():
    a = util.event_id("proj", "git", "abc123", "commit")
    b = util.event_id("proj", "git", "def456", "commit")
    assert a != b


def test_slugify_basic():
    assert util.slugify("Add CSV Validation!") == "add-csv-validation"


def test_slugify_empty_falls_back():
    assert util.slugify("   ") == "item"


def test_redact_secrets_openai_style_key():
    text = "here is my key sk-abcdefghijklmnopqrstuvwx use it"
    redacted = util.redact_secrets(text)
    assert "sk-abcdefghijklmnopqrstuvwx" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_secrets_github_token():
    text = "token ghp_1234567890abcdefghijklmnop end"
    redacted = util.redact_secrets(text)
    assert "ghp_1234567890abcdefghijklmnop" not in redacted


def test_redact_secrets_leaves_normal_text_alone():
    text = "Reject automatic type coercion because it corrupts identifiers"
    assert util.redact_secrets(text) == text


def test_jaccard_identical_sets():
    assert util.jaccard({"a", "b"}, {"a", "b"}) == 1.0


def test_jaccard_disjoint_sets():
    assert util.jaccard({"a"}, {"b"}) == 0.0


def test_jaccard_partial_overlap():
    score = util.jaccard({"a", "b", "c"}, {"b", "c", "d"})
    assert score == 2 / 4


def test_extract_issue_refs_multiple():
    assert util.extract_issue_refs("Fixes #12 and relates to #45") == [12, 45]


def test_extract_issue_refs_none():
    assert util.extract_issue_refs("no references here") == []


def test_extract_issue_refs_dedupes():
    assert util.extract_issue_refs("#7 again #7") == [7]


def test_parse_since_duration_days():
    cutoff = util.parse_since("2d")
    expected = util.utc_now() - timedelta(days=2)
    assert abs((cutoff - expected).total_seconds()) < 5


def test_parse_since_yesterday():
    cutoff = util.parse_since("yesterday")
    expected = util.utc_now() - timedelta(days=1)
    assert abs((cutoff - expected).total_seconds()) < 5


def test_parse_iso_roundtrip():
    iso = util.utc_now_iso()
    parsed = util.parse_iso(iso)
    assert parsed.tzinfo is not None
