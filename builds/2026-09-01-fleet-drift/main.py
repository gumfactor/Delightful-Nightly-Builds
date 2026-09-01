#!/usr/bin/env python3
"""Fleet Drift — cross-repo dependency version drift dashboard.

Usage:
    GITHUB_TOKEN=... python main.py sync
    python main.py render [--ai]
    python main.py list
    python main.py history python requests

See Manual.md for the full command reference.
"""
from __future__ import annotations

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
