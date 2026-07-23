from src.schema import (
    DEFAULT_OWNERSHIP_STATUS_VALUES,
    DEFAULT_REQUIRED_COLUMNS,
    Schema,
    normalize_business_name,
    normalize_province,
)


def test_default_schema_has_expected_required_columns():
    schema = Schema.default()
    assert schema.required_columns == DEFAULT_REQUIRED_COLUMNS
    assert schema.ownership_status_values == DEFAULT_OWNERSHIP_STATUS_VALUES


def test_schema_from_dict_overrides_required_columns():
    schema = Schema.from_dict({"required_columns": ["business_name", "province"]})
    assert schema.required_columns == ["business_name", "province"]
    # ownership values fall back to defaults when not provided
    assert schema.ownership_status_values == DEFAULT_OWNERSHIP_STATUS_VALUES


def test_schema_from_dict_empty_falls_back_to_defaults():
    schema = Schema.from_dict({})
    assert schema.required_columns == DEFAULT_REQUIRED_COLUMNS


def test_normalize_province_accepts_code_and_full_name():
    assert normalize_province("on") == "ON"
    assert normalize_province("Ontario") == "ON"
    assert normalize_province("  BC ") == "BC"


def test_normalize_province_rejects_unknown_value():
    assert normalize_province("Ontari-o") is None
    assert normalize_province("Texas") is None


def test_normalize_business_name_strips_legal_suffix_and_punctuation():
    assert normalize_business_name("Northern Lights Bakery Inc") == "northern lights bakery"
    assert normalize_business_name("Northern Lights Bakery") == "northern lights bakery"
    assert normalize_business_name("Acme, Corp.") == "acme"
