import pytest

import infer


def test_scalar_type_inference():
    records = [{"a": "x", "b": 1, "c": 1.5, "d": True, "e": None}]
    schema = infer.infer_schema(records)
    assert schema["a"]["types"] == {"str"}
    assert schema["b"]["types"] == {"int"}
    assert schema["c"]["types"] == {"float"}
    assert schema["d"]["types"] == {"bool"}
    assert schema["e"]["types"] == {"null"}


def test_mixed_type_field():
    records = [{"x": 1}, {"x": "one"}, {"x": None}]
    schema = infer.infer_schema(records)
    assert schema["x"]["types"] == {"int", "str", "null"}


def test_required_field_present_in_all_records():
    records = [{"id": 1}, {"id": 2}, {"id": 3}]
    schema = infer.infer_schema(records)
    assert schema["id"]["required"] is True
    assert schema["id"]["presence_rate"] == 1.0


def test_field_missing_from_some_records_is_not_required():
    records = [{"id": 1, "name": "a"}, {"id": 2}]
    schema = infer.infer_schema(records)
    assert schema["name"]["required"] is False
    assert schema["name"]["presence_rate"] == 0.5


def test_null_value_counts_as_absent_for_required():
    records = [{"id": 1, "note": "hi"}, {"id": 2, "note": None}]
    schema = infer.infer_schema(records)
    assert schema["note"]["required"] is False
    assert schema["note"]["presence_rate"] == 0.5


def test_enum_candidate_detected_for_low_cardinality_strings():
    records = [{"status": "active"}, {"status": "cancelled"}, {"status": "active"}]
    schema = infer.infer_schema(records)
    assert schema["status"]["enum_candidate"] is True
    assert schema["status"]["enum_values"] == {"active", "cancelled"}


def test_enum_candidate_rejected_above_cardinality_threshold():
    records = [{"id": str(i)} for i in range(20)]
    schema = infer.infer_schema(records)
    assert schema["id"]["enum_candidate"] is False


def test_enum_candidate_requires_at_least_two_occurrences():
    records = [{"status": "active"}]
    schema = infer.infer_schema(records)
    assert schema["status"]["enum_candidate"] is False


def test_single_json_object_treated_as_one_record():
    records = infer.load_records_from_text('{"a": 1, "b": "x"}', "snapshot.json")
    assert records == [{"a": 1, "b": "x"}]


def test_json_array_of_objects():
    records = infer.load_records_from_text('[{"a": 1}, {"a": 2}]', "snapshot.json")
    assert records == [{"a": 1}, {"a": 2}]


def test_malformed_json_raises_clear_error():
    with pytest.raises(infer.SchemaInferenceError, match="Malformed JSON"):
        infer.load_records_from_text("{not valid json", "snapshot.json")


def test_empty_json_file_raises_clear_error():
    with pytest.raises(infer.SchemaInferenceError, match="Malformed JSON"):
        infer.load_records_from_text("", "snapshot.json")


def test_unsupported_extension_raises_clear_error():
    with pytest.raises(infer.SchemaInferenceError, match="Unsupported file extension"):
        infer.load_records_from_text("data", "snapshot.txt")


def test_top_level_scalar_json_rejected():
    with pytest.raises(infer.SchemaInferenceError, match="object or an array"):
        infer.load_records_from_text("42", "snapshot.json")
