from src.checklist import BLOCKING, WARNING, run_checklist
from src.models import Study
from tests.factories import make_study_dict


def _codes(report):
    return {f.code for f in report.findings}


def test_clean_study_has_no_findings():
    study = Study.from_dict(make_study_dict())
    report = run_checklist(study)
    assert report.is_clean
    assert report.completeness_score == 100


def test_missing_procedures_flagged():
    # Study.from_dict rejects an empty procedures field outright, so to exercise
    # the checklist rule directly we build a valid Study then clear the field
    # in-memory (checklist.py must not assume from_dict already guarantees this).
    study = Study.from_dict(make_study_dict())
    study.procedures = ""
    report = run_checklist(study)
    assert "missing_required_field" in _codes(report)
    assert any(f.severity == BLOCKING for f in report.findings)


def test_missing_data_collected_flagged():
    study = Study.from_dict(make_study_dict())
    study.data_collected = []
    report = run_checklist(study)
    assert "missing_required_field" in _codes(report)


def test_deception_without_debrief_flagged():
    data = make_study_dict(deception=True, deception_debrief="")
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "deception_without_debrief" in _codes(report)
    finding = next(f for f in report.findings if f.code == "deception_without_debrief")
    assert finding.severity == BLOCKING


def test_deception_with_debrief_not_flagged():
    data = make_study_dict(
        deception=True, deception_debrief="Participants are fully debriefed immediately after the session."
    )
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "deception_without_debrief" not in _codes(report)


def test_vulnerable_population_missing_safeguard_flagged():
    data = make_study_dict()
    data["population"]["vulnerable_groups"] = ["minors"]
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "vulnerable_population_missing_safeguard" in _codes(report)
    finding = next(f for f in report.findings if f.code == "vulnerable_population_missing_safeguard")
    assert finding.severity == WARNING


def test_vulnerable_population_safeguard_in_procedures_not_flagged():
    data = make_study_dict(
        procedures="Participants complete a task after providing assent alongside parental consent."
    )
    data["population"]["vulnerable_groups"] = ["minors"]
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "vulnerable_population_missing_safeguard" not in _codes(report)


def test_vulnerable_population_safeguard_in_consent_process_not_flagged():
    """Regression: safeguard language written in consent_process (not procedures)
    must also satisfy the rule — assent language is conventionally documented there."""
    data = make_study_dict(
        consent_process="Minors provide assent and a parent or guardian provides consent before participation."
    )
    data["population"]["vulnerable_groups"] = ["minors"]
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "vulnerable_population_missing_safeguard" not in _codes(report)


def test_identifiable_data_no_security_mention_flagged():
    data = make_study_dict(data_identifiable=True, data_storage_plan="Data is stored on a shared department drive.")
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "identifiable_data_no_security_mention" in _codes(report)


def test_identifiable_data_with_security_mention_not_flagged():
    data = make_study_dict(
        data_identifiable=True,
        data_storage_plan="Data is stored on an encrypted, password-protected server with restricted access.",
    )
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "identifiable_data_no_security_mention" not in _codes(report)


def test_missing_retention_period_flagged():
    data = make_study_dict(data_retention_years=0)
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "missing_retention_period" in _codes(report)


def test_no_risks_documented_flagged():
    data = make_study_dict(risks=[])
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "no_risks_documented" in _codes(report)


def test_compensation_without_withdrawal_mention_flagged():
    data = make_study_dict(
        compensation="$10 gift card",
        consent_process="Participants review and sign a consent form before beginning the study.",
    )
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "compensation_without_withdrawal_mention" in _codes(report)


def test_no_compensation_skips_withdrawal_rule():
    data = make_study_dict(
        compensation="",
        consent_process="Participants review and sign a consent form before beginning the study.",
    )
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert "compensation_without_withdrawal_mention" not in _codes(report)


def test_completeness_score_deducts_per_finding():
    data = make_study_dict(data_retention_years=0, risks=[])
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert len(report.findings) == 2
    assert report.completeness_score == 100 - 8 - 8


def test_completeness_score_floors_at_zero():
    data = make_study_dict(
        deception=True,
        deception_debrief="",
        data_identifiable=True,
        data_storage_plan="shared drive",
        data_retention_years=0,
        risks=[],
        compensation="$50",
        consent_process="Sign the form.",
    )
    data["population"]["vulnerable_groups"] = ["minors", "prisoners", "pregnant"]
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert report.completeness_score >= 0


def test_blocking_and_warning_findings_partitioned_correctly():
    data = make_study_dict(deception=True, deception_debrief="", data_retention_years=0)
    study = Study.from_dict(data)
    report = run_checklist(study)
    assert any(f.code == "deception_without_debrief" for f in report.blocking_findings)
    assert any(f.code == "missing_retention_period" for f in report.warning_findings)
