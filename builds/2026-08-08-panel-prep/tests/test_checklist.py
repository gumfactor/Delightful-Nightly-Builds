import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import checklist

COMPLETE_SECTIONS = {
    "aims": (
        "Aim 1: test the mechanism. Aim 2: test the intervention. "
        "Our central hypothesis is that X causes Y. "
        "Upon completion of these aims, this work will provide a new framework."
    ),
    "significance": (
        "A critical barrier to progress is that the mechanism remains unknown. "
        "Recent advances make this work timely."
    ),
    "innovation": "This proposal is novel and is the first to combine these methods.",
    "approach": (
        "A power analysis indicates a sample size of 80 participants. "
        "Timeline: Year 1 will focus on recruitment. "
        "Potential pitfalls include recruitment delay; an alternative approach is remote testing. "
        "Preliminary data from our lab show feasibility. "
        "Data will be analyzed using mixed-effects regression models."
    ),
    "rigor": (
        "Sex as a biological variable will be considered. "
        "Raters will be blinded and condition order randomized. "
        "All reagents will be authenticated against RRID identifiers. "
        "We will assess reproducibility in an independent sample."
    ),
}


def test_complete_sections_pass_every_check():
    result = checklist.run(COMPLETE_SECTIONS)
    assert result["overall_pass_rate"] == 1.0
    assert result["missing_sections"] == []


def test_all_sections_missing_fails_every_check():
    result = checklist.run({})
    assert result["overall_pass_rate"] == 0.0
    assert set(result["missing_sections"]) == set(checklist.CHECKLIST_SPEC.keys())


def test_missing_section_is_flagged_present_false():
    result = checklist.run({"aims": COMPLETE_SECTIONS["aims"]})
    assert result["sections"]["aims"]["present"] is True
    assert result["sections"]["significance"]["present"] is False
    assert result["sections"]["significance"]["pass_rate"] == 0.0


def test_numbered_aims_check_requires_aim_marker():
    passing = checklist.run({"aims": "Aim 1: do X. Aim 2: do Y."})
    failing = checklist.run({"aims": "We will explore several related questions about X."})
    assert passing["sections"]["aims"]["checks"]["numbered_aims"]["passed"] is True
    assert failing["sections"]["aims"]["checks"]["numbered_aims"]["passed"] is False


def test_sample_size_power_check_in_approach():
    passing = checklist.run({"approach": "A power analysis indicates a sample size of 100."})
    failing = checklist.run({"approach": "We will recruit as many participants as possible."})
    assert passing["sections"]["approach"]["checks"]["sample_size_power"]["passed"] is True
    assert failing["sections"]["approach"]["checks"]["sample_size_power"]["passed"] is False


def test_rigor_checks_case_insensitive():
    result = checklist.run({"rigor": "PARTICIPANTS WILL BE RANDOMIZED AND RATERS BLINDED."})
    assert result["sections"]["rigor"]["checks"]["blinding_randomization"]["passed"] is True


def test_failed_items_returns_only_failed_checks():
    result = checklist.run({"aims": "A vague paragraph with no structure."})
    failed = checklist.failed_items(result, section_keys=["aims"])
    assert len(failed) == 3
    assert all(item["section"] == "aims" for item in failed)


def test_failed_items_empty_when_all_pass():
    result = checklist.run(COMPLETE_SECTIONS)
    failed = checklist.failed_items(result)
    assert failed == []


def test_partial_pass_rate_between_zero_and_one():
    result = checklist.run({"approach": "A power analysis indicates a sample size of 80."})
    rate = result["sections"]["approach"]["pass_rate"]
    assert 0.0 < rate < 1.0
