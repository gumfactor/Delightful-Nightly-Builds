# Manual — Layer Guard

> **Version:** 1.0 (built 2026-08-30)
> **Complexity:** Ambitious

---

## What This Is

Layer Guard is a Python CLI that reads any Python codebase's import statements — never executing a single line of the code it scans — and answers three questions a growing codebase eventually needs answered: does it have real circular imports, which modules are both heavily depended-upon and unstable (a maintenance risk), and (if you tell it your intended architecture) does anything actually violate it. It's for the moment a project has grown past the point where you can hold its whole shape in your head, and you want a concrete, evidence-backed answer instead of a hunch.

---

## Quick Start

1. `cd` into this build's folder: `builds/2026-08-30-layer-guard/`
2. Try it on itself first — there's nothing to set up: `python3 main.py . --exclude tests --exclude .pytest_cache --layers layers.example.json`
3. Try it on any other Python project you have locally: `python3 main.py /path/to/your/project`
4. Add `--html report.html` to get a browsable dashboard, or `--json` for machine-readable output.
5. (Optional) `export ANTHROPIC_API_KEY=sk-...` before running for an AI-written refactor-advice paragraph — everything works identically without it.

---

## How to Use It

### Basic scan (cycles + coupling metrics only)

```
python3 main.py /path/to/project
```

Prints a terminal summary: module/edge counts, any import cycles found (with the exact file:line of every import statement forming the cycle), and any "structurally risky" modules — ones that are both heavily depended-upon (afferent coupling ≥ 2) and highly unstable (instability ≥ 0.8). Exits with code `2` if any cycle is found (useful for a CI gate: `layer-guard . || echo "cycles found"`), otherwise `0`.

### Checking against a declared architecture

Layer Guard can't safely guess what architecture you *intend* — it can only tell you when code violates one you declare. Write a `layers.json`:

```json
{
  "order": ["core", "presentation", "cli"],
  "modules": {
    "core": ["src.scanner", "src.ast_parser", "src.graph", "src.layers"],
    "presentation": ["src.report", "src.ai"],
    "cli": ["src.cli", "main"]
  }
}
```

`order` lists your layers from lowest/most-stable to highest/least-stable. The rule: a module in an earlier layer must never import from a later layer (a "core" module reaching up into "cli" is a violation; "cli" importing from "core" is fine — that's the normal direction). Module names are matched by dotted prefix, so `"src.graph"` also covers `src.graph.helpers` if that existed. Anything not matched by any entry is reported separately as "unassigned" and excluded from violation checks — it's never silently misclassified.

Run it: `python3 main.py . --layers layers.example.json` (the committed `layers.example.json` describes this build's own architecture — run it to see a real example with zero violations, which is also how this build verified its own design during development).

### Reading the HTML report

`--html report.html` writes a self-contained dashboard you can open in any browser (no server needed): hero stats, a dependency graph (nodes colored by layer, cycle edges in red, layering violations in orange), a sortable/searchable per-module metrics table, and full Cycles/Violations panels with exact evidence. Open it directly — `file:///path/to/report.html` — no internet connection required.

### The AI note

If `ANTHROPIC_API_KEY` is set in your environment, Layer Guard sends **only** aggregate structure to Claude Haiku — cycle chains as module-name lists, violation tuples, and the names/metrics of the top structurally-risky modules. It never sends file contents, file paths, or anything from your actual source code. Without a key, you get a clear deterministic summary built from the exact same data — the tool is fully functional either way.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `root` (positional) | — (required) | Directory to scan recursively for `.py` files |
| `--layers PATH` | none | Path to a `layers.json` config; omit to skip layering checks entirely |
| `--exclude PATTERN` | (repeatable) | Additional glob pattern to exclude, on top of the built-in defaults (`.git`, `__pycache__`, `venv`, `.venv`, `node_modules`, `.tox`, `build`, `dist`) |
| `--json` | off | Print the full analysis as JSON instead of the terminal summary |
| `--html PATH` | none | Also write a self-contained HTML dashboard to this path |
| `--no-color` | off | Disable ANSI color codes in the terminal summary (also respects the `NO_COLOR` environment variable) |
| `ANTHROPIC_API_KEY` (env var) | unset | When set, enables the AI refactor-advice note; the tool works fully without it |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| "scan root does not exist or is not a directory" | Typo'd path, or a relative path resolved from the wrong working directory | Use an absolute path, or double-check your current directory with `pwd` |
| A `layers.json` module never shows up as a violation even though you expect one | The module doesn't actually appear in the import graph — check the report's "Unassigned modules" count, or confirm the prefix in `layers.json` actually matches the module's real dotted name (run with `--json` and inspect the `modules` list) | Fix the prefix in `layers.json`, or check that the file is being discovered at all (not caught by an exclude pattern) |
| A cycle you know exists isn't detected | The import might be dynamic (`importlib.import_module(...)`, `__import__(...)`, or gated behind `if TYPE_CHECKING:`) — Layer Guard only sees imports visible to static `ast` parsing, by design (it never executes code) | This is a known, intentional limitation — see FutureFeatures.md |
| "not valid JSON" error on `--layers` | Malformed `layers.json` (trailing comma, missing quote, etc.) | Validate the file with `python3 -m json.tool layers.json` |

---

## Known Limitations

- Python only — no JavaScript/TypeScript/Dart support, since the parser is Python's own `ast` module.
- Dynamic imports (`importlib.import_module`, `__import__`, imports inside `if TYPE_CHECKING:` blocks) are invisible to static analysis by design — the tool never executes scanned code, which is also what makes it safe to point at any codebase, even a broken one.
- No auto-suggested layer ordering — you must declare your intended architecture yourself; the tool checks conformance, it doesn't guess intent.
- Large strongly-connected components (rare in practice) report one concrete illustrative cycle per component rather than an exhaustive enumeration of every possible cycle within it.
