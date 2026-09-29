from worklog.ledger import make_event
from worklog.project import normalize_remote
from worklog.redact import PLACEHOLDER, redact, redact_text


def test_github_and_anthropic_tokens_are_redacted():
    text = "used ghp_" + "A" * 36 + " and sk-ant-" + "b" * 30
    cleaned = redact_text(text)
    assert "ghp_" not in cleaned and "sk-ant-" not in cleaned
    assert cleaned.count(PLACEHOLDER) == 2


def test_key_value_secrets_and_bearer_headers_are_redacted():
    assert "hunter2xx" not in redact_text("password=hunter2xx in config")
    assert "abcdef123456789" not in redact_text("Authorization: Bearer abcdef123456789")


def test_private_key_block_is_redacted():
    block = "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJB\n-----END RSA PRIVATE KEY-----"
    assert "MIIBOg" not in redact_text("key: " + block)


def test_url_credentials_are_stripped_but_host_kept():
    assert redact_text("clone https://user:pw@github.com/a/b") == "clone https://github.com/a/b"


def test_ordinary_text_is_untouched():
    text = "Reject automatic type coercion; token bucket refill fixed (#12)"
    assert redact_text(text) == text


def test_redaction_recurses_through_nested_structures():
    data = {"a": ["ok", "token=supersecretvalue"], "b": {"c": "AKIA" + "X" * 16}, "n": 3}
    cleaned = redact(data)
    assert "supersecretvalue" not in str(cleaned) and "AKIAXXXX" not in str(cleaned)
    assert cleaned["n"] == 3


def test_make_event_redacts_summary_and_metadata_before_persistence():
    event = make_event(ts="2026-09-01T00:00:00Z", project_id="p", etype="commit", provider="git", ref="abc",
                       summary="fix with ghp_" + "Z" * 30, metadata={"note": "api_key=abcd1234efgh"})
    assert "ghp_" not in event["summary"]
    assert "abcd1234efgh" not in str(event["metadata"])


def test_remote_normalisation_drops_credentials_and_unifies_ssh_https():
    https = normalize_remote("https://ghp_" + "q" * 30 + "@github.com/Acme/Lab.git")
    ssh = normalize_remote("git@github.com:Acme/Lab.git")
    assert https == ssh == "github.com/acme/lab"
