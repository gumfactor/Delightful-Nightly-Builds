from src.ast_parser import ImportRef
from src.graph import Edge, Evidence, build_edges, compute_metrics, find_cycles


def _ref(importer, target, kind="first_party", file="f.py", line=1, statement=""):
    return ImportRef(importer=importer, target=target, kind=kind, file=file, line=line, statement=statement or f"import {target}")


def _edge(importer, importee):
    return Edge(importer=importer, importee=importee, evidence=(Evidence(file="f.py", line=1, statement="x"),))


def test_build_edges_dedupes_and_keeps_all_evidence():
    refs = [
        _ref("a", "b", line=1, statement="import b"),
        _ref("a", "b", line=5, statement="from b import x"),
    ]
    edges = build_edges(refs)
    assert len(edges) == 1
    assert len(edges[0].evidence) == 2


def test_build_edges_skips_non_first_party_refs():
    refs = [_ref("a", "os", kind="stdlib"), _ref("a", "requests", kind="external")]
    edges = build_edges(refs)
    assert edges == []


def test_build_edges_skips_self_import():
    refs = [_ref("a", "a")]
    edges = build_edges(refs)
    assert edges == []


def test_find_cycles_no_false_positive_on_diamond():
    # a -> b, a -> c, b -> d, c -> d  (converges but no cycle)
    edges = [_edge("a", "b"), _edge("a", "c"), _edge("b", "d"), _edge("c", "d")]
    cycles = find_cycles(["a", "b", "c", "d"], edges)
    assert cycles == []


def test_find_cycles_two_node_cycle():
    edges = [_edge("a", "b"), _edge("b", "a")]
    cycles = find_cycles(["a", "b"], edges)
    assert len(cycles) == 1
    assert cycles[0].modules == ("a", "b", "a")


def test_find_cycles_three_node_cycle_with_evidence():
    edges = [_edge("a", "b"), _edge("b", "c"), _edge("c", "a")]
    cycles = find_cycles(["a", "b", "c"], edges)
    assert len(cycles) == 1
    assert cycles[0].modules == ("a", "b", "c", "a")
    assert len(cycles[0].edges) == 3


def test_find_cycles_disconnected_components_only_reports_the_cyclic_one():
    edges = [_edge("a", "b"), _edge("b", "a"), _edge("x", "y")]
    cycles = find_cycles(["a", "b", "x", "y"], edges)
    assert len(cycles) == 1
    assert set(cycles[0].modules) == {"a", "b"}


def test_find_cycles_isolated_module_is_not_a_cycle():
    cycles = find_cycles(["lonely"], [])
    assert cycles == []


def test_compute_metrics_afferent_and_efferent_counts():
    edges = [_edge("a", "b"), _edge("c", "b")]
    metrics = {m.module: m for m in compute_metrics(["a", "b", "c"], edges)}
    assert metrics["b"].afferent == 2
    assert metrics["b"].efferent == 0
    assert metrics["a"].afferent == 0
    assert metrics["a"].efferent == 1


def test_compute_metrics_instability_formula():
    # a imports 3 modules, nobody imports a -> maximally unstable (I=1.0)
    edges = [_edge("a", "b"), _edge("a", "c"), _edge("a", "d")]
    metrics = {m.module: m for m in compute_metrics(["a", "b", "c", "d"], edges)}
    assert metrics["a"].instability == 1.0
    # b/c/d each have Ca=1, Ce=0 -> maximally stable (I=0.0)
    assert metrics["b"].instability == 0.0


def test_compute_metrics_isolated_module_has_none_instability():
    metrics = {m.module: m for m in compute_metrics(["lonely"], [])}
    assert metrics["lonely"].instability is None
    assert metrics["lonely"].structural_risk is False


def test_compute_metrics_structural_risk_boundary():
    # "hub" is imported by 2 modules (Ca=2) and imports 8 others (Ce=8) -> I=0.8, Ca=2 -> risky
    edges = [_edge("dep1", "hub"), _edge("dep2", "hub")] + [_edge("hub", f"x{i}") for i in range(8)]
    modules = ["hub", "dep1", "dep2"] + [f"x{i}" for i in range(8)]
    metrics = {m.module: m for m in compute_metrics(modules, edges)}
    assert metrics["hub"].instability == 0.8
    assert metrics["hub"].structural_risk is True


def test_compute_metrics_not_risky_when_afferent_too_low():
    # Only one module depends on "hub" (Ca=1) -> not flagged even though instability is high
    edges = [_edge("dep1", "hub")] + [_edge("hub", f"x{i}") for i in range(5)]
    modules = ["hub", "dep1"] + [f"x{i}" for i in range(5)]
    metrics = {m.module: m for m in compute_metrics(modules, edges)}
    assert metrics["hub"].instability > 0.8
    assert metrics["hub"].afferent == 1
    assert metrics["hub"].structural_risk is False
