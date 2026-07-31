"""Optional Claude Haiku layer: turns structural findings into a short,
prioritized, plain-English action list.

Only issue codes, counts, and BIDS entity labels (e.g. "sub-01") are ever
sent — never scan file content, and never anything beyond what the dataset
owner already put in the filenames themselves.
"""

from __future__ import annotations

import os
from collections import Counter

from .bids_rules import Finding

MODEL = "claude-haiku-4-5-20251001"

_PROMPT_TEMPLATE = """You are helping a neuroscience researcher fix a BIDS \
(Brain Imaging Data Structure) dataset before running it through analysis \
pipelines. Below is a structural summary of validation findings — issue \
codes, how many times each occurred, and a few example locations. Write a \
short, prioritized, plain-English action list (most important fix first). \
Be concise and concrete. Do not invent issues that are not listed.

Findings summary:
{summary}
"""


def _build_prompt(findings: list[Finding]) -> str:
    counts = Counter(f.code for f in findings)
    examples: dict[str, str] = {}
    for f in findings:
        if f.code not in examples and f.path:
            examples[f.code] = f.path

    lines = []
    for code, count in counts.most_common():
        example = examples.get(code)
        example_txt = f" (e.g. {example})" if example else ""
        lines.append(f"- {code}: {count} occurrence(s){example_txt}")
    return _PROMPT_TEMPLATE.format(summary="\n".join(lines))


def generate_ai_summary(findings: list[Finding], client=None) -> str | None:
    """Return a plain-English summary, or None if there's nothing to say or
    no API access is configured. `client` is injectable for testing so no
    real network call is ever made in the test suite.
    """
    if not findings:
        return None

    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

    prompt = _build_prompt(findings)
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
