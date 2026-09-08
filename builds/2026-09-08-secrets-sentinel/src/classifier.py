"""Tier assignment, redaction, and optional AI triage.

Security property this module exists to guarantee: the real secret value
(`RawHit.matched_text`) never crosses into a `Finding` — only a redacted
snippet does — so anything downstream (report rendering, the AI triage
prompt) is structurally incapable of leaking the actual credential.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from src.patterns import SUSPICIOUS_VARIABLE_NAMES
from src.scanner import RawHit, file_still_at_head

Tier = Literal["high", "medium", "low"]

AI_VERDICTS = frozenset({"likely_real_secret", "likely_test_fixture_or_hash", "uncertain"})

_TRIAGE_MODEL = "claude-haiku-4-5-20251001"

_TRIAGE_PROMPT_TEMPLATE = """You are triaging a possible leaked credential found in a git repository's history.
The actual secret value has been redacted and replaced with a placeholder — you will never see it.

Detected pattern: {pattern_name}
Redacted code context:
{redacted_snippet}

Classify this as exactly one of: likely_real_secret, likely_test_fixture_or_hash, uncertain.
Reply with only that one label, nothing else."""


@dataclass
class Finding:
    repo: str
    commit: str
    file: str
    line: int
    pattern_name: str
    tier: Tier
    redacted_snippet: str
    still_in_head: bool
    ai_verdict: str | None = None


def redact(line_content: str, matched_text: str) -> str:
    """Replace every occurrence of matched_text in line_content with a length-only placeholder."""
    if not matched_text:
        return line_content
    placeholder = f"[REDACTED:{len(matched_text)}chars]"
    return line_content.replace(matched_text, placeholder)


def assign_tier(hit: RawHit) -> Tier:
    """High for a named vendor pattern; medium if a suspicious variable name sits nearby; low otherwise."""
    if hit.is_vendor_pattern:
        return "high"
    if SUSPICIOUS_VARIABLE_NAMES.search(hit.line_content):
        return "medium"
    return "low"


def build_findings(hits: list[RawHit], repo_path: Path) -> list[Finding]:
    """Convert raw hits into deduplicated, redacted Findings.

    Deduplicates by (file, matched_text): since `RawHit`s come from newest
    commit first, the last one seen while iterating is the chronologically
    oldest — i.e. when the secret was first introduced, which is the most
    actionable commit for remediation.
    """
    deduped: dict[tuple[str, str], RawHit] = {}
    for hit in hits:
        deduped[(hit.file, hit.matched_text)] = hit

    findings: list[Finding] = []
    for hit in deduped.values():
        still_in_head = file_still_at_head(repo_path, hit.file, hit.matched_text)
        findings.append(
            Finding(
                repo=hit.repo,
                commit=hit.commit,
                file=hit.file,
                line=hit.line,
                pattern_name=hit.pattern_name,
                tier=assign_tier(hit),
                redacted_snippet=redact(hit.line_content, hit.matched_text),
                still_in_head=still_in_head,
            )
        )
    return findings


def _build_triage_prompt(finding: Finding) -> str:
    return _TRIAGE_PROMPT_TEMPLATE.format(
        pattern_name=finding.pattern_name,
        redacted_snippet=finding.redacted_snippet,
    )


def _parse_verdict(response_text: str) -> str:
    cleaned = response_text.strip().lower()
    for verdict in AI_VERDICTS:
        if verdict in cleaned:
            return verdict
    return "uncertain"


def classify_with_ai(findings: list[Finding], client: Any | None = None) -> None:
    """Mutate finding.ai_verdict for every medium/low finding.

    High-tier findings are skipped entirely — a named vendor pattern match
    is already unambiguous. With no client (no ANTHROPIC_API_KEY at
    runtime), medium/low findings are tagged 'unreviewed' rather than
    guessed at.
    """
    for finding in findings:
        if finding.tier == "high":
            continue
        if client is None:
            finding.ai_verdict = "unreviewed"
            continue
        prompt = _build_triage_prompt(finding)
        response = client.messages.create(
            model=_TRIAGE_MODEL,
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text
        finding.ai_verdict = _parse_verdict(response_text)
