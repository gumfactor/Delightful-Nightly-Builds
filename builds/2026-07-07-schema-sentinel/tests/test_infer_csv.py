import infer


def test_csv_coerces_int_float_bool_and_empty():
    text = "id,score,active,note\n1,2.5,true,\n2,3.5,false,hi\n"
    records = infer.load_records_from_text(text, "data.csv")
    assert records[0] == {"id": 1, "score": 2.5, "active": True, "note": None}
    assert records[1] == {"id": 2, "score": 3.5, "active": False, "note": "hi"}


def test_csv_falls_back_to_string_for_non_numeric():
    text = "name\nAlice\nBob\n"
    records = infer.load_records_from_text(text, "data.csv")
    assert records == [{"name": "Alice"}, {"name": "Bob"}]


def test_csv_schema_matches_json_shape():
    text = "id,name\n1,Alice\n2,Bob\n"
    records = infer.load_records_from_text(text, "data.csv")
    schema = infer.infer_schema(records)
    assert schema["id"]["types"] == {"int"}
    assert schema["id"]["required"] is True
    assert schema["name"]["types"] == {"str"}
    assert schema["name"]["enum_candidate"] is True


def test_csv_boolean_is_not_misread_as_int():
    text = "flag\ntrue\nfalse\n"
    records = infer.load_records_from_text(text, "data.csv")
    schema = infer.infer_schema(records)
    assert schema["flag"]["types"] == {"bool"}


def test_csv_missing_trailing_columns_yield_null():
    text = "a,b\n1,2\n3,\n"
    records = infer.load_records_from_text(text, "data.csv")
    assert records[1]["b"] is None
