"""Layer Guard CLI: orchestrates scanning, parsing, graph analysis, layer
checking, the optional AI note, and output rendering."""

from __future__ import annotations

import argparse
import os
import sys

from src import ast_parser, graph, report
from src import layers as layers_mod
from src import ai, scanner


def analyze(
    root: str,
    layers_path: str | None = None,
    exclude: list[str] | None = None,
    api_key: str | None = None,
) -> report.AnalysisResult:
    """Run the full analysis pipeline and return a structured result.
    Reusable independent of the CLI (used directly by tests)."""
    source_files = scanner.discover(root, exclude=exclude)
    known_modules = {sf.module for sf in source_files}
    stdlib_names = set(getattr(sys, "stdlib_module_names", ()))

    all_refs: list[ast_parser.ImportRef] = []
    warnings: list[str] = []
    for source_file in source_files:
        refs, warning = ast_parser.parse_file(source_file, known_modules, stdlib_names)
        all_refs.extend(refs)
        if warning:
            warnings.append(warning)

    edges = graph.build_edges(all_refs)
    all_modules = sorted(known_modules)
    cycles = graph.find_cycles(all_modules, edges)
    metrics = graph.compute_metrics(all_modules, edges)

    layer_assignment = None
    violations: list[layers_mod.Violation] = []
    if layers_path:
        config = layers_mod.load_layer_config(layers_path)
        layer_assignment = layers_mod.assign_layers(all_modules, config)
        violations = layers_mod.find_violations(edges, layer_assignment)

    ai_note = ai.build_note(cycles, violations, metrics, api_key)

    return report.AnalysisResult(
        root=os.path.abspath(root),
        modules=all_modules,
        edges=edges,
        cycles=cycles,
        metrics=metrics,
        layer_assignment=layer_assignment,
        violations=violations,
        ai_note=ai_note,
        warnings=warnings,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="layer-guard",
        description="Detect import cycles, layering violations, and coupling risk in a Python codebase.",
    )
    parser.add_argument("root", help="Root directory of the Python codebase to scan")
    parser.add_argument("--layers", metavar="PATH", help="Path to a layers.json config for layering-violation checks")
    parser.add_argument(
        "--exclude", metavar="PATTERN", action="append", default=[], help="Additional glob pattern to exclude (repeatable)"
    )
    parser.add_argument("--json", action="store_true", help="Print the full analysis as JSON instead of a terminal summary")
    parser.add_argument("--html", metavar="PATH", help="Write a self-contained HTML dashboard to PATH")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color in the terminal summary")
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    try:
        result = analyze(args.root, layers_path=args.layers, exclude=args.exclude, api_key=api_key)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.html:
        try:
            with open(args.html, "w", encoding="utf-8") as fh:
                fh.write(report.render_html(result))
        except OSError as exc:
            print(f"Error writing HTML report: {exc}", file=sys.stderr)
            return 1
        print(f"HTML report written to {args.html}")

    if args.json:
        print(report.render_json(result))
    else:
        print(report.render_terminal(result, use_color=not args.no_color))

    return 2 if result.cycles else 0


def main() -> None:
    sys.exit(run())
