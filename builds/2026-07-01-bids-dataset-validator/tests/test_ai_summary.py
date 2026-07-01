"""Tests for the optional AI summary layer — no real network call is ever
made; the Anthropic client is always injected as a fake."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_summary import generate_ai_summary
from src.bids_rules import Finding


class _FakeMessage:
    def __init__(self, text):
        self.content = [type("Block", (), {"text": text})()]


class _FakeMessages:
    def __init__(self, text):
        self._text = text
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return _FakeMessage(self._text)


class _FakeClient:
    def __init__(self, text="Fix the sidecars first."):
        self.messages = _FakeMessages(text)


def test_returns_none_when_no_findings():
    assert generate_ai_summary([], client=_FakeClient()) is None


def test_returns_none_when_no_client_and_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    findings = [Finding("error", "MISSING_SUB_ENTITY", "no sub", "a.nii.gz")]
    assert generate_ai_summary(findings, client=None) is None


def test_returns_text_from_injected_client():
    findings = [Finding("error", "MISSING_SUB_ENTITY", "no sub", "a.nii.gz")]
    client = _FakeClient(text="Add sub- entities to the flagged files.")
    result = generate_ai_summary(findings, client=client)
    assert result == "Add sub- entities to the flagged files."


def test_prompt_includes_finding_counts_not_raw_paths_only():
    findings = [
        Finding("warning", "MISSING_SIDECAR", "no sidecar", "sub-01_T1w.nii.gz"),
        Finding("warning", "MISSING_SIDECAR", "no sidecar", "sub-02_T1w.nii.gz"),
    ]
    client = _FakeClient()
    generate_ai_summary(findings, client=client)
    prompt = client.messages.last_kwargs["messages"][0]["content"]
    assert "MISSING_SIDECAR: 2 occurrence(s)" in prompt
