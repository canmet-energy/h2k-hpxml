"""
Example H2K files for testing and demonstration.

This module provides access to sample H2K files included with the package.
"""

import os
from pathlib import Path
from typing import List
from typing import Optional


def get_examples_directory() -> Path:
    """
    Get the path to the examples directory.

    Returns:
        Path to the examples directory containing sample H2K files
    """
    return Path(__file__).parent


def list_example_files(extension: str = ".h2k") -> List[Path]:
    """
    List all example files with the given extension.

    Args:
        extension: File extension to filter by (default: ".h2k")

    Returns:
        List of Path objects for matching example files
    """
    examples_dir = get_examples_directory()
    pattern = f"*{extension}"
    files = list(examples_dir.glob(pattern))

    # Also check for uppercase extension
    if extension.lower() != extension:
        upper_pattern = f"*{extension.upper()}"
        files.extend(examples_dir.glob(upper_pattern))
    else:
        upper_pattern = f"*{extension.upper()}"
        files.extend(examples_dir.glob(upper_pattern))

    return sorted(files)


def get_example_file(filename: Optional[str] = None) -> Optional[Path]:
    """
    Get path to a specific example file, or the first available if none specified.

    Args:
        filename: Name of the example file (e.g., "WizardHouse.h2k")
                 If None, returns the first available H2K file

    Returns:
        Path to the example file, or None if not found
    """
    examples_dir = get_examples_directory()

    if filename is None:
        # Return first available H2K file
        example_files = list_example_files(".h2k")
        if example_files:
            return example_files[0]
        return None

    example_path = examples_dir / filename
    if example_path.exists():
        return example_path

    return None


def get_wizard_house() -> Optional[Path]:
    """
    Get path to the WizardHouse.h2k example file.

    Returns:
        Path to WizardHouse.h2k, or None if not found
    """
    return get_example_file("WizardHouse.h2k")


# Convenience constants
EXAMPLES_DIR = get_examples_directory()
