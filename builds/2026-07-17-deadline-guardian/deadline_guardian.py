#!/usr/bin/env python3
"""Entry point for Deadline Guardian.

Usage: python3 deadline_guardian.py <add|capture|complete|list|render> [options]
Run with --help for the full command reference.
"""

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
