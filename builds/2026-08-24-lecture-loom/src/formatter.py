"""Renders a parsed Lecture + LectureReport (+ optional polish) to Markdown."""
from __future__ import annotations

from pathlib import Path

from ai_polish import PolishResult
from parser import Lecture
from timing import LectureReport

STATUS_LABELS = {
    "on_target": "On target",
    "over_budget": "Over budget",
    "under_budget": "Under budget",
}


def _bullets_for(lecture: Lecture, polish: PolishResult | None, heading: str, original: list[str]) -> list[str]:
    if polish is not None and heading in polish.sections:
        return polish.sections[heading]
    return list(original)


def build_outline_md(lecture: Lecture, report: LectureReport, polish: PolishResult | None = None) -> str:
    lines = [f"# {lecture.title}", ""]

    lines.append("## Learning Objectives")
    if lecture.objectives:
        lines.extend(f"- {obj}" for obj in lecture.objectives)
    else:
        lines.append("- _(none detected — add an \"Objectives\" section or a \"By the end of this lecture...\" sentence)_")
    lines.append("")

    lines.append("## Timing Summary")
    lines.append(
        f"- Target: {report.target_minutes:.1f} min | Estimated: {report.total_minutes:.1f} min "
        f"| Status: {STATUS_LABELS[report.budget_status]}"
    )
    if report.budget_status == "over_budget" and report.worst_section:
        lines.append(f"- Longest section: {report.worst_section}")
    if report.dense_sections:
        lines.append(f"- Dense sections (consider splitting): {', '.join(report.dense_sections)}")
    if report.heading_skip_warning:
        lines.append("- Warning: a heading level was skipped (e.g. H1 straight to H3)")
    lines.append("")

    for section, timing in zip(lecture.sections, report.section_timings):
        lines.append(f"## {section.heading} — ~{timing.estimated_minutes:.1f} min")
        for bullet in _bullets_for(lecture, polish, section.heading, section.bullets):
            lines.append(f"- {bullet}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_handout_md(lecture: Lecture, polish: PolishResult | None = None) -> str:
    lines = [f"# {lecture.title}", ""]

    lines.append("## Learning Objectives")
    if lecture.objectives:
        lines.extend(f"- {obj}" for obj in lecture.objectives)
    else:
        lines.append("- _(none detected)_")
    lines.append("")

    for section in lecture.sections:
        lines.append(f"## {section.heading}")
        for bullet in _bullets_for(lecture, polish, section.heading, section.bullets):
            lines.append(f"- {bullet}")
        for prose in section.prose:
            lines.append(prose)
        lines.append("")

    if polish is not None and polish.discussion_questions:
        lines.append("## Discussion Questions")
        for i, question in enumerate(polish.discussion_questions, start=1):
            lines.append(f"{i}. {question}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    lecture: Lecture,
    report: LectureReport,
    output_dir: Path,
    polish: PolishResult | None = None,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(lecture.path).stem
    outline_path = output_dir / f"{stem}.outline.md"
    handout_path = output_dir / f"{stem}.handout.md"
    outline_path.write_text(build_outline_md(lecture, report, polish), encoding="utf-8")
    handout_path.write_text(build_handout_md(lecture, polish), encoding="utf-8")
    return outline_path, handout_path
