"""Build the first-party module dependency graph and analyze it: cycle
detection via an iterative Tarjan's strongly-connected-components
algorithm, plus per-module coupling/instability metrics."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.ast_parser import ImportRef

STRUCTURAL_RISK_INSTABILITY_THRESHOLD = 0.8
STRUCTURAL_RISK_MIN_AFFERENT = 2


@dataclass(frozen=True)
class Evidence:
    file: str
    line: int
    statement: str


@dataclass(frozen=True)
class Edge:
    importer: str
    importee: str
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class Cycle:
    modules: tuple[str, ...]  # ordered chain; first element repeats at the end
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class ModuleMetrics:
    module: str
    afferent: int
    efferent: int
    instability: float | None
    structural_risk: bool


def build_edges(refs: list[ImportRef]) -> list[Edge]:
    """Deduplicate first-party import references into edges, keeping every
    contributing statement as evidence."""
    grouped: dict[tuple[str, str], list[Evidence]] = {}
    for ref in refs:
        if ref.kind != "first_party":
            continue
        if ref.importer == ref.target:
            continue  # a module referencing itself is not a real dependency edge
        key = (ref.importer, ref.target)
        grouped.setdefault(key, []).append(Evidence(ref.file, ref.line, ref.statement))
    edges = [Edge(importer=k[0], importee=k[1], evidence=tuple(v)) for k, v in grouped.items()]
    return sorted(edges, key=lambda e: (e.importer, e.importee))


def _adjacency(all_modules: list[str], edges: list[Edge]) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {m: [] for m in all_modules}
    for e in edges:
        adj.setdefault(e.importer, []).append(e.importee)
    for m in adj:
        adj[m].sort()
    return adj


def _tarjan_scc(all_modules: list[str], adjacency: dict[str, list[str]]) -> list[list[str]]:
    """Iterative Tarjan's SCC algorithm (explicit work stack, no recursion)
    so it never risks Python's recursion limit on a large real codebase."""
    index_counter = 0
    index: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    tarjan_stack: list[str] = []
    result: list[list[str]] = []

    for start in all_modules:
        if start in index:
            continue

        work: list[tuple[str, "list[str]", int]] = [(start, adjacency.get(start, []), 0)]
        index[start] = index_counter
        lowlink[start] = index_counter
        index_counter += 1
        tarjan_stack.append(start)
        on_stack[start] = True

        while work:
            v, neighbors, pos = work[-1]
            advanced = False
            i = pos
            while i < len(neighbors):
                w = neighbors[i]
                i += 1
                if w not in index:
                    index[w] = index_counter
                    lowlink[w] = index_counter
                    index_counter += 1
                    tarjan_stack.append(w)
                    on_stack[w] = True
                    work[-1] = (v, neighbors, i)
                    work.append((w, adjacency.get(w, []), 0))
                    advanced = True
                    break
                elif on_stack.get(w):
                    lowlink[v] = min(lowlink[v], index[w])
            if advanced:
                continue

            work[-1] = (v, neighbors, i)
            work.pop()
            if work:
                parent, _, _ = work[-1]
                lowlink[parent] = min(lowlink[parent], lowlink[v])
            if lowlink[v] == index[v]:
                component = []
                while True:
                    w = tarjan_stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == v:
                        break
                result.append(component)

    return result


def _extract_one_cycle(scc_nodes: set[str], adjacency: dict[str, list[str]]) -> list[str]:
    """Walk a strongly-connected component to produce one concrete cycle
    chain (a genuine SCC is not guaranteed to be Hamiltonian, so this finds
    *a* real cycle within it rather than assuming one pass covers every
    member)."""
    start = min(scc_nodes)
    path = [start]
    position = {start: 0}
    current = start
    while True:
        candidates = sorted(n for n in adjacency.get(current, []) if n in scc_nodes)
        if not candidates:
            return path  # should not happen for a genuine size>1 SCC
        next_node = candidates[0]
        if next_node in position:
            return path[position[next_node] :] + [next_node]
        path.append(next_node)
        position[next_node] = len(path) - 1
        current = next_node


def find_cycles(all_modules: list[str], edges: list[Edge]) -> list[Cycle]:
    adjacency = _adjacency(all_modules, edges)
    edges_by_pair = {(e.importer, e.importee): e for e in edges}
    cycles: list[Cycle] = []

    for component in _tarjan_scc(all_modules, adjacency):
        if len(component) < 2:
            continue
        chain = _extract_one_cycle(set(component), adjacency)
        chain_edges = []
        for a, b in zip(chain, chain[1:]):
            edge = edges_by_pair.get((a, b))
            if edge is not None:
                chain_edges.append(edge)
        cycles.append(Cycle(modules=tuple(chain), edges=tuple(chain_edges)))

    return sorted(cycles, key=lambda c: c.modules)


def compute_metrics(all_modules: list[str], edges: list[Edge]) -> list[ModuleMetrics]:
    efferent: dict[str, set[str]] = {m: set() for m in all_modules}
    afferent: dict[str, set[str]] = {m: set() for m in all_modules}
    for e in edges:
        efferent.setdefault(e.importer, set()).add(e.importee)
        afferent.setdefault(e.importee, set()).add(e.importer)

    metrics = []
    for m in all_modules:
        ce = len(efferent.get(m, set()))
        ca = len(afferent.get(m, set()))
        instability = (ce / (ce + ca)) if (ce + ca) > 0 else None
        structural_risk = (
            instability is not None
            and instability >= STRUCTURAL_RISK_INSTABILITY_THRESHOLD
            and ca >= STRUCTURAL_RISK_MIN_AFFERENT
        )
        metrics.append(
            ModuleMetrics(module=m, afferent=ca, efferent=ce, instability=instability, structural_risk=structural_risk)
        )
    return sorted(metrics, key=lambda x: x.module)
