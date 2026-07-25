from src.redact import redact_secrets


def test_redacts_api_key_assignment():
    text = 'API_KEY="sk_live_abcdef1234567890"'
    result = redact_secrets(text)
    assert "sk_live_abcdef1234567890" not in result
    assert "[REDACTED]" in result


def test_redacts_password_assignment():
    text = "password = supersecretvalue123"
    result = redact_secrets(text)
    assert "supersecretvalue123" not in result


def test_redacts_aws_style_key():
    # AWS's own publicly-documented example access key ID, used as a canonical test fixture.
    text = "aws_key = AKIAIOSFODNN7EXAMPLE"
    result = redact_secrets(text)
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    assert "[REDACTED_AWS_KEY]" in result


def test_redacts_bearer_token():
    text = "Authorization: Bearer abcDEF123456789012345"
    result = redact_secrets(text)
    assert "abcDEF123456789012345" not in result
    assert "Bearer [REDACTED]" in result


def test_leaves_normal_code_untouched():
    code = "def add(a, b):\n    return a + b\n"
    assert redact_secrets(code) == code


def test_handles_empty_and_none_gracefully():
    assert redact_secrets("") == ""
    assert redact_secrets(None) is None
