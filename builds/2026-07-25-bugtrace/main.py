#!/usr/bin/env python3
"""BugTrace entry point. Usage: python3 main.py sync|report|show ..."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
