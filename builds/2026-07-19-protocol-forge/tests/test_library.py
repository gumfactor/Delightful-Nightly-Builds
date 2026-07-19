import pytest

from src.library import STATUS_APPROVED, STATUS_DRAFT, ProtocolLibrary
from src.models import Study
from tests.factories import make_study_dict


@pytest.fixture
def library(tmp_path):
    lib = ProtocolLibrary(tmp_path / "test_library.db")
    yield lib
    lib.close()


def _sections(text="Some section text."):
    return {"study_summary": (text, "template")}


def test_save_protocol_returns_id_and_lists(library):
    study = Study.from_dict(make_study_dict())
    protocol_id = library.save_protocol(study, _sections(), completeness_score=100)
    assert isinstance(protocol_id, int)

    protocols = library.list_protocols()
    assert len(protocols) == 1
    assert protocols[0]["id"] == protocol_id
    assert protocols[0]["status"] == STATUS_DRAFT
    assert protocols[0]["title"] == study.title


def test_get_protocol_round_trips_study_and_sections(library):
    study = Study.from_dict(make_study_dict())
    protocol_id = library.save_protocol(study, _sections("Reusable summary text."), completeness_score=92)

    record = library.get_protocol(protocol_id)
    assert record is not None
    assert record.title == study.title
    assert record.completeness_score == 92
    assert record.sections["study_summary"]["text"] == "Reusable summary text."
    assert record.sections["study_summary"]["source"] == "template"
    assert record.study.title == study.title


def test_get_protocol_returns_none_for_unknown_id(library):
    assert library.get_protocol(999) is None


def test_approve_marks_status(library):
    study = Study.from_dict(make_study_dict())
    protocol_id = library.save_protocol(study, _sections(), completeness_score=100)
    library.approve(protocol_id)
    record = library.get_protocol(protocol_id)
    assert record.status == STATUS_APPROVED


def test_approve_unknown_id_raises(library):
    with pytest.raises(ValueError):
        library.approve(999)


def test_find_reusable_section_no_match_when_no_approved_protocols(library):
    study = Study.from_dict(make_study_dict())
    library.save_protocol(study, _sections(), completeness_score=100)  # stays draft
    match = library.find_reusable_section(study, "study_summary")
    assert match is None


def test_find_reusable_section_matches_approved_protocol(library):
    data = make_study_dict()
    data["population"]["vulnerable_groups"] = ["minors"]
    study = Study.from_dict(data)
    protocol_id = library.save_protocol(study, _sections("Approved boilerplate."), completeness_score=100)
    library.approve(protocol_id)

    new_study = Study.from_dict(data)  # identical tag profile
    match = library.find_reusable_section(new_study, "study_summary")
    assert match is not None
    assert match.text == "Approved boilerplate."
    assert match.source_protocol_id == protocol_id


def test_find_reusable_section_no_match_for_different_section_key(library):
    data = make_study_dict()
    study = Study.from_dict(data)
    protocol_id = library.save_protocol(study, _sections(), completeness_score=100)
    library.approve(protocol_id)

    match = library.find_reusable_section(study, "risks_benefits")
    assert match is None


def test_find_reusable_section_below_threshold_returns_none(library):
    data = make_study_dict()
    data["population"]["vulnerable_groups"] = ["minors"]
    data["data_identifiable"] = True
    data["deception"] = True
    study = Study.from_dict(data)
    protocol_id = library.save_protocol(study, _sections(), completeness_score=100)
    library.approve(protocol_id)

    # A study with a very different tag profile (no vulnerable groups, not
    # identifiable, no deception) should fall below the reuse threshold.
    dissimilar = Study.from_dict(make_study_dict())
    match = library.find_reusable_section(dissimilar, "study_summary")
    assert match is None


def test_find_reusable_section_picks_best_of_multiple_matches(library):
    data_a = make_study_dict()
    data_a["population"]["vulnerable_groups"] = ["minors"]
    study_a = Study.from_dict(data_a)
    id_a = library.save_protocol(study_a, _sections("From A, partial match."), completeness_score=100)
    library.approve(id_a)

    data_b = make_study_dict()
    data_b["population"]["vulnerable_groups"] = ["minors"]
    data_b["data_identifiable"] = True
    study_b = Study.from_dict(data_b)
    id_b = library.save_protocol(study_b, _sections("From B, exact match."), completeness_score=100)
    library.approve(id_b)

    query_data = make_study_dict(data_identifiable=True)
    query_data["population"]["vulnerable_groups"] = ["minors"]
    query = Study.from_dict(query_data)

    match = library.find_reusable_section(query, "study_summary")
    assert match is not None
    assert match.source_protocol_id == id_b
