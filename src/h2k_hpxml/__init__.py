"""
H2K to HPXML translation package.

This package provides tools for converting Canadian Hot2000 (H2K) building energy
models to US DOE's HPXML format for EnergyPlus simulation.
"""

import os

__version__ = "1.7.0.1.1"

# Check dependencies on first import (unless disabled by CLI tools)
if os.environ.get('H2K_SKIP_AUTO_INSTALL') != '1':
    try:
        from .utils.dependencies import validate_dependencies
        # Only check dependencies, don't auto-install on import
        # Users can run h2k-deps --install-quiet for installation
        validate_dependencies(interactive=False, check_only=True)
    except Exception:
        # Don't fail package import if dependency check fails
        pass

# Import high-level API functions
from .api import convert_h2k_file
from .api import convert_h2k_string
from .api import run_full_workflow
from .api import validate_dependencies

# Keep backward compatibility
from .core.translator import h2ktohpxml

# Public API - only expose these functions to users
__all__ = [
    # Primary API functions
    "convert_h2k_file",  # File-based conversion
    "convert_h2k_string",  # String-based conversion
    "run_full_workflow",  # Complete workflow with simulation
    "validate_dependencies",  # Dependency checking
    # Legacy compatibility
    "h2ktohpxml",  # Original function name
]
