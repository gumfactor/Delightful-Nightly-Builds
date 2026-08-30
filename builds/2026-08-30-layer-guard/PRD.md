# PRD — Layer Guard

> **Build date:** 2026-08-30
> **Category:** H — Developer Tool
> **Complexity:** Ambitious (every build is ambitious per CLAUDE.md's config)
> **Day of week:** Sunday

---

## Goal

A Python CLI that parses any Python codebase's import graph via `ast` (no execution), detects real circular-import cycles with a from-scratch Tarjan's strongly-connected-components algorithm, computes per-module afferent/efferent coupling and instability metrics, and — when the user supplies an explicit layer ordering — flags every import that violates it, all rendered as a terminal report, JSON, or a self-contained interactive HTML dashboard.

## User Story

As an intermediate-to-advanced developer who is "increasingly focused on expanding beyond traditional academia into AI-enabled software" and explicitly wants to "better understand scalable software architecture" while avoiding "overly complex architectures," I want to point a tool at any of my Python codebases (this repo, or a future one) and see exactly where its module dependencies have gone tangled — real import cycles, and modules that are both heavily depended-upon and unstable — so that I can catch and fix architectural decay before it compounds, without manually tracing imports file by file.

## Scope

### In Scope
- Recursive `.py` file discovery under a given root directory, with sensible default excludes (`.git`, `__pycache__`, `venv`, `.venv`, `node_modules`, `.tox`, `build`, `dist`) plus a user `--exclude` glob list
- AST-based import extraction (`ast.parse`, no code execution ever) for `import a.b.c`, `import a.b.c as x`, `from a.b import c`, and relative imports (`from . import x`, `from ..pkg import y`) with correct `ImportFrom.level` resolution against each file's package position
- Module-name derivation from file paths (package-aware: honors `__init__.py`) and best-effort progressive-prefix matching so `from pkg.sub import name` resolves to the closest real module in the scanned set
- Classification of every import target as first-party (in-graph), stdlib (via `sys.stdlib_module_names`), or third-party/external (anything else) — only first-party edges enter the graph
- A directed module dependency graph with deduplicated edges, each edge retaining every contributing `(file, line, statement text)` as evidence
- A from-scratch iterative Tarjan's SCC algorithm (no recursion depth risk on large graphs) to find every real import cycle, reported as an ordered module chain with the evidence for each edge in the cycle
- Afferent coupling (Ca), efferent coupling (Ce), and instability (I = Ce / (Ce + Ca), undefined when both are 0) per module
- "Structural risk" flagging: modules with instability ≥ 0.8 **and** afferent coupling ≥ 2 (heavily depended-upon yet itself highly dependent — a Stable Dependencies Principle violation)
- Optional layer-ordering config (`--layers layers.json`): an explicit low-to-high layer order plus a module→layer assignment (exact or dotted-prefix match); any edge where the importing module's layer is *lower* than the imported module's layer is reported as a violation with severity and the exact evidence
- Unassigned modules (present in the graph but not matched by any layer entry) are reported separately and excluded from violation checks, never silently misclassified
- Three output modes: colored terminal summary, `--json` machine-readable export, `--html report.html` self-contained dark-mode dashboard (hero stats, sortable/searchable per-module metrics table, Cycles panel, Violations panel, and a hand-drawn Canvas 2D dependency graph colored by layer with cycle edges in red and violation edges in orange)
- Optional Claude Haiku refactor-advice paragraph per run (`ANTHROPIC_API_KEY` env var) built **only** from aggregate structural data — cycle chains as module-name lists, violation tuples, top instability module names/metrics — never file contents or full source; unconditional deterministic-template fallback with zero network calls when no key is set
- A `layers.example.json` reflecting this build's own architecture, and documentation showing the tool run against its own `src/` folder as a live, self-referential demo

### Out of Scope
- Auto-inferring a layer ordering when none is supplied (the tool works standalone on cycles/metrics without one; the user must supply intent for violation-checking, which is a judgment call it cannot make safely)
- Cross-language support (JS/TS/Dart) — Python `ast` only, matching this build's own primary language and the majority of the user's automation scripts
- Executing or importing the scanned code in any way (pure static analysis — this is also what makes it safe to point at arbitrary, even broken, codebases)
- Auto-fixing cycles or violations (report-only, matching this catalog's established read-only developer-tool pattern, e.g. Landing Pattern)
- A persistent history/trend database across runs (each run is a fresh, complete analysis; no SQLite needed since there's no meaningful "drift over time" question here the way there is for e.g. dependency freshness)

## Tech Stack

- **Language:** Python 3.11
- **Framework:** None
- **Dependencies:** stdlib only (`ast`, `sys`, `os`, `json`, `argparse`, `urllib.request` for the optional Anthropic call). No third-party packages required to run.
- **Runtime requirement:** `python3 main.py <root> [--layers layers.json] [--html report.html] [--json]`

## Data Structure

No persistent storage — every run is a stateless, complete analysis of the codebase as it currently exists on disk. In-memory data model per run:

```python
Module = str  # dotted module name, e.g. "src.graph"

Edge = {
    "importer": Module,
    "importee": Module,
    "evidence": [{"file": str, "line": int, "statement": str}, ...],
}

Cycle = {
    "modules": [Module, ...],   # ordered chain, first == last implied
    "edges": [Edge, ...],       # the edges forming the cycle, in order
}

ModuleMetrics = {
    "module": Module,
    "afferent": int,       # Ca: modules that import this one
    "efferent": int,       # Ce: modules this one imports
    "instability": float | None,  # Ce / (Ce + Ca), None if Ce+Ca == 0
    "structural_risk": bool,
}

Violation = {
    "importer": Module, "importer_layer": str,
    "importee": Module, "importee_layer": str,
    "evidence": [{"file": str, "line": int, "statement": str}, ...],
}

AnalysisResult = {
    "root": str,
    "modules": [Module, ...],
    "edges": [Edge, ...],
    "cycles": [Cycle, ...],
    "metrics": [ModuleMetrics, ...],
    "layers": {"order": [str,...], "assigned": {Module: str}, "unassigned": [Module,...]} | None,
    "violations": [Violation, ...],
    "ai_note": str | None,
}
```

`layers.json` input format:
```json
{
  "order": ["core", "presentation", "cli"],
  "modules": {
    "core": ["scanner", "ast_parser", "graph", "layers"],
    "presentation": ["report", "ai"],
    "cli": ["cli"]
  }
}
```

## Folder Structure

```
builds/2026-08-30-layer-guard/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── pytest.ini
├── .gitignore
├── main.py
├── layers.example.json
├── src/
│   ├── __init__.py
│   ├── scanner.py
│   ├── ast_parser.py
│   ├── graph.py
│   ├── layers.py
│   ├── ai.py
│   ├── report.py
│   └── cli.py
└── tests/
    ├── test_scanner.py
    ├── test_ast_parser.py
    ├── test_graph.py
    ├── test_layers.py
    ├── test_ai.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - File discovery: nested packages found, default excludes (`.git`, `__pycache__`, `venv`) respected, user `--exclude` globs respected
  - Module naming: package-aware dotted names, `__init__.py` handling, flat (non-package) directories
  - Import extraction: plain `import`, `import ... as`, `from ... import`, multi-name `from` imports, relative imports at various `level`s, syntax-error files skipped gracefully (not a crash)
  - stdlib/third-party filtering: `os`, `json` excluded from the graph; a fake third-party name excluded
  - Progressive-prefix resolution: `from pkg.sub import name` resolving to `pkg.sub` when `pkg.sub.name` doesn't exist as a module
  - Tarjan's SCC: two-node cycle, three-node cycle, self-loop, acyclic diamond graph (no false positive), disconnected components, a graph with one cycle and one separate acyclic branch
  - Coupling metrics: correct Ca/Ce counts on a hand-built graph, instability formula, `None` instability for an isolated module, structural-risk flag boundary conditions
  - Layer violations: a correct low→high edge (no violation), a genuine high→low-reversed violation, prefix-matched module assignment, unassigned modules excluded from violations but listed separately
  - AI layer: mocked `urlopen` returns a Claude response → note used; no `ANTHROPIC_API_KEY` → deterministic fallback with **zero** `urlopen` calls (call-count assertion)
  - Report rendering: JSON output round-trips the `AnalysisResult` shape; HTML report contains expected section markers and safely escapes a `</script><script>` payload injected into a module name so it never appears as an executable tag
  - CLI: nonexistent root path errors clearly; empty directory produces a valid empty report instead of crashing; `--layers` pointing at a malformed JSON file errors clearly instead of crashing

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. Running the tool against its own `src/` folder with `layers.example.json` produces zero false-positive cycles and a violations list that matches the architecture actually written (verified by hand)
3. A synthetic fixture with a deliberately introduced 3-module import cycle is correctly detected, with accurate file:line evidence for every edge in the cycle
4. The HTML report renders with zero unescaped injection when a module name (via a synthetic fixture with an unusual file name) contains `</script><script>alert(1)</script>`-style content
5. With no `ANTHROPIC_API_KEY` set, a full run makes zero network calls and still produces a complete report via the deterministic fallback

---

## Scope Changes

None — full in-scope feature set was delivered as planned. (See BUILD_LOG.md for any minor implementation-detail adjustments made while coding.)
