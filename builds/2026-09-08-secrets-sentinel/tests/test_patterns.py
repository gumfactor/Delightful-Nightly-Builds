import pytest

from src.patterns import SUSPICIOUS_VARIABLE_NAMES, match_vendor_patterns

CANONICAL_EXAMPLES = [
    ("AWS Access Key ID", "aws_key = 'AKIAIOSFODNN7EXAMPLE'"),
    ("GitHub Personal Access Token", "token = 'ghp_" + "a" * 36 + "'"),
    ("GitHub OAuth Token", "token = 'gho_" + "b" * 36 + "'"),
    ("Slack Token", "SLACK_TOKEN=xoxb-1234567890-abcdefghij"),
    ("Stripe Live Secret Key", "stripe_key = 'sk_live_" + "c" * 24 + "'"),
    ("Google/Firebase API Key", "apiKey: 'AIza" + "D" * 35 + "'"),
    ("Twilio API Key", "TWILIO_KEY=SK" + "0123456789abcdef" * 2),
    ("PEM Private Key Block", "-----BEGIN RSA PRIVATE KEY-----"),
    (
        "JSON Web Token",
        "jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U'",
    ),
]


@pytest.mark.parametrize("pattern_name,line", CANONICAL_EXAMPLES)
def test_each_vendor_pattern_matches_its_canonical_example(pattern_name, line):
    matches = match_vendor_patterns(line)
    assert any(m.name == pattern_name for m in matches), f"{pattern_name} did not match: {line}"


def test_plain_code_line_matches_no_vendor_pattern():
    line = "def calculate_total(items): return sum(item.price for item in items)"
    assert match_vendor_patterns(line) == []


def test_short_random_string_matches_no_vendor_pattern():
    line = "id = 'AKIA123'  # too short to be a real AWS key"
    assert match_vendor_patterns(line) == []


def test_suspicious_variable_names_matches_common_secret_var_names():
    for name in ["api_key", "API_KEY", "secret", "auth_token", "password", "private_key"]:
        assert SUSPICIOUS_VARIABLE_NAMES.search(f"{name} = 'x'"), f"expected match for {name}"


def test_suspicious_variable_names_does_not_match_unrelated_code():
    assert SUSPICIOUS_VARIABLE_NAMES.search("total_price = compute_price(items)") is None
