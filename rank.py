#!/usr/bin/env python3
"""Entry point for the Redrob India Runs candidate ranker."""

import sys
from pathlib import Path

# Add src to sys.path to allow imports from the ranker package
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from ranker.main import run_cli

if __name__ == "__main__":
    run_cli()
