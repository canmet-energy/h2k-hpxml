#!/usr/bin/env python3
"""
H2K GUI Launcher Script

Simple launcher script for the H2K to HPXML Converter GUI.
Place this in the project root for easy access.
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from h2k_hpxml.gui.main import main
    sys.exit(main())