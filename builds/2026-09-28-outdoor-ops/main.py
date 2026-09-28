"""Outdoor Ops entry point.

Usage:
    python3 main.py sync [--location NAME --lat LAT --lon LON --days N --db PATH]
    python3 main.py render [--location NAME --db PATH --out PATH]
    python3 main.py demo [--db PATH --out PATH]
"""

from __future__ import annotations

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
