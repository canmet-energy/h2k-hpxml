#!/usr/bin/env python3
"""
Platform-specific utilities for dependency management.

Handles platform detection, path resolution, and configuration loading.
"""

import json
import os
import platform
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for Python < 3.11
    except ImportError:
        tomllib = None


def load_dependency_config():
    """Load dependency configuration from packaged JSON file or pyproject.toml fallback.

    First tries to load from packaged dependency_versions.json file.
    Falls back to pyproject.toml for development environments.

    Returns:
        dict: Configuration dictionary with openstudio_version, openstudio_sha,
              openstudio_hpxml_version

    Raises:
        RuntimeError: If neither config source can be found or read, or if required
                     dependency configuration is missing.
    """
    # First try to load from packaged JSON file
    try:
        from importlib import resources

        # Try to load from package resources
        try:
            with resources.open_text('h2k_hpxml.resources', 'dependency_versions.json') as f:
                config = json.load(f)

                # Validate required fields
                required_fields = ["openstudio_version", "openstudio_sha", "openstudio_hpxml_version"]
                missing_fields = [field for field in required_fields if field not in config]

                if missing_fields:
                    raise RuntimeError(
                        f"Missing required dependency configuration in packaged config: {', '.join(missing_fields)}"
                    )

                return config

        except (FileNotFoundError, ImportError, AttributeError):
            # Package resources not available or file not found, try alternative approach
            pass

        # Try alternative resource loading for older Python versions
        try:
            import pkg_resources
            resource_path = pkg_resources.resource_filename('h2k_hpxml', 'resources/dependency_versions.json')
            if os.path.exists(resource_path):
                with open(resource_path, 'r') as f:
                    config = json.load(f)

                    # Validate required fields
                    required_fields = ["openstudio_version", "openstudio_sha", "openstudio_hpxml_version"]
                    missing_fields = [field for field in required_fields if field not in config]

                    if missing_fields:
                        raise RuntimeError(
                            f"Missing required dependency configuration in packaged config: {', '.join(missing_fields)}"
                        )

                    return config
        except (ImportError, FileNotFoundError):
            pass

    except Exception as e:
        # Log the error but continue to fallback
        pass

    # Fallback to pyproject.toml for development environments
    if tomllib is None:
        raise RuntimeError(
            "TOML library not available and packaged config not found. "
            "Install tomli for Python < 3.11: pip install tomli"
        )

    # Find pyproject.toml - walk up from this file to find project root
    current_path = Path(__file__).parent
    pyproject_path = None

    for _ in range(5):  # Look up to 5 levels up
        candidate = current_path / "pyproject.toml"
        if candidate.exists():
            pyproject_path = candidate
            break
        current_path = current_path.parent

    if pyproject_path is None:
        raise RuntimeError(
            "Could not find dependency configuration. Neither packaged dependency_versions.json "
            "nor pyproject.toml found. This may indicate a packaging issue."
        )

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to parse pyproject.toml: {e}")

    # Extract dependency configuration
    config = data.get("tool", {}).get("h2k-hpxml", {}).get("dependencies", {})

    if not config:
        raise RuntimeError(
            "Missing [tool.h2k-hpxml.dependencies] section in pyproject.toml. "
            "Required fields: openstudio_version, openstudio_sha, openstudio_hpxml_version"
        )

    # Validate required fields
    required_fields = ["openstudio_version", "openstudio_sha", "openstudio_hpxml_version"]
    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        raise RuntimeError(
            f"Missing required dependency configuration in pyproject.toml: {', '.join(missing_fields)}. "
            f"Add these to [tool.h2k-hpxml.dependencies] section."
        )

    return config


def get_user_data_dir():
    """Get platform-appropriate user data directory without external dependencies.

    Returns:
        Path: User data directory (LOCALAPPDATA on Windows, XDG_DATA_HOME on Linux)
    """
    if platform.system() == "Windows":
        # Use LOCALAPPDATA for consistency with OpenStudio CLI (not APPDATA/Roaming)
        localappdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local"))
        return Path(localappdata)
    else:
        # Linux/Unix: use XDG_DATA_HOME or ~/.local/share
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return Path(xdg_data)


