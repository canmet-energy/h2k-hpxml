#!/usr/bin/env python3
"""
Validation and detection utilities for dependencies.

Provides functions to check if OpenStudio and OpenStudio-HPXML are properly installed.
"""

import os
import re
import subprocess
from pathlib import Path

import click


def check_openstudio(manager):
    """
    Check if OpenStudio CLI is installed and available.

    Args:
        manager: DependencyManager instance

    Returns:
        bool: True if OpenStudio CLI is available
    """
    return check_cli_binary(manager)


def check_cli_binary(manager):
    """Check OpenStudio CLI binary availability."""
    from .platform_utils import get_openstudio_paths

    # Get paths from platform utils
    paths = get_openstudio_paths(
        manager.REQUIRED_OPENSTUDIO_VERSION,
        manager.OPENSTUDIO_BUILD_HASH,
        manager._custom_openstudio_path
    )

    # Try common installation paths
    for openstudio_path in paths:
        if test_binary_path(openstudio_path):
            click.echo(f"✅ OpenStudio CLI: {openstudio_path}")
            return True

    # Try openstudio command in PATH
    if test_openstudio_command():
        click.echo("✅ OpenStudio CLI found in PATH")
        return True

    # Show expected installation path
    if paths:
        click.echo(f"❌ OpenStudio CLI not found (expected: {paths[0]})")
    else:
        click.echo("❌ OpenStudio CLI not found (not in PATH)")
    return False


def test_binary_path(path):
    """Test if OpenStudio binary exists and runs."""
    if not os.path.exists(path):
        return False

    try:
        result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return False


def test_openstudio_command():
    """Test if 'openstudio' command works in PATH."""
    try:
        result = subprocess.run(
            ["openstudio", "--version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return False


def check_openstudio_hpxml(manager):
    """
    Check if OpenStudio-HPXML is installed.

    Args:
        manager: DependencyManager instance

    Returns:
        bool: True if OpenStudio-HPXML is available
    """
    # Check environment variable first
    hpxml_path = os.environ.get("OPENSTUDIO_HPXML_PATH")
    if hpxml_path:
        hpxml_path = Path(hpxml_path)
    else:
        hpxml_path = manager.default_hpxml_path

    if not hpxml_path.exists():
        click.echo(f"❌ OpenStudio-HPXML not found (expected: {hpxml_path})")
        return False

    # Check for required workflow script
    workflow_script = hpxml_path / "workflow" / "run_simulation.rb"
    if not workflow_script.exists():
        click.echo(f"❌ OpenStudio-HPXML workflow script missing: {workflow_script}")
        return False

    # Try to detect version
    version_info = detect_hpxml_version(hpxml_path)
    if version_info:
        click.echo(f"✅ OpenStudio-HPXML: {version_info} at {hpxml_path}")
    else:
        click.echo(f"✅ OpenStudio-HPXML found at: {hpxml_path}")

    return True


def detect_hpxml_version(hpxml_path):
    """
    Try to detect OpenStudio-HPXML version from documentation files.

    Args:
        hpxml_path (Path): Path to OpenStudio-HPXML installation

    Returns:
        str or None: Version string if found, None otherwise
    """
    version_files = ["README.md", "CHANGELOG.md", "docs/source/conf.py"]

    for version_file in version_files:
        file_path = hpxml_path / version_file
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                # Look for version patterns
                patterns = [
                    r"v?(\d+\.\d+\.\d+)",
                    r"Version\s+(\d+\.\d+\.\d+)",
                    r'version\s*=\s*[\'"]([^"\']+)[\'"]',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        return f"v{matches[0]}"
            except Exception:
                continue

    return None
