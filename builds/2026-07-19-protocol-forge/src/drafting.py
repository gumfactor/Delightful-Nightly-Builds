"""Section drafting with a 3-tier fallback: reuse approved boilerplate,
then the Anthropic API (only if ANTHROPIC_API_KEY is set at runtime), then a
deterministic template. The template tier is always available, so the tool
is fully functional with no API key.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from src.checklist import ChecklistReport
from src.library import ProtocolLibrary, ProtocolRecord
from src.models import Study

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

SECTION_TITLES = {
    "study_summary": "Study Summary",
    "recruitment_consent": "Recruitment & Consent Process",
    "procedures": "Procedures",
    "risks_benefits": "Risks & Benefits",
    "data_management": "Data Management & Confidentiality",
    "vulnerable_populations": "Vulnerable Populations Safeguards",
}

SECTION_ORDER = [
    "study_summary",
    "recruitment_consent",
    "procedures",
    "risks_benefits",
    "data_management",
]


@dataclass
class SectionDraft:
    text: str
    source: str  # "reused" | "ai" | "template"
    source_protocol_id: Optional[int] = None


def _template_study_summary(study: Study) -> str:
    lines = [f'This is a {study.study_type} protocol titled "{study.title}".']
    if study.pi:
        lines.append(f"Principal Investigator: {study.pi}.")
    lines.append(f"Population: {study.population_description}.")
    if study.has_real_vulnerable_groups():
        groups = ", ".join(g for g in study.vulnerable_groups if g != "none")
        lines.append(f"This study includes the following vulnerable population(s): {groups}.")
    return " ".join(lines)


def _template_recruitment_consent(study: Study) -> str:
    lines = [
        f"Participants will be recruited via: {study.recruitment_method}.",
        f"Informed consent will be obtained as follows: {study.consent_process}.",
    ]
    if study.compensation:
        lines.append(
            f"Compensation: {study.compensation}. Participants may withdraw at any time "
            "without losing compensation already earned for completed portions of the study."
        )
    else:
        lines.append("No compensation is offered for participation.")
    return " ".join(lines)


def _template_procedures(study: Study) -> str:
    lines = [study.procedures]
    if study.deception:
        lines.append(
            f"This study involves deception of participants. Debrief plan: {study.deception_debrief}"
        )
    return " ".join(lines)


def _template_risks_benefits(study: Study) -> str:
    if not study.risks:
        return (
            "This study presents no more than minimal risk to participants beyond those "
            "encountered in daily life. No direct benefits to participants are guaranteed; "
            "participation may contribute to generalizable scientific knowledge."
        )
    lines = []
    for r in study.risks:
        sentence = f"Risk: {r.description}."
        if r.likelihood:
            sentence += f" Likelihood: {r.likelihood}."
        if r.mitigation:
            sentence += f" Mitigation: {r.mitigation}."
        lines.append(sentence)
    return " ".join(lines)


def _template_data_management(study: Study) -> str:
    lines = [
        f"Data collected: {', '.join(study.data_collected)}.",
        f"Storage and access plan: {study.data_storage_plan}.",
    ]
    lines.append(
        "Data collected is identifiable."
        if study.data_identifiable
        else "Data collected is not identifiable, or will be de-identified prior to analysis."
    )
    if study.data_retention_years:
        lines.append(
            f"Data will be retained for {study.data_retention_years:g} year(s) following "
            "study completion, then securely destroyed."
        )
    return " ".join(lines)


def _template_vulnerable_populations(study: Study) -> str:
    groups = [g for g in study.vulnerable_groups if g != "none"]
    return (
        "This study involves the following vulnerable population(s): "
        + ", ".join(groups)
        + ". Additional safeguards specific to each group's capacity to consent, potential "
        "for coercion or undue influence, and heightened risk of harm are described in the "
        "Procedures and Recruitment & Consent Process sections above."
    )


_TEMPLATE_FUNCS = {
    "study_summary": _template_study_summary,
    "recruitment_consent": _template_recruitment_consent,
    "procedures": _template_procedures,
    "risks_benefits": _template_risks_benefits,
    "data_management": _template_data_management,
    "vulnerable_populations": _template_vulnerable_populations,
}


def _build_prompt(section_key: str, study: Study) -> str:
    section_title = SECTION_TITLES[section_key]
    return (
        f"Draft the '{section_title}' section of an IRB/ethics protocol for the following "
        f"study, in formal but plain regulatory prose, 2-5 sentences:\n\n"
        f"{json.dumps(study.to_json_dict(), indent=2)}"
    )


def _call_anthropic(prompt: str, api_key: str) -> Optional[str]:
    """Returns the drafted text, or None on any failure (network, auth, malformed
    response) so the caller falls through to the deterministic template tier.
    Never raises.
    """
    body = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                return None
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None

    content = payload.get("content")
    if not content or "text" not in content[0]:
        return None
    text = content[0]["text"].strip()
    return text or None


def draft_section(section_key: str, study: Study, library: ProtocolLibrary) -> SectionDraft:
    match = library.find_reusable_section(study, section_key)
    if match is not None:
        return SectionDraft(text=match.text, source="reused", source_protocol_id=match.source_protocol_id)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        ai_text = _call_anthropic(_build_prompt(section_key, study), api_key)
        if ai_text:
            return SectionDraft(text=ai_text, source="ai")

    return SectionDraft(text=_TEMPLATE_FUNCS[section_key](study), source="template")


def assemble_markdown(
    study: Study, library: ProtocolLibrary, checklist_report: ChecklistReport
) -> tuple[str, dict[str, SectionDraft]]:
    """Returns (full_markdown_document, {section_key: SectionDraft})."""
    keys = list(SECTION_ORDER)
    if study.has_real_vulnerable_groups():
        keys.append("vulnerable_populations")

    drafts: dict[str, SectionDraft] = {}
    parts = [
        f"# {study.title}",
        "",
        f"**Protocol Type:** {study.study_type}  ",
        f"**PI:** {study.pi or '—'}  ",
        "",
    ]
    for key in keys:
        draft = draft_section(key, study, library)
        drafts[key] = draft
        parts.append(f"## {SECTION_TITLES[key]}")
        parts.append("")
        section_text = draft.text
        if draft.source == "reused":
            section_text += f"\n\n_(reused from protocol #{draft.source_protocol_id})_"
        parts.append(section_text)
        parts.append("")

    parts.append("## Compliance Check Summary")
    parts.append("")
    if checklist_report.is_clean:
        parts.append("No compliance issues found.")
    else:
        for finding in checklist_report.findings:
            parts.append(
                f"- **[{finding.severity.upper()}]** `{finding.code}` ({finding.field}): {finding.message}"
            )
        parts.append("")
        parts.append(f"Completeness score: {checklist_report.completeness_score}/100")

    return "\n".join(parts), drafts


def render_stored_protocol(record: ProtocolRecord) -> str:
    """Reconstructs the Markdown document for an already-saved protocol from its
    stored sections (used by `show`), annotating each section with its source.
    """
    keys = list(SECTION_ORDER)
    if record.study.has_real_vulnerable_groups():
        keys.append("vulnerable_populations")

    parts = [
        f"# {record.study.title}",
        "",
        f"**Protocol Type:** {record.study.study_type}  ",
        f"**PI:** {record.study.pi or '—'}  ",
        f"**Status:** {record.status}  ",
        f"**Completeness Score:** {record.completeness_score}/100  ",
        "",
    ]
    for key in keys:
        section = record.sections.get(key)
        if section is None:
            continue
        parts.append(f"## {SECTION_TITLES[key]} _(source: {section['source']})_")
        parts.append("")
        parts.append(section["text"])
        parts.append("")

    return "\n".join(parts)