def has_write_access(path):
    """Check if we have write access to a directory.

    Args:
        path (Path|str): Path to check

    Returns:
        bool: True if writable, False otherwise
    """
    try:
        test_path = Path(path)
        if not test_path.exists():
            # Check parent directory
            return (
                has_write_access(test_path.parent)
                if test_path.parent != test_path
                else False
            )
        return os.access(str(test_path), os.W_OK)
    except (PermissionError, OSError):
        return False


def get_windows_openstudio_paths(openstudio_version, build_hash):
    """Get Windows-specific OpenStudio paths with user-writable alternatives and portable installations.

    Args:
        openstudio_version (str): Required OpenStudio version (e.g., "3.9.0")
        build_hash (str): OpenStudio build hash (e.g., "bb29e94a73")

    Returns:
        list: List of potential OpenStudio binary paths
    """
    paths = []
    program_files_dirs = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
    ]

    # System-wide Program Files installations (MSI-based)
    for pf_dir in program_files_dirs:
        paths.extend(
            [
                os.path.join(pf_dir, "OpenStudio", "bin", "openstudio.exe"),
                os.path.join(
                    pf_dir,
                    f"OpenStudio {openstudio_version}",
                    "bin",
                    "openstudio.exe",
                ),
            ]
        )

    # System-wide C:\ installations
    paths.extend(
        [
            r"C:\openstudio\bin\openstudio.exe",
            f"C:\\openstudio-{openstudio_version}\\bin\\openstudio.exe",
        ]
    )

    # User-specific installations (both MSI and portable)
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    local_appdata = os.environ.get(
        "LOCALAPPDATA", os.path.join(user_profile, "AppData", "Local")
    )

    # Legacy user installations (MSI-based)
    paths.extend(
        [
            os.path.join(user_profile, "openstudio", "bin", "openstudio.exe"),
            os.path.join(local_appdata, "OpenStudio", "bin", "openstudio.exe"),
            os.path.join(
                local_appdata,
                f"OpenStudio-{openstudio_version}",
                "bin",
                "openstudio.exe",
            ),
        ]
    )

    # Portable installations (tar.gz based) - PRIORITY PATHS
    # These are checked first as they're the new preferred installation method
    portable_paths = [
        # Version-specific portable installation (our default location)
        os.path.join(
            local_appdata,
            f"OpenStudio-{openstudio_version}",
            "bin",
            "openstudio.exe",
        ),
        # Generic portable installation in LOCALAPPDATA
        os.path.join(local_appdata, "OpenStudio", "bin", "openstudio.exe"),
        # User profile installation
        os.path.join(user_profile, "OpenStudio", "bin", "openstudio.exe"),
        # h2k_hpxml managed installation
        os.path.join(str(get_user_data_dir()), "OpenStudio", "bin", "openstudio.exe"),
        # Alternative locations with build hash
        os.path.join(
            local_appdata,
            f"OpenStudio-{openstudio_version}+{build_hash}",
            "bin",
            "openstudio.exe",
        ),
    ]

    # Prioritize portable installations by putting them first
    return portable_paths + paths


