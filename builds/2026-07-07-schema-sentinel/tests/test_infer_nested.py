import infer


def test_nested_dict_field_produces_children_schema():
    records = [
        {"address": {"city": "Toronto", "postal_code": "M5V"}},
        {"address": {"city": "Ottawa", "postal_code": "K1A"}},
    ]
    schema = infer.infer_schema(records)
    assert "children" in schema["address"]
    children = schema["address"]["children"]
    assert children["city"]["types"] == {"str"}
    assert children["postal_code"]["types"] == {"str"}


def test_list_of_dict_field_collects_children_across_items():
    records = [
        {"tags": [{"name": "a", "weight": 1}, {"name": "b", "weight": 2}]},
        {"tags": [{"name": "c", "weight": 3}]},
    ]
    schema = infer.infer_schema(records)
    children = schema["tags"]["children"]
    assert children["name"]["types"] == {"str"}
    assert children["weight"]["types"] == {"int"}
    # 3 dict items total collected across both records' lists
    assert children["name"]["presence_rate"] == 1.0


def test_two_level_nesting_is_recursive():
    records = [{"a": {"b": {"c": 1}}}, {"a": {"b": {"c": 2}}}]
    schema = infer.infer_schema(records)
    assert schema["a"]["children"]["b"]["children"]["c"]["types"] == {"int"}


def test_scalar_list_field_has_no_children():
    records = [{"scores": [1, 2, 3]}]
    schema = infer.infer_schema(records)
    assert schema["scores"]["types"] == {"list"}
    assert "children" not in schema["scores"]


def test_field_missing_dict_in_some_records_lowers_presence():
    records = [{"address": {"city": "Toronto"}}, {}]
    schema = infer.infer_schema(records)
    assert schema["address"]["required"] is False
    assert schema["address"]["presence_rate"] == 0.5
