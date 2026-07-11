import diff as diff_mod
import infer


def schema_of(records):
    return infer.infer_schema(records)


def test_added_field_is_safe():
    old = schema_of([{"id": 1}])
    new = schema_of([{"id": 1, "email": "a@example.com"}])
    entries = diff_mod.diff_schemas(old, new)
    assert len(entries) == 1
    assert entries[0] == {
        "field": "email",
        "change": "added",
        "severity": "safe",
        "old": None,
        "new": "str",
        "detail": "field added with type(s) str",
    }


def test_removed_field_is_breaking():
    old = schema_of([{"id": 1, "email": "a@example.com"}])
    new = schema_of([{"id": 1}])
    entries = diff_mod.diff_schemas(old, new)
    assert len(entries) == 1
    assert entries[0]["change"] == "removed"
    assert entries[0]["severity"] == "breaking"


def test_type_widened_int_to_float_is_safe():
    old = schema_of([{"amount": 1}, {"amount": 2}])
    new = schema_of([{"amount": 1.5}, {"amount": 2.5}])
    entries = diff_mod.diff_schemas(old, new)
    type_entries = [e for e in entries if e["change"] == "type_changed"]
    assert len(type_entries) == 1
    assert type_entries[0]["severity"] == "safe"


def test_type_changed_str_to_int_is_breaking():
    old = schema_of([{"id": "abc"}])
    new = schema_of([{"id": 123}])
    entries = diff_mod.diff_schemas(old, new)
    type_entries = [e for e in entries if e["change"] == "type_changed"]
    assert len(type_entries) == 1
    assert type_entries[0]["severity"] == "breaking"
    assert type_entries[0]["old"] == "str"
    assert type_entries[0]["new"] == "int"


def test_required_to_optional_is_risky():
    old = schema_of([{"id": 1}, {"id": 2}])
    new = schema_of([{"id": 1}, {}])
    entries = diff_mod.diff_schemas(old, new)
    presence_entries = [e for e in entries if e["change"] == "presence_changed"]
    assert len(presence_entries) == 1
    assert presence_entries[0]["severity"] == "risky"
    assert presence_entries[0]["old"] == "required"
    assert presence_entries[0]["new"] == "optional"


def test_optional_to_required_is_safe():
    old = schema_of([{"id": 1}, {}])
    new = schema_of([{"id": 1}, {"id": 2}])
    entries = diff_mod.diff_schemas(old, new)
    presence_entries = [e for e in entries if e["change"] == "presence_changed"]
    assert len(presence_entries) == 1
    assert presence_entries[0]["severity"] == "safe"


def test_new_enum_value_is_risky():
    old = schema_of([{"status": "active"}, {"status": "active"}])
    new = schema_of([{"status": "active"}, {"status": "cancelled"}])
    entries = diff_mod.diff_schemas(old, new)
    enum_entries = [e for e in entries if e["change"] == "enum_changed"]
    assert len(enum_entries) == 1
    assert enum_entries[0]["severity"] == "risky"
    assert enum_entries[0]["new"] == "cancelled"


def test_removed_enum_value_is_safe():
    old = schema_of([{"status": "active"}, {"status": "cancelled"}])
    new = schema_of([{"status": "active"}, {"status": "active"}])
    entries = diff_mod.diff_schemas(old, new)
    enum_entries = [e for e in entries if e["change"] == "enum_changed"]
    assert len(enum_entries) == 1
    assert enum_entries[0]["severity"] == "safe"
    assert enum_entries[0]["old"] == "cancelled"


def test_nested_field_diff_recurses_with_dotted_path():
    old = schema_of([{"address": {"city": "Toronto"}}])
    new = schema_of([{"address": {"city": 123}}])
    entries = diff_mod.diff_schemas(old, new)
    nested = [e for e in entries if e["field"] == "address.city"]
    assert len(nested) == 1
    assert nested[0]["severity"] == "breaking"


def test_no_changes_yields_empty_diff():
    old = schema_of([{"id": 1, "name": "a"}])
    new = schema_of([{"id": 2, "name": "b"}])
    entries = diff_mod.diff_schemas(old, new)
    assert entries == []


def test_ignore_fields_suppresses_matching_entries():
    old = schema_of([{"id": 1, "last_synced_at": "2026-01-01"}])
    new = schema_of([{"id": 1}])
    entries = diff_mod.diff_schemas(old, new, ignore_fields={"last_synced_at"})
    assert entries == []


def test_nested_structure_removed_is_breaking():
    old = schema_of([{"address": {"city": "Toronto"}}])
    new = schema_of([{"address": "unstructured text"}])
    entries = diff_mod.diff_schemas(old, new)
    top_level = [e for e in entries if e["field"] == "address"]
    assert any(e["severity"] == "breaking" for e in top_level)
