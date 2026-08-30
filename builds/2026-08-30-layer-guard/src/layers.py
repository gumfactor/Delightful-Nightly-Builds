"""Load an explicit layer ordering, assign discovered modules to layers by
dotted-prefix match, and flag every import that violates the ordering."""

from __future__ import annotations

import json
from dataclasses import dataclass

from src.graph import Edge, Evidence


@dataclass(frozen=True)
class LayerAssignment:
    order: tuple[str, ...]
    assigned: dict[str, str]
    unassigned: tuple[str, ...]


@dataclass(frozen=True)
class Violation:
    importer: str
    importer_layer: str
    importee: str
    importee_layer: str
    evidence: tuple[Evidence, ...]


def load_layer_config(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"'{path}' is not valid JSON: {exc}") from exc

    if "order" not in data or "modules" not in data:
        raise ValueError("layers config must contain both 'order' and 'modules' keys")
    order = data["order"]
    if not isinstance(order, list) or not all(isinstance(x, str) for x in order):
        raise ValueError("'order' must be a list of layer name strings")
    for layer_name in data["modules"]:
        if layer_name not in order:
            raise ValueError(f"layer '{layer_name}' in 'modules' is not listed in 'order'")
    return data


def assign_layers(all_modules: list[str], config: dict) -> LayerAssignment:
    order = tuple(config["order"])
    prefix_to_layer: list[tuple[str, str]] = []
    for layer_name, prefixes in config["modules"].items():
        for prefix in prefixes:
            prefix_to_layer.append((prefix, layer_name))
    # Longest prefix wins when a module could match more than one entry.
    prefix_to_layer.sort(key=lambda pair: -len(pair[0]))

    assigned: dict[str, str] = {}
    unassigned: list[str] = []
    for module in all_modules:
        matched = None
        for prefix, layer_name in prefix_to_layer:
            if module == prefix or module.startswith(prefix + "."):
                matched = layer_name
                break
        if matched is not None:
            assigned[module] = matched
        else:
            unassigned.append(module)

    return LayerAssignment(order=order, assigned=assigned, unassigned=tuple(sorted(unassigned)))


def find_violations(edges: list[Edge], layer_assignment: LayerAssignment) -> list[Violation]:
    """A violation is an edge where the importer's layer comes *before*
    the importee's layer in the declared low-to-high order — i.e. a
    lower/more-stable layer reaching up into a higher/less-stable one."""
    order_index = {name: i for i, name in enumerate(layer_assignment.order)}
    violations: list[Violation] = []
    for edge in edges:
        importer_layer = layer_assignment.assigned.get(edge.importer)
        importee_layer = layer_assignment.assigned.get(edge.importee)
        if importer_layer is None or importee_layer is None:
            continue
        if order_index[importer_layer] < order_index[importee_layer]:
            violations.append(
                Violation(
                    importer=edge.importer,
                    importer_layer=importer_layer,
                    importee=edge.importee,
                    importee_layer=importee_layer,
                    evidence=edge.evidence,
                )
            )
    return sorted(violations, key=lambda v: (v.importer, v.importee))
