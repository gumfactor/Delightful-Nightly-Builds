#!/usr/bin/env python3
"""Launcher: `python lookalike.py <command>` works without installing the package."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from lookalike.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
