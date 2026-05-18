#!/usr/bin/env python3
"""Markdown Engine - CLI entry point (delegates to markdown_engine.main)."""

import sys
from pathlib import Path

from system.markdown_engine.markdown_engine import main


if __name__ == "__main__":
    sys.exit(main())
