"""Layer Guard — entry point.

Usage:
    python main.py <root> [--layers layers.json] [--exclude PATTERN] [--json] [--html report.html]
"""

from src.cli import main

if __name__ == "__main__":
    main()
