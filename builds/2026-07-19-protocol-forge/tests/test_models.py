import json

import pytest

from src.models import Study
from tests.factories import make_study_dict


def test_valid_study_loads_from_dict():
    study = Study.from_dict(make_study_dict())
    assert study.title == "Effects of Time Pressure on Empathic Accuracy"
    assert study.study_type == "new"
    assert study.vulnerable_groups == ["none"]


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        Study.from_file(tmp_path / "does_not_exist.json")


def test_malformed_json_raises_value_error(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json")
    with pytest.raises(ValueError):
        Study.from_file(bad_file)


def test_valid_file_loads(tmp_path):
    good_file = tmp_path / "study.json"
    good_file.write_text(json.dumps(make_study_dict()))
    study = Study.from_file(good_file)
    assert study.title == "Effects of Time Pressure on Empathic Accuracy"


@pytest.mark.parametrize("field_to_remove", ["title", "procedures", "data_storage_plan"])
def test_missing_required_field_raises(field_to_remove):
    data = make_study_dict()
    del data[field_to_remove]
    with pytest.raises(ValueError, match=field_to_remove):
        Study.from_dict(data)


def test_invalid_study_type_raises():
    data = make_study_dict(study_type="not_a_real_type")
    with pytest.raises(ValueError, match="study_type"):
        Study.from_dict(data)


def test_invalid_vulnerable_group_raises():
    data = make_study_dict()
    data["population"]["vulnerable_groups"] = ["martians"]
    with pytest.raises(ValueError, match="vulnerable_groups"):
        Study.from_dict(data)


def test_has_real_vulnerable_groups_false_for_none():
    study = Study.from_dict(make_study_dict())
    assert study.has_real_vulnerable_groups() is False


def test_has_real_vulnerable_groups_true_when_present():
    data = make_study_dict()
    data["population"]["vulnerable_groups"] = ["minors"]
    study = Study.from_dict(data)
    assert study.has_real_vulnerable_groups() is True


def test_tag_set_contents():
    data = make_study_dict()
    data["population"]["vulnerable_groups"] = ["minors", "none"]
    data["data_identifiable"] = True
    data["deception"] = True
    study = Study.from_dict(data)
    tags = study.tag_set()
    assert "vg:minors" in tags
    assert "vg:none" not in tags  # "none" is never a real tag
    assert "identifiable:True" in tags
    assert "deception:True" in tags


def test_to_json_dict_round_trips():
    study = Study.from_dict(make_study_dict())
    round_tripped = Study.from_dict(study.to_json_dict())
    assert round_tripped == study
