"""Optional Claude Haiku refactor-advice note.

Only aggregate structural data ever leaves the machine: cycle chains as
module-name lists, violation tuples, and top structural-risk module names
with their metrics. No file paths, no source text. With no
``ANTHROPIC_API_KEY`` set, this makes zero network calls and returns a
deterministic template built from the same data.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from src.graph import Cycle, ModuleMetrics
from src.layers import Violation

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"
TOP_RISK_LIMIT = 3


def _top_risk(metrics: list[ModuleMetrics]) -> list[ModuleMetrics]:
    risky = [m for m in metrics if m.structural_risk]
    return sorted(risky, key=lambda m: -(m.instability or 0.0))[:TOP_RISK_LIMIT]


def _deterministic_note(cycles: list[Cycle], violations: list[Violation], top_risk: list[ModuleMetrics]) -> str:
    if not cycles and not violations and not top_risk:
        return "No cycles, layering violations, or structural-risk modules found — this codebase's import graph looks healthy."

    parts = []
    if cycles:
        worst = cycles[0]
        parts.append(
            f"Priority: break the {len(worst.modules) - 1}-module import cycle "
            f"({' -> '.join(worst.modules)}) by introducing a shared interface or moving the "
            "shared logic into a lower-level module both sides can depend on."
        )
    if violations:
        v = violations[0]
        parts.append(
            f"{len(violations)} layering violation(s) found; the clearest is '{v.importer}' "
            f"({v.importer_layer}) importing '{v.importee}' ({v.importee_layer}) — invert that "
            "dependency or move the shared code down a layer."
        )
    if top_risk:
        m = top_risk[0]
        parts.append(
            f"'{m.module}' is both heavily depended-upon (afferent={m.afferent}) and highly "
            f"unstable (instability={m.instability:.2f}) — consider extracting a stable "
            "interface so its dependents aren't exposed to its churn."
        )
    return " ".join(parts)


def _build_prompt(cycles: list[Cycle], violations: list[Violation], top_risk: list[ModuleMetrics]) -> str:
    lines = [
        "You are reviewing the structural health of a Python codebase's import graph.",
        "Only aggregate structure is provided below — no source code or file paths.",
        "",
        f"Import cycles found: {len(cycles)}",
    ]
    for c in cycles[:5]:
        lines.append(f"  - {' -> '.join(c.modules)}")
    lines.append(f"Layering violations found: {len(violations)}")
    for v in violations[:5]:
        lines.append(f"  - {v.importer} ({v.importer_layer}) -> {v.importee} ({v.importee_layer})")
    lines.append(f"Structurally risky modules (high instability + heavily depended-upon): {len(top_risk)}")
    for m in top_risk:
        lines.append(f"  - {m.module}: afferent={m.afferent}, efferent={m.efferent}, instability={m.instability:.2f}")
    lines.append("")
    lines.append("In 2-4 sentences, give prioritized, concrete refactoring advice.")
    return "\n".join(lines)


def _call_anthropic(prompt: str, api_key: str) -> str:
    body = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["content"][0]["text"].strip()


def build_note(
    cycles: list[Cycle],
    violations: list[Violation],
    metrics: list[ModuleMetrics],
    api_key: str | None,
) -> str:
    top_risk = _top_risk(metrics)
    if not api_key:
        return _deterministic_note(cycles, violations, top_risk)

    prompt = _build_prompt(cycles, violations, top_risk)
    try:
        return _call_anthropic(prompt, api_key)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError, OSError):
        return _deterministic_note(cycles, violations, top_risk)
