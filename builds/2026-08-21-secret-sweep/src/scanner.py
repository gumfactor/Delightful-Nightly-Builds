"""Core detection: turns repo content into Finding dicts.

Severity is resolved purely by presence: a match found in the working tree
(or still present at HEAD when found via history) is 'critical'; a match
that only ever existed in a past commit and is gone from HEAD is 'high'.
"""

from __future__ import annotations

from pathlib import Path

from . import git_ops, patterns, redact


def _matches_for_line(line_text: str) -> list[tuple[str, str]]:
    """Return (pattern_name, raw_value) for every match on one line of text.

    A value already caught by a named credential pattern is not also reported
    by the generic entropy detector — otherwise a single AWS key, say, would
    surface as two separate findings for the same underlying value.
    """
    results: list[tuple[str, str]] = []
    named_values: set[str] = set()
    for pattern, value, _offset in patterns.find_named_matches(line_text):
        results.append((pattern.name, value))
        named_values.add(value)
    for var_name, value, _offset in patterns.find_generic_matches(line_text):
        if value in named_values:
            continue
        results.append((f"Generic High-Entropy Match ({var_name})", value))
    return results


def _build_finding(
    repo_path: str,
    repo_name: str,
    scope: str,
    file_path: str,
    line_number: int,
    commit_sha: str,
    pattern_name: str,
    severity: str,
    raw_value: str,
    line_text: str,
) -> dict:
    idx = line_text.find(raw_value)
    before = line_text[:idx] if idx >= 0 else ""
    after = line_text[idx + len(raw_value):] if idx >= 0 else ""
    return {
        "repo_path": repo_path,
        "repo_name": repo_name,
        "scope": scope,
        "file_path": file_path,
        "line_number": line_number,
        "commit_sha": commit_sha or "",
        "pattern_name": pattern_name,
        "severity": severity,
        "entropy": patterns.shannon_entropy(raw_value),
        "masked_preview": redact.mask_value(raw_value),
        "match_hash": redact.hash_value(raw_value),
        "masked_context": redact.masked_context(before, raw_value, after),
        "ai_verdict": None,
        "ai_rationale": None,
    }


def scan_working_tree(repo_path: str) -> list[dict]:
    name = git_ops.repo_name(repo_path)
    findings: list[dict] = []
    for rel_path in git_ops.list_working_tree_files(repo_path):
        content = git_ops.read_working_tree_file(repo_path, rel_path)
        if content is None:
            continue
        for line_number, line_text in enumerate(content.splitlines(), start=1):
            for pattern_name, raw_value in _matches_for_line(line_text):
                findings.append(
                    _build_finding(
                        repo_path, name, "working-tree", rel_path, line_number,
                        "", pattern_name, "critical", raw_value, line_text,
                    )
                )
    return findings


def scan_history(repo_path: str, max_commits: int | None = None) -> list[dict]:
    name = git_ops.repo_name(repo_path)
    if not git_ops.has_any_commits(repo_path):
        return []
    patch_text = git_ops.get_history_patch(repo_path, max_commits=max_commits)
    findings: list[dict] = []
    head_presence_cache: dict[tuple[str, str], bool] = {}

    for commit_sha, file_path, line_number, line_text in git_ops.iter_added_lines(patch_text):
        for pattern_name, raw_value in _matches_for_line(line_text):
            cache_key = (file_path, raw_value)
            if cache_key not in head_presence_cache:
                head_content = git_ops.read_head_file(repo_path, file_path)
                head_presence_cache[cache_key] = head_content is not None and raw_value in head_content
            severity = "critical" if head_presence_cache[cache_key] else "high"
            findings.append(
                _build_finding(
                    repo_path, name, "history", file_path, line_number,
                    commit_sha, pattern_name, severity, raw_value, line_text,
                )
            )
    return findings


def apply_ai_review(findings: list[dict], api_key: str | None = None) -> None:
    """Mutate each finding in place, setting ai_verdict / ai_rationale."""
    from . import ai_review  # local import keeps ai_review optional/decoupled

    for finding in findings:
        file_ext = Path(finding["file_path"]).suffix
        result = ai_review.review_finding(
            pattern_name=finding["pattern_name"],
            file_ext=file_ext,
            entropy=finding["entropy"],
            masked_snippet=finding["masked_context"],
            api_key=api_key,
        )
        finding["ai_verdict"] = result["verdict"]
        finding["ai_rationale"] = result["rationale"]


def scan_multiple(repo_paths: list[str], include_history: bool = False, max_commits: int | None = None) -> list[dict]:
    all_findings: list[dict] = []
    for repo_path in repo_paths:
        if not git_ops.is_git_repo(repo_path):
            continue
        all_findings.extend(scan_working_tree(repo_path))
        if include_history:
            all_findings.extend(scan_history(repo_path, max_commits=max_commits))
    return all_findings
