"""Deterministic, rule-based IRB/ethics compliance checklist. No AI involved."""
from __future__ import annotations

from dataclasses import dataclass

from src.models import Study

BLOCKING = "blocking"
WARNING = "warning"

# Points deducted from the 100-point completeness score per finding severity.
_SEVERITY_PENALTY = {BLOCKING: 20, WARNING: 8}

# Simple keyword heuristics for safeguard language expected per vulnerable group.
_SAFEGUARD_KEYWORDS = {
    "minors": ("assent", "parental consent", "guardian"),
    "prisoners": ("prisoner representative", "institutional review", "coercion"),
    "cognitively_impaired": ("capacity to consent", "legally authorized representative", "surrogate"),
    "pregnant": ("obstetric", "pregnancy-specific", "fetal risk"),
    "students_as_subjects": ("no academic penalty", "instructor is not the researcher", "grade"),
}

_SECURITY_KEYWORDS = ("encrypt", "password", "secure", "restricted access", "de-identif", "anonymiz")
_WITHDRAWAL_KEYWORDS = ("withdraw", "discontinue participation")


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    field: str


@dataclass
class ChecklistReport:
    findings: list[Finding]

    @property
    def blocking_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == BLOCKING]

    @property
    def warning_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == WARNING]

    @property
    def completeness_score(self) -> int:
        score = 100
        for f in self.findings:
            score -= _SEVERITY_PENALTY[f.severity]
        return max(0, score)

    @property
    def is_clean(self) -> bool:
        return not self.findings


def _rule_required_fields(study: Study) -> list[Finding]:
    findings = []
    checks = {
        "title": study.title,
        "procedures": study.procedures,
        "data_storage_plan": study.data_storage_plan,
        "recruitment_method": study.recruitment_method,
        "consent_process": study.consent_process,
    }
    for field_name, value in checks.items():
        if not value:
            findings.append(
                Finding(
                    BLOCKING,
                    "missing_required_field",
                    f"Required field '{field_name}' is empty.",
                    field_name,
                )
            )
    if not study.data_collected:
        findings.append(
            Finding(
                BLOCKING,
                "missing_required_field",
                "At least one data_collected item is required.",
                "data_collected",
            )
        )
    return findings


def _rule_deception_without_debrief(study: Study) -> list[Finding]:
    if study.deception and not study.deception_debrief:
        return [
            Finding(
                BLOCKING,
                "deception_without_debrief",
                "Study uses deception but no deception_debrief plan is documented.",
                "deception_debrief",
            )
        ]
    return []


def _rule_vulnerable_population_safeguard(study: Study) -> list[Finding]:
    findings = []
    combined_text = f"{study.procedures} {study.consent_process}".lower()
    for group in study.vulnerable_groups:
        if group == "none":
            continue
        keywords = _SAFEGUARD_KEYWORDS.get(group, ())
        if keywords and not any(kw in combined_text for kw in keywords):
            findings.append(
                Finding(
                    WARNING,
                    "vulnerable_population_missing_safeguard",
                    f"Population includes '{group}' but no matching safeguard language "
                    f"found in procedures or consent_process (expected one of: {', '.join(keywords)}).",
                    "population.vulnerable_groups",
                )
            )
    return findings


def _rule_identifiable_data_security(study: Study) -> list[Finding]:
    if study.data_identifiable and not any(
        kw in study.data_storage_plan.lower() for kw in _SECURITY_KEYWORDS
    ):
        return [
            Finding(
                WARNING,
                "identifiable_data_no_security_mention",
                "Data is identifiable but data_storage_plan does not mention any "
                f"security measure (expected one of: {', '.join(_SECURITY_KEYWORDS)}).",
                "data_storage_plan",
            )
        ]
    return []


def _rule_missing_retention_period(study: Study) -> list[Finding]:
    if not study.data_retention_years or study.data_retention_years <= 0:
        return [
            Finding(
                WARNING,
                "missing_retention_period",
                "data_retention_years is missing or zero.",
                "data_retention_years",
            )
        ]
    return []


def _rule_no_risks_documented(study: Study) -> list[Finding]:
    if not study.risks:
        return [
            Finding(
                WARNING,
                "no_risks_documented",
                "No risks are documented. Even minimal-risk studies should state this explicitly.",
                "risks",
            )
        ]
    return []


def _rule_compensation_without_withdrawal_mention(study: Study) -> list[Finding]:
    if study.compensation and not any(
        kw in study.consent_process.lower() for kw in _WITHDRAWAL_KEYWORDS
    ):
        return [
            Finding(
                WARNING,
                "compensation_without_withdrawal_mention",
                "Compensation is offered but consent_process does not mention that "
                "participants may withdraw without losing compensation already earned.",
                "consent_process",
            )
        ]
    return []


_ALL_RULES = (
    _rule_required_fields,
    _rule_deception_without_debrief,
    _rule_vulnerable_population_safeguard,
    _rule_identifiable_data_security,
    _rule_missing_retention_period,
    _rule_no_risks_documented,
    _rule_compensation_without_withdrawal_mention,
)


def run_checklist(study: Study) -> ChecklistReport:
    findings: list[Finding] = []
    for rule in _ALL_RULES:
        findings.extend(rule(study))
    return ChecklistReport(findings=findings)
