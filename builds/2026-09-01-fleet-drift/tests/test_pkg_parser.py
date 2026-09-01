import json

from src.pkg_parser import parse_package_json


def _pkg(dependencies=None, dev_dependencies=None):
    body = {}
    if dependencies is not None:
        body["dependencies"] = dependencies
    if dev_dependencies is not None:
        body["devDependencies"] = dev_dependencies
    return json.dumps(body)


def test_parses_exact_version():
    entries = parse_package_json(_pkg(dependencies={"react": "18.3.1"}))
    assert entries == [{"name": "react", "pinned_version": "18.3.1", "pin_kind": "exact"}]


def test_caret_prefix_is_range():
    entries = parse_package_json(_pkg(dependencies={"react": "^18.3.1"}))
    assert entries == [{"name": "react", "pinned_version": "18.3.1", "pin_kind": "range"}]


def test_tilde_prefix_is_range():
    entries = parse_package_json(_pkg(dependencies={"lodash": "~4.17.21"}))
    assert entries == [{"name": "lodash", "pinned_version": "4.17.21", "pin_kind": "range"}]


def test_gte_prefix_is_range():
    entries = parse_package_json(_pkg(dependencies={"vite": ">=5.0.0"}))
    assert entries == [{"name": "vite", "pinned_version": "5.0.0", "pin_kind": "range"}]


def test_reads_both_dependencies_and_dev_dependencies():
    entries = parse_package_json(_pkg(dependencies={"react": "18.3.1"}, dev_dependencies={"vitest": "1.6.0"}))
    names = {e["name"] for e in entries}
    assert names == {"react", "vitest"}


def test_dependencies_wins_over_dev_dependencies_on_name_conflict():
    entries = parse_package_json(_pkg(dependencies={"shared": "2.0.0"}, dev_dependencies={"shared": "1.0.0"}))
    assert entries == [{"name": "shared", "pinned_version": "2.0.0", "pin_kind": "exact"}]


def test_wildcard_spec_is_unparseable():
    entries = parse_package_json(_pkg(dependencies={"anything": "*"}))
    assert entries == [{"name": "anything", "pinned_version": None, "pin_kind": "unparseable"}]


def test_workspace_spec_is_unparseable():
    entries = parse_package_json(_pkg(dependencies={"internal-lib": "workspace:*"}))
    assert entries == [{"name": "internal-lib", "pinned_version": None, "pin_kind": "unparseable"}]


def test_malformed_json_returns_empty_list_without_crashing():
    assert parse_package_json("{not valid json") == []


def test_non_object_top_level_returns_empty_list():
    assert parse_package_json("[1, 2, 3]") == []


def test_missing_dependency_sections_returns_empty_list():
    assert parse_package_json(json.dumps({"name": "my-app", "version": "1.0.0"})) == []


def test_non_string_dependency_value_is_skipped():
    body = json.dumps({"dependencies": {"weird": 123}})
    assert parse_package_json(body) == []
