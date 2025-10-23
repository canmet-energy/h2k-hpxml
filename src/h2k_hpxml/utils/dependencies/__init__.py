"""
Dependency management for h2k_hpxml.

This package provides modular dependency management for OpenStudio and OpenStudio-HPXML.
"""

import platform
import shutil
from pathlib import Path

# Core functionality
from .manager import DependencyManager
from .cli import validate_dependencies, main
from .download_utils import download_file, safe_echo

# Platform utilities (available for direct use)
from .platform_utils import (
    load_dependency_config,
    get_user_data_dir,
    get_openstudio_paths,
    get_default_hpxml_path,
    get_default_openstudio_path,
)


# Lightweight helper functions (don't create DependencyManager instances!)
def get_dependency_paths():
    """Get all dependency paths in a single call."""
    config = load_dependency_config()
    openstudio_binary = get_openstudio_binary()
    hpxml_os_path = get_hpxml_os_path()

    # EnergyPlus is bundled with OpenStudio
    energyplus_binary = None
    if openstudio_binary:
        openstudio_dir = Path(openstudio_binary).parent.parent
        if Path(openstudio_binary).name == "openstudio.exe":
            energyplus_binary = str(openstudio_dir / "EnergyPlus" / "energyplus.exe")
        else:
            energyplus_binary = str(openstudio_dir / "EnergyPlus" / "energyplus")

        if not Path(energyplus_binary).exists():
            energyplus_binary = None

    return {
        "openstudio_binary": openstudio_binary,
        "hpxml_os_path": hpxml_os_path,
        "energyplus_binary": energyplus_binary,
    }


def get_openstudio_binary():
    """Get OpenStudio binary path without creating DependencyManager."""
    config = load_dependency_config()
    paths = get_openstudio_paths(config["openstudio_version"], config["openstudio_sha"], None)

    for path in paths:
        if Path(path).exists():
            return str(path)

    # Fallback to system PATH
    system_path = shutil.which("openstudio")
    if system_path:
        return system_path

    return None


def get_hpxml_os_path():
    """Get OpenStudio-HPXML path without creating DependencyManager."""
    config = load_dependency_config()
    hpxml_path = get_default_hpxml_path(config["openstudio_hpxml_version"], None)

    if hpxml_path.exists():
        return str(hpxml_path)

    return None


def get_energyplus_binary():
    """Get EnergyPlus binary path."""
    paths = get_dependency_paths()
    return paths["energyplus_binary"]


# Aliases for backward compatibility
get_openstudio_path = get_openstudio_binary
get_openstudio_hpxml_path = get_hpxml_os_path
get_openstudio_path_static = get_openstudio_binary
get_openstudio_hpxml_path_static = get_hpxml_os_path

# Export all public APIs
__all__ = [
    # Core classes and functions
    "DependencyManager",
    "validate_dependencies",
    "main",
    # Download utilities
    "download_file",
    "safe_echo",
    # Compatibility functions
    "get_dependency_paths",
    "get_openstudio_binary",
    "get_hpxml_os_path",
    "get_energyplus_binary",
    "get_openstudio_path",
    "get_openstudio_hpxml_path",
    "get_openstudio_path_static",
    "get_openstudio_hpxml_path_static",
    # Platform utilities
    "load_dependency_config",
    "get_user_data_dir",
    "get_openstudio_paths",
    "get_default_hpxml_path",
    "get_default_openstudio_path",
]
