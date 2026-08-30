import json

import pytest

from src.graph import Edge, Evidence
from src.layers import assign_layers, find_violations, load_layer_config


def _edge(importer, importee):
    return Edge(importer=importer, importee=importee, evidence=(Evidence(file="f.py", line=1, statement="x"),))


def _write_config(tmp_path, data):
    path = tmp_path / "layers.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_load_layer_config_valid(tmp_path):
    path = _write_config(tmp_path, {"order": ["core", "ui"], "modules": {"core": ["a"], "ui": ["b"]}})
    config = load_layer_config(path)
    assert config["order"] == ["core", "ui"]


def test_load_layer_config_missing_order_key(tmp_path):
    path = _write_config(tmp_path, {"modules": {"core": ["a"]}})
    with pytest.raises(ValueError, match="order"):
        load_layer_config(path)


def test_load_layer_config_unknown_layer_name(tmp_path):
    path = _write_config(tmp_path, {"order": ["core"], "modules": {"ui": ["a"]}})
    with pytest.raises(ValueError, match="ui"):
        load_layer_config(path)


def test_load_layer_config_malformed_json(tmp_path):
    path = tmp_path / "layers.json"
    path.write_text("{not valid json")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_layer_config(str(path))


def test_assign_layers_exact_and_prefix_match():
    config = {"order": ["core", "ui"], "modules": {"core": ["pkg.core"], "ui": ["pkg.ui"]}}
    assignment = assign_layers(["pkg.core", "pkg.core.helpers", "pkg.ui.button"], config)
    assert assignment.assigned["pkg.core"] == "core"
    assert assignment.assigned["pkg.core.helpers"] == "core"
    assert assignment.assigned["pkg.ui.button"] == "ui"


def test_assign_layers_longest_prefix_wins():
    config = {
        "order": ["general", "specific"],
        "modules": {"general": ["pkg"], "specific": ["pkg.special"]},
    }
    assignment = assign_layers(["pkg.special.thing", "pkg.other"], config)
    assert assignment.assigned["pkg.special.thing"] == "specific"
    assert assignment.assigned["pkg.other"] == "general"


def test_assign_layers_reports_unassigned():
    config = {"order": ["core"], "modules": {"core": ["pkg.core"]}}
    assignment = assign_layers(["pkg.core", "unrelated"], config)
    assert assignment.unassigned == ("unrelated",)


def test_find_violations_lower_layer_importing_higher_is_a_violation():
    config = {"order": ["core", "ui"], "modules": {"core": ["core_mod"], "ui": ["ui_mod"]}}
    assignment = assign_layers(["core_mod", "ui_mod"], config)
    violations = find_violations([_edge("core_mod", "ui_mod")], assignment)
    assert len(violations) == 1
    assert violations[0].importer == "core_mod"
    assert violations[0].importee == "ui_mod"


def test_find_violations_higher_layer_importing_lower_is_fine():
    config = {"order": ["core", "ui"], "modules": {"core": ["core_mod"], "ui": ["ui_mod"]}}
    assignment = assign_layers(["core_mod", "ui_mod"], config)
    violations = find_violations([_edge("ui_mod", "core_mod")], assignment)
    assert violations == []


def test_find_violations_excludes_unassigned_modules():
    config = {"order": ["core"], "modules": {"core": ["core_mod"]}}
    assignment = assign_layers(["core_mod", "mystery"], config)
    violations = find_violations([_edge("mystery", "core_mod"), _edge("core_mod", "mystery")], assignment)
    assert violations == []
