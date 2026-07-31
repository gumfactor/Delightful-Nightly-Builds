"""Anthropic API integration for Stats Coach.

Generates a plain-English explanation of why a specific statistical
test is appropriate for the given research design.
"""

from __future__ import annotations
import os

import anthropic


def build_prompt(
    test_name: str,
    outcome_type: str,
    num_groups: int,
    paired: bool,
    normality: str,
    relationship: bool,
    study_context: str,
    assumptions: list[str],
) -> str:
    groups_desc = {1: "one group", 2: "two groups", 3: "three or more groups"}.get(
        num_groups if num_groups <= 3 else 3, "three or more groups"
    )
    paired_desc = "paired/repeated-measures" if paired else "independent"
    relationship_desc = "testing a relationship between two variables" if relationship else "comparing groups"

    context_line = f"\nStudy context provided by the researcher: {study_context}" if study_context.strip() else ""

    return f"""You are an expert statistics instructor explaining statistical test selection to a researcher or graduate student.

The researcher has described their study design:
- Outcome variable type: {outcome_type}
- Number of groups: {groups_desc}
- Design: {paired_desc}
- Normality assumption: {normality}
- Goal: {relationship_desc}{context_line}

The recommended test is: **{test_name}**

Assumptions that apply:
{chr(10).join(f'- {a}' for a in assumptions)}

Write exactly 3 paragraphs. Do not use headers or bullet points — write flowing prose:

Paragraph 1: Explain what the {test_name} does in plain language a graduate student could understand. Avoid jargon. Focus on what question it answers.

Paragraph 2: Explain specifically why this test is the right choice for this researcher's design — connect the design parameters above to the test's requirements. If normality is violated or unknown, briefly explain why you recommended a non-parametric alternative.

Paragraph 3: Tell the researcher what to look for in the output: which statistic to report, how to interpret the p-value, and what effect size measure to include. Be concrete about reporting format.

Write clearly, directly, and without any AI-sounding filler phrases. Keep total length under 300 words."""


def generate_explanation(
    test_name: str,
    outcome_type: str,
    num_groups: int,
    paired: bool,
    normality: str,
    relationship: bool,
    study_context: str,
    assumptions: list[str],
    client: anthropic.Anthropic | None = None,
) -> str:
    """Call Anthropic API to generate a personalized test explanation.

    Returns the explanation string, or a fallback message on API error.
    """
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.Anthropic(api_key=api_key)

    prompt = build_prompt(
        test_name=test_name,
        outcome_type=outcome_type,
        num_groups=num_groups,
        paired=paired,
        normality=normality,
        relationship=relationship,
        study_context=study_context,
        assumptions=assumptions,
    )

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as exc:
        return (
            f"The {test_name} is appropriate for this research design. "
            f"(AI explanation unavailable: {type(exc).__name__})"
        )
