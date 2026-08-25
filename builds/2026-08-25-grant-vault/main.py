#!/usr/bin/env python3
"""Grant Vault entry point.

Usage:
    python3 main.py ingest <path> [--ai] [--db grantvault.db]
    python3 main.py search [query] [--section TYPE] [--tag TAG] [--min-reuse N]
    python3 main.py stats
    python3 main.py render [--output grant_vault_dashboard.html]
"""

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
