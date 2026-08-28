#!/usr/bin/env python3
"""EDGAR Lens entry point.

Usage:
    python main.py sync --tickers AAPL,MSFT
    python main.py list
    python main.py show AAPL
    python main.py flags
    python main.py render --ai
"""

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
