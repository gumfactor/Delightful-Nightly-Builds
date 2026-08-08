"""Deterministic, regex-based completeness/rigor checklist for grant drafts.

No AI, no ML — a fixed rule engine, the same shape as Protocol Forge's
ethics-compliance engine (2026-07-19). Every check is a simple "does this
section contain language matching pattern X" test. This is intentionally
crude: it cannot judge whether a power analysis is *correct*, only whether
one appears to have been written at all. That is still a genuinely useful,
always-available first pass with zero API key required.
"""

from __future__ import annotations

import re
from typing import Callable

Check = tuple[str, str, Callable[[str], bool]]


def _contains(*patterns: str) -> Callable[[str], bool]:
    compiled = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]

    def _check(text: str) -> bool:
        return any(p.search(text) for p in compiled)

    return _check


CHECKLIST_SPEC: dict[str, list[Check]] = {
    "aims": [
        (
            "numbered_aims",
            "Aims are explicitly numbered (Aim 1 / Aim 2, or a numbered list).",
            _contains(r"\baim\s*[1-3]\b", r"^\s*[1-3][.)]\s", ),
        ),
        (
            "hypothesis_language",
            "A central hypothesis or prediction is explicitly stated.",
            _contains(r"\bhypothes(is|ize|ized)\b", r"\bwe predict\b", r"\bcentral hypothesis\b"),
        ),
        (
            "expected_outcome",
            "Expected outcomes or the impact of completing the aims is stated.",
            _contains(r"\bexpected outcome", r"\bupon completion\b", r"\bthis work will (provide|establish|determine)"),
        ),
    ],
    "significance": [
        (
            "gap_stated",
            "An explicit gap in current knowledge is named.",
            _contains(r"\bgap in\b", r"\bremains unknown\b", r"\bhas not been (established|determined|shown)\b", r"\bcritical barrier\b", r"\bit is unclear\b"),
        ),
        (
            "why_now",
            "The proposal argues why this work is timely.",
            _contains(r"\btimely\b", r"\bpoised to\b", r"\brecent advances\b", r"\bnow possible\b"),
        ),
    ],
    "innovation": [
        (
            "explicit_innovation_claim",
            "An explicit innovation or novelty claim is made.",
            _contains(r"\bnovel\b", r"\binnovat", r"\bfirst to\b", r"\bdeparts from\b", r"\bnew approach\b"),
        ),
    ],
    "approach": [
        (
            "sample_size_power",
            "A sample-size or statistical power justification is present.",
            _contains(r"\bpower analysis\b", r"\bsample size\b", r"\bpowered to detect\b", r"\beffect size\b", r"\bG\*Power\b"),
        ),
        (
            "timeline",
            "A project timeline is present.",
            _contains(r"\btimeline\b", r"\byear 1\b", r"\bmonths? 1[-–]", r"\bgantt\b"),
        ),
        (
            "pitfalls_alternatives",
            "Potential pitfalls and alternative approaches are addressed.",
            _contains(r"\bpotential pitfall", r"\balternative approach", r"\bif this approach (fails|does not)", r"\bcontingency\b"),
        ),
        (
            "preliminary_data",
            "Preliminary or pilot data is cited.",
            _contains(r"\bpreliminary data\b", r"\bpilot data\b", r"\bour (prior|previous) work\b", r"\bpreliminary studies\b"),
        ),
        (
            "statistical_plan",
            "A statistical analysis plan is described.",
            _contains(r"\bstatistical analysis\b", r"\bwill be analyzed using\b", r"\banova\b", r"\bregression\b", r"\bmixed[- ]effects model\b"),
        ),
    ],
    "rigor": [
        (
            "biological_variables",
            "Sex or gender as a biological variable is addressed.",
            _contains(r"\bsex as a biological variable\b", r"\bsex and gender\b"),
        ),
        (
            "blinding_randomization",
            "Blinding or randomization is mentioned.",
            _contains(r"\bblind(ed|ing)?\b", r"\brandomiz"),
        ),
        (
            "authentication",
            "Authentication of key resources/reagents is mentioned.",
            _contains(r"\bauthenticat", r"\bvalidated reagent", r"\bRRID\b"),
        ),
        (
            "reproducibility_plan",
            "Replication or reproducibility is explicitly discussed.",
            _contains(r"\breplicat", r"\breproducib"),
        ),
    ],
}


def run(sections: dict[str, str]) -> dict:
    """Evaluate every check in CHECKLIST_SPEC against `sections`.

    A section absent from `sections` is treated as present-but-empty: every
    check for it fails, and it is flagged in `missing_sections`.
    """
    section_results: dict[str, dict] = {}
    missing_sections: list[str] = []
    total_checks = 0
    total_passed = 0

    for section_key, checks in CHECKLIST_SPEC.items():
        text = sections.get(section_key, "")
        present = bool(text.strip())
        if not present:
            missing_sections.append(section_key)

        check_results = {}
        passed = 0
        for check_id, description, fn in checks:
            ok = present and fn(text)
            check_results[check_id] = {"passed": ok, "description": description}
            total_checks += 1
            if ok:
                passed += 1
                total_passed += 1

        section_results[section_key] = {
            "present": present,
            "checks": check_results,
            "pass_rate": passed / len(checks) if checks else 1.0,
        }

    return {
        "sections": section_results,
        "missing_sections": missing_sections,
        "overall_pass_rate": (total_passed / total_checks) if total_checks else 0.0,
    }


def failed_items(checklist_result: dict, section_keys: list[str] | None = None) -> list[dict]:
    """Flatten the failed checks across the given sections (or all sections)
    into a list of {"section": ..., "id": ..., "description": ...} dicts,
    in CHECKLIST_SPEC order."""
    keys = section_keys if section_keys is not None else list(CHECKLIST_SPEC.keys())
    items = []
    for section_key in keys:
        section = checklist_result["sections"].get(section_key)
        if not section:
            continue
        for check_id, result in section["checks"].items():
            if not result["passed"]:
                items.append({"section": section_key, "id": check_id, "description": result["description"]})
    return items
