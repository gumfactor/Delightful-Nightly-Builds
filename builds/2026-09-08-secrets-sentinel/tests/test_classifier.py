import subprocess
from pathlib import Path
from unittest.mock import MagicMock

from src.classifier import (
    Finding,
    assign_tier,
    build_findings,
    classify_with_ai,
    redact,
)
from src.scanner import RawHit


def _run(repo_path: Path, args: list[str]) -> None:
    subprocess.run(["git", "-C", str(repo_path), *args], check=True, capture_output=True, text=True)


def _init_repo(repo_path: Path) -> None:
    repo_path.mkdir(parents=True, exist_ok=True)
    _run(repo_path, ["init", "-q"])
    _run(repo_path, ["config", "user.email", "test@example.com"])
    _run(repo_path, ["config", "user.name", "Test User"])


def _commit_file(repo_path: Path, filename: str, content: str, message: str) -> None:
    (repo_path / filename).write_text(content, encoding="utf-8")
    _run(repo_path, ["add", filename])
    _run(repo_path, ["commit", "-q", "-m", message])


def _make_hit(**overrides) -> RawHit:
    defaults = dict(
        repo="myrepo",
        commit="abc123",
        file="config.py",
        line=1,
        pattern_name="AWS Access Key ID",
        matched_text="AKIAIOSFODNN7EXAMPLE",
        is_vendor_pattern=True,
        line_content='AWS_KEY = "AKIAIOSFODNN7EXAMPLE"',
    )
    defaults.update(overrides)
    return RawHit(**defaults)


def test_assign_tier_high_for_vendor_pattern_hit():
    hit = _make_hit(is_vendor_pattern=True)
    assert assign_tier(hit) == "high"


def test_assign_tier_medium_for_suspicious_variable_name_without_vendor_match():
    hit = _make_hit(
        is_vendor_pattern=False,
        pattern_name="High-Entropy Token",
        line_content='api_key = "k3Jd82jfQ0zLmXpR7vNwT9bYh8sQ2fLk"',
    )
    assert assign_tier(hit) == "medium"


def test_assign_tier_low_for_generic_entropy_without_suspicious_name():
    hit = _make_hit(
        is_vendor_pattern=False,
        pattern_name="High-Entropy Token",
        line_content='payload = "k3Jd82jfQ0zLmXpR7vNwT9bYh8sQ2fLk"',
    )
    assert assign_tier(hit) == "low"


def test_redact_replaces_matched_text_with_length_placeholder():
    result = redact('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"', "AKIAIOSFODNN7EXAMPLE")
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    assert "[REDACTED:20chars]" in result


def test_redact_leaves_line_unchanged_when_matched_text_empty():
    line = "some line with no secret"
    assert redact(line, "") == line


def test_build_findings_dedupes_by_file_and_matched_text(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "config.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "add")
    hit_newer = _make_hit(commit="newer_sha")
    hit_older = _make_hit(commit="older_sha")
    findings = build_findings([hit_newer, hit_older], tmp_path)
    assert len(findings) == 1
    # Last one in the input list wins — scan_repo feeds hits newest-first,
    # so this keeps the chronologically oldest (first-introduced) commit.
    assert findings[0].commit == "older_sha"


def test_build_findings_sets_still_in_head_true_when_secret_present(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "config.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "add")
    findings = build_findings([_make_hit()], tmp_path)
    assert findings[0].still_in_head is True


def test_build_findings_never_stores_raw_matched_text_on_finding(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "config.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "add")
    findings = build_findings([_make_hit()], tmp_path)
    finding = findings[0]
    assert not hasattr(finding, "matched_text")
    assert "AKIAIOSFODNN7EXAMPLE" not in finding.redacted_snippet


def _make_finding(**overrides) -> Finding:
    defaults = dict(
        repo="myrepo",
        commit="abc123",
        file="config.py",
        line=1,
        pattern_name="AWS Access Key ID",
        tier="high",
        redacted_snippet='AWS_KEY = "[REDACTED:20chars]"',
        still_in_head=True,
    )
    defaults.update(overrides)
    return Finding(**defaults)


def test_classify_with_ai_skips_high_tier_findings_entirely():
    client = MagicMock()
    finding = _make_finding(tier="high")
    classify_with_ai([finding], client=client)
    client.messages.create.assert_not_called()
    assert finding.ai_verdict is None


def test_classify_with_ai_tags_unreviewed_when_no_client_available():
    finding = _make_finding(tier="medium")
    classify_with_ai([finding], client=None)
    assert finding.ai_verdict == "unreviewed"


def test_classify_with_ai_parses_verdict_from_mocked_response():
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text="likely_test_fixture_or_hash")]
    client.messages.create.return_value = response
    finding = _make_finding(tier="low")
    classify_with_ai([finding], client=client)
    assert finding.ai_verdict == "likely_test_fixture_or_hash"


def test_classify_with_ai_never_sends_real_secret_value_to_client():
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text="uncertain")]
    client.messages.create.return_value = response

    real_secret = "k3Jd82jfQ0zLmXpR7vNwT9bYh8sQ2fLk"
    finding = _make_finding(
        tier="medium",
        redacted_snippet='api_key = "[REDACTED:32chars]"',
    )
    classify_with_ai([finding], client=client)

    call_args_repr = repr(client.messages.create.call_args)
    assert real_secret not in call_args_repr
