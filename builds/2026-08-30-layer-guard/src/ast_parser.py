"""Extract import statements from a Python source file via ``ast`` only.

The source is never executed — ``ast.parse`` builds a syntax tree without
running any code, which is what makes it safe to point this tool at
arbitrary, even broken, codebases.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass

from src.scanner import SourceFile


@dataclass(frozen=True)
class ImportRef:
    importer: str  # dotted module name of the file being parsed
    target: str  # resolved dotted name of the import target
    kind: str  # "first_party" | "stdlib" | "external"
    file: str
    line: int
    statement: str


def _resolve_relative(importer_module: str, is_package: bool, level: int, module: str | None) -> str:
    """Mirrors CPython's own relative-import resolution algorithm
    (``importlib._bootstrap._resolve_name``)."""
    package = importer_module if is_package else importer_module.rpartition(".")[0]
    if level > 1:
        bits = package.rsplit(".", level - 1)
        base = bits[0]
    else:
        base = package
    if module:
        return f"{base}.{module}" if base else module
    return base


def _resolve_first_party(candidate: str, known_modules: set[str]) -> str | None:
    """Progressively shorten a dotted candidate until it matches a known
    module, since ``from pkg.sub import name`` may target either a real
    submodule ``pkg.sub.name`` or an attribute of ``pkg.sub``."""
    if not candidate:
        return None
    parts = candidate.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        if cand in known_modules:
            return cand
    return None


def _classify(
    source_file: SourceFile,
    candidate: str,
    node: ast.AST,
    source: str,
    known_modules: set[str],
    stdlib_names: set[str],
) -> ImportRef:
    statement = (ast.get_source_segment(source, node) or "").strip()
    first_party = _resolve_first_party(candidate, known_modules)
    if first_party:
        target, kind = first_party, "first_party"
    else:
        top = candidate.split(".")[0] if candidate else ""
        kind = "stdlib" if (top in stdlib_names or top == "builtins") else "external"
        target = candidate
    return ImportRef(
        importer=source_file.module,
        target=target,
        kind=kind,
        file=source_file.path,
        line=getattr(node, "lineno", 0),
        statement=statement,
    )


def parse_file(
    source_file: SourceFile, known_modules: set[str], stdlib_names: set[str]
) -> tuple[list[ImportRef], str | None]:
    """Parse one file's imports. Returns ``(refs, warning)`` — ``warning``
    is set (and ``refs`` empty) when the file can't be read or parsed, so a
    single broken file never aborts the whole scan."""
    try:
        with open(source_file.path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        return [], f"could not read {source_file.path}: {exc}"

    try:
        tree = ast.parse(source, filename=source_file.path)
    except SyntaxError as exc:
        return [], f"syntax error in {source_file.path}: {exc}"

    is_package = os.path.basename(source_file.path) == "__init__.py"
    refs: list[ImportRef] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                refs.append(_classify(source_file, alias.name, node, source, known_modules, stdlib_names))
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                base = _resolve_relative(source_file.module, is_package, node.level, node.module)
            else:
                base = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    candidate = base
                else:
                    candidate = f"{base}.{alias.name}" if base else alias.name
                refs.append(_classify(source_file, candidate, node, source, known_modules, stdlib_names))

    return refs, None
