"""Discover Python source files under a root directory and derive their
dotted module names, without ever importing or executing them."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass

DEFAULT_EXCLUDES = (
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "node_modules",
    ".tox",
    "build",
    "dist",
)


@dataclass(frozen=True)
class SourceFile:
    path: str  # absolute path on disk
    module: str  # dotted module name relative to the scanned root


def _is_excluded(name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def _path_to_module(rel_path: str) -> str:
    """Convert a root-relative file path to a dotted module name.

    Package-aware: a trailing ``__init__`` component (the package itself)
    is dropped so the package's own module name is its directory name.
    """
    without_ext = rel_path[: -len(".py")] if rel_path.endswith(".py") else rel_path
    parts = without_ext.replace(os.sep, "/").split("/")
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(p for p in parts if p)


def discover(root: str, exclude: list[str] | None = None) -> list[SourceFile]:
    """Recursively find every ``.py`` file under ``root``.

    ``exclude`` is a list of additional fnmatch-style glob patterns matched
    against individual path components (directory or file names), on top
    of the built-in ``DEFAULT_EXCLUDES``.
    """
    if not os.path.isdir(root):
        raise FileNotFoundError(f"scan root does not exist or is not a directory: {root}")

    patterns = DEFAULT_EXCLUDES + tuple(exclude or ())
    root = os.path.abspath(root)
    found: list[SourceFile] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not _is_excluded(d, patterns)]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            if _is_excluded(filename, patterns):
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, root)
            module = _path_to_module(rel_path)
            if not module:
                # A bare root-level __init__.py has no meaningful module
                # name of its own; skip rather than emit an empty string.
                continue
            found.append(SourceFile(path=abs_path, module=module))

    return sorted(found, key=lambda f: f.module)