def get_linux_openstudio_paths(openstudio_version):
    """Get Linux-specific OpenStudio paths with user-writable paths prioritized.

    Args:
        openstudio_version (str): Required OpenStudio version (e.g., "3.9.0")

    Returns:
        list: List of potential OpenStudio binary paths
    """
    paths = [
        # User installations FIRST (preferred for consistency)
        os.path.expanduser(f"~/.local/share/OpenStudio-{openstudio_version}/bin/openstudio"),
        os.path.expanduser("~/.local/bin/openstudio"),
        os.path.expanduser(f"~/.local/OpenStudio-{openstudio_version}/bin/openstudio"),

        # Legacy user paths
        os.path.expanduser("~/openstudio/bin/openstudio"),
        os.path.expanduser(f"~/openstudio-{openstudio_version}/bin/openstudio"),

        # System installations LAST (fallback for existing installs)
        "/usr/local/bin/openstudio",
        "/usr/bin/openstudio",
        f"/usr/local/openstudio-{openstudio_version}/bin/openstudio",
        "/opt/openstudio/bin/openstudio",
        f"/opt/openstudio-{openstudio_version}/bin/openstudio",
    ]

    return paths


def get_openstudio_paths(openstudio_version, build_hash, custom_path=None):
    """Get platform-specific OpenStudio installation paths.

    Supports environment variables for path customization:
    - OPENSTUDIO_PATH: Custom OpenStudio installation directory

    Args:
        openstudio_version (str): Required OpenStudio version
        build_hash (str): OpenStudio build hash
        custom_path (Path|str): Custom OpenStudio path hint (optional)

    Returns:
        list: List of potential OpenStudio binary paths
    """
    paths = []
    is_windows = platform.system() == "Windows"

    # 1. Check for custom path from caller
    if custom_path:
        custom_path = Path(custom_path)
        if is_windows:
            paths.append(str(custom_path / "bin" / "openstudio.exe"))
        else:
            paths.append(str(custom_path / "bin" / "openstudio"))

    # 2. Check environment variable
    env_path = os.environ.get("OPENSTUDIO_PATH")
    if env_path:
        env_path = Path(env_path)
        if is_windows:
            paths.append(str(env_path / "bin" / "openstudio.exe"))
        else:
            paths.append(str(env_path / "bin" / "openstudio"))

    # 3. Add platform-specific default paths
    if is_windows:
        paths.extend(get_windows_openstudio_paths(openstudio_version, build_hash))
    else:
        paths.extend(get_linux_openstudio_paths(openstudio_version))

    return paths


def get_default_hpxml_path(hpxml_version, custom_path=None):
    """Get platform-appropriate default OpenStudio-HPXML installation path.

    Supports environment variables and custom paths:
    1. Custom path provided by caller
    2. OPENSTUDIO_HPXML_PATH environment variable
    3. Platform-appropriate user directory with version

    Args:
        hpxml_version (str): Required HPXML version (e.g., "v1.9.1")
        custom_path (Path|str): Custom HPXML path (optional)

    Returns:
        Path: Default installation path for OpenStudio-HPXML
    """
    # 1. Use custom path if provided
    if custom_path:
        return Path(custom_path)

    # 2. Check OPENSTUDIO_HPXML_PATH environment variable
    env_path = os.environ.get("OPENSTUDIO_HPXML_PATH")
    if env_path:
        return Path(env_path)

    # 3. Use versioned user-writable locations (consistent with OpenStudio CLI pattern)
    return get_user_data_dir() / f"OpenStudio-HPXML-{hpxml_version}"


def get_default_openstudio_path(openstudio_version, custom_path=None):
    """Get platform-appropriate default OpenStudio installation path.

    Supports environment variables and custom paths:
    1. Custom path provided by caller
    2. OPENSTUDIO_PATH environment variable
    3. Platform-appropriate user directory with version

    Args:
        openstudio_version (str): Required OpenStudio version (e.g., "3.9.0")
        custom_path (Path|str): Custom OpenStudio path (optional)

    Returns:
        Path: Default installation path for OpenStudio
    """
    # 1. Use custom path if provided
    if custom_path:
        return Path(custom_path)

    # 2. Check OPENSTUDIO_PATH environment variable
    env_path = os.environ.get("OPENSTUDIO_PATH")
    if env_path:
        return Path(env_path)

    # 3. Use versioned user-writable locations (consistent with HPXML)
    return get_user_data_dir() / f"OpenStudio-{openstudio_version}"
