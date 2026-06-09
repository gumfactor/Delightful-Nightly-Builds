"""Entry point for ctxlog — AI Session Context Bridge.

Usage:
    python3 main.py <command> [options]

Commands:
    add        Capture a new AI session context entry
    list       List recent sessions
    search     Search sessions by keyword
    handoff    Generate a markdown handoff document
    projects   List all tracked projects
    show       Show full detail for a specific session

Run with --help for full usage.
"""

import sys
from pathlib import Path

# Allow running from the build folder root without installing as a package
sys.path.insert(0, str(Path(__file__).parent))

from src.cli import main

if __name__ == "__main__":
    main()
