#!/usr/bin/env python3
"""Thesis Breaker -- adversarial bear-case critique for your own investment thesis.

Usage:
    python3 main.py demo
    python3 main.py check AAPL --thesis "Bullish because ..."
    python3 main.py history AAPL
    python3 main.py render --id 3
    python3 main.py list
"""
import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
