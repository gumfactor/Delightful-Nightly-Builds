#!/usr/bin/env python3
"""Throughline entry point.

Usage:
    python3 main.py lookup "Jane Doe"
    python3 main.py sync --author-id <id> --name "Jane Doe"
    python3 main.py cluster
    python3 main.py narrative [--ai]
    python3 main.py growth
    python3 main.py render [--output dashboard.html]
    python3 main.py papers
"""
from __future__ import annotations

import sys

from src.cli import main as cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
