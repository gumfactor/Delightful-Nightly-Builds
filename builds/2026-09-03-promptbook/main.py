#!/usr/bin/env python3
"""Entry point for the Promptbook CLI. Run as `python main.py <command> ...`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
