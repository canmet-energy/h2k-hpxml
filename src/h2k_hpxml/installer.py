"""
Automatic dependency installer for h2k-hpxml package.

This module handles downloading and installing OpenStudio and OpenStudio-HPXML
dependencies into the package directory for consistent, versioned installations.
"""

import os
import platform
import shutil
import ssl
import sys
import tarfile
import time
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import tomllib


def _get_user_data_dir():
    """Get platform-appropriate user data directory for h2k_hpxml."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~/AppData/Roaming"))
        return Path(appdata) / "h2k_hpxml"
    else:
        # Linux/Unix: use XDG_DATA_HOME or ~/.local/share
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return Path(xdg_data) / "h2k_hpxml"


def _has_write_access(path):
    """Check if we have write access to a directory."""
    try:
        test_path = Path(path).resolve()  # Resolve to handle symlinks/relative paths
        max_depth = 10  # Maximum recursion depth to prevent infinite loops

        # Iterative approach to check parent directories
        current_path = test_path
        for _ in range(max_depth):
            if current_path.exists():
                return os.access(str(current_path), os.W_OK)

            parent_path = current_path.parent
            if parent_path == current_path:  # Reached root directory
                break
            current_path = parent_path

        # If we've exhausted max_depth, assume no access
        return False
    except (PermissionError, OSError):
        return False


def _get_deps_dir():
    """
    Get the directory for installing dependencies with smart fallback.

    Priority:
    1. H2K_DEPS_DIR environment variable (for Docker/CI)
    2. Package directory _deps if writable
    3. User data directory (~/.local/share/h2k_hpxml on Linux)
    """
    # 1. Check environment variable first (for Docker/CI)
    if os.environ.get("H2K_DEPS_DIR"):
        return Path(os.environ["H2K_DEPS_DIR"])

    # 2. Try package directory if writable
    package_deps = PACKAGE_DIR / "_deps"
    if _has_write_access(PACKAGE_DIR):
        return package_deps

    # 3. Fall back to user data directory
    user_deps = _get_user_data_dir() / "deps"
    return user_deps


# Package-relative paths
PACKAGE_DIR = Path(__file__).parent
# Get dependencies directory with smart fallback
DEPS_DIR = _get_deps_dir()
OPENSTUDIO_HPXML_DIR = DEPS_DIR / "OpenStudio-HPXML"
OPENSTUDIO_DIR = DEPS_DIR / "openstudio"


def get_dependency_versions():
    """Read dependency versions from pyproject.toml."""
    # Find pyproject.toml (go up from src/h2k_hpxml/installer.py to project root)
    pyproject_path = PACKAGE_DIR.parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {pyproject_path}. "
            "Dependency versions must be defined in [tool.h2k-hpxml.dependencies] section."
        )

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to parse pyproject.toml: {e}")

    dependencies = data.get("tool", {}).get("h2k-hpxml", {}).get("dependencies")
    if not dependencies:
        raise ValueError(
            "Missing [tool.h2k-hpxml.dependencies] section in pyproject.toml. "
            "Please add openstudio_version, openstudio_sha, and openstudio_hpxml_version."
        )

    # Validate required keys
    required_keys = ["openstudio_version", "openstudio_sha", "openstudio_hpxml_version"]
    missing_keys = [key for key in required_keys if key not in dependencies]
    if missing_keys:
        raise ValueError(
            f"Missing required dependency versions in pyproject.toml: {missing_keys}. "
            f"Required keys: {required_keys}"
        )

    return dependencies


def get_openstudio_hpxml_url():
    """Get OpenStudio-HPXML download URL with current version."""
    versions = get_dependency_versions()
    version = versions["openstudio_hpxml_version"]
    return f"https://github.com/NREL/OpenStudio-HPXML/releases/download/{version}/OpenStudio-HPXML-{version}.zip"


def get_openstudio_urls():
    """Get OpenStudio download URLs for all platforms with current version."""
    versions = get_dependency_versions()
    os_version = versions["openstudio_version"]
    os_sha = versions["openstudio_sha"]

    return {
        "Windows": f"https://github.com/NREL/OpenStudio/releases/download/v{os_version}/OpenStudio-{os_version}+{os_sha}-Windows.exe",
        "Linux": f"https://github.com/NREL/OpenStudio/releases/download/v{os_version}/OpenStudio-{os_version}+{os_sha}-Ubuntu-22.04-x86_64.tar.gz",
        "Darwin": f"https://github.com/NREL/OpenStudio/releases/download/v{os_version}/OpenStudio-{os_version}+{os_sha}-Darwin-x86_64.tar.gz",
    }


def get_deps_status():
    """Check if dependencies are installed."""
    return {
        "openstudio_hpxml": OPENSTUDIO_HPXML_DIR.exists(),
        "openstudio": OPENSTUDIO_DIR.exists(),
        "deps_dir": DEPS_DIR.exists(),
    }


def get_installation_info():
    """
    Get information about dependency installation locations.

    Returns:
        dict: Information about installation paths and status
    """
    info = {
        "deps_dir": str(DEPS_DIR),
        "deps_dir_type": "unknown",
        "openstudio_hpxml_path": str(OPENSTUDIO_HPXML_DIR),
        "openstudio_path": str(OPENSTUDIO_DIR),
        "writable": _has_write_access(DEPS_DIR.parent if not DEPS_DIR.exists() else DEPS_DIR),
        "status": get_deps_status(),
    }

    # Determine installation type
    if os.environ.get("H2K_DEPS_DIR"):
        info["deps_dir_type"] = "environment_variable"
        info["deps_dir_source"] = "H2K_DEPS_DIR"
    elif DEPS_DIR == PACKAGE_DIR / "_deps":
        info["deps_dir_type"] = "package_directory"
        info["deps_dir_source"] = "Package-local installation"
    else:
        info["deps_dir_type"] = "user_directory"
        info["deps_dir_source"] = "User home directory (package not writable)"

    return info


def download_file(url, dest_path, desc=""):
    """Download file with progress indicator."""
    print(f"Downloading {desc or url}...")

    # Create SSL context that doesn't verify certificates (for corporate networks)
    # In production, you might want to make this configurable
    import urllib.request

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:

        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100) if total_size > 0 else 0
            print(f"  Progress: {percent:.1f}%", end="\r")

        # Create opener with SSL context
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        urllib.request.install_opener(opener)

        urlretrieve(url, dest_path, reporthook=download_progress)
        print(f"\n  ✓ Downloaded to {dest_path}")
        return True
    except urllib.error.URLError as e:
        print(f"\n  ✗ Download failed: {e}")
        return False


def install_openstudio_hpxml(force=False):
    """Install OpenStudio-HPXML to package directory."""
    if OPENSTUDIO_HPXML_DIR.exists() and not force:
        print("OpenStudio-HPXML already installed")
        return True

    print("Installing OpenStudio-HPXML...")
    DEPS_DIR.mkdir(parents=True, exist_ok=True)

    # Download zip file
    versions = get_dependency_versions()
    hpxml_version = versions["openstudio_hpxml_version"]
    zip_path = DEPS_DIR / "OpenStudio-HPXML.zip"
    if not download_file(get_openstudio_hpxml_url(), zip_path, f"OpenStudio-HPXML {hpxml_version}"):
        return False

    # Extract
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(DEPS_DIR)

        # Handle nested directory structure (OpenStudio-HPXML/OpenStudio-HPXML)
        extracted_dir = DEPS_DIR / "OpenStudio-HPXML"
        nested_dir = extracted_dir / "OpenStudio-HPXML"

        if nested_dir.exists() and nested_dir.is_dir():
            # Move inner directory contents to expected location
            print("  ⚠ Detected nested structure, fixing...")
            temp_dir = DEPS_DIR / f"OpenStudio-HPXML_temp_{int(time.time())}"

            # Move nested content to temporary location
            shutil.move(str(nested_dir), str(temp_dir))

            # Remove empty parent directory
            if extracted_dir.exists():
                shutil.rmtree(str(extracted_dir))

            # Move temp directory to final location
            shutil.move(str(temp_dir), str(extracted_dir))
            print(f"  ✓ Fixed nested structure and extracted to {extracted_dir}")
        elif extracted_dir.exists():
            print(f"  ✓ Extracted to {extracted_dir}")
        else:
            # Check if extraction created different structure
            potential_dirs = [
                d for d in DEPS_DIR.iterdir() if d.is_dir() and "hpxml" in d.name.lower()
            ]
            if potential_dirs:
                actual_dir = potential_dirs[0]
                shutil.move(str(actual_dir), str(extracted_dir))
                print(f"  ✓ Moved {actual_dir.name} to {extracted_dir}")

        # Verify final structure
        workflow_file = extracted_dir / "workflow" / "run_simulation.rb"
        if not workflow_file.exists():
            raise RuntimeError(
                f"OpenStudio-HPXML extraction failed - missing workflow file at {workflow_file}"
            )

        # Clean up zip
        zip_path.unlink()
        return True

    except Exception as e:
        print(f"  ✗ Extraction failed: {e}")
        return False


def install_openstudio(force=False):
    """Install OpenStudio SDK to package directory."""
    if OPENSTUDIO_DIR.exists() and not force:
        print("OpenStudio already installed")
        return True

    system = platform.system()
    openstudio_urls = get_openstudio_urls()
    if system not in openstudio_urls:
        print(f"Unsupported platform: {system}")
        return False

    versions = get_dependency_versions()
    os_version = versions["openstudio_version"]
    print(f"Installing OpenStudio {os_version} for {system}...")
    DEPS_DIR.mkdir(parents=True, exist_ok=True)
    OPENSTUDIO_DIR.mkdir(parents=True, exist_ok=True)

    url = openstudio_urls[system]

    if system == "Windows":
        # Windows .exe installer - attempt automatic extraction
        exe_path = DEPS_DIR / "OpenStudio-installer.exe"
        print("  Note: Windows installer will be extracted automatically")
        if not download_file(url, exe_path, f"OpenStudio {os_version} for Windows"):
            return False

        print(f"  Extracting Windows installer to {OPENSTUDIO_DIR}...")

        # Try multiple extraction methods
        extraction_success = False

        # Method 1: Try using msiexec (requires admin rights but more reliable)
        try:
            import subprocess

            print("  Attempting extraction with msiexec...")
            result = subprocess.run(
                ["msiexec", "/a", str(exe_path), "/quiet", f"TARGETDIR={OPENSTUDIO_DIR}"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0 and OPENSTUDIO_DIR.exists():
                extraction_success = True
                print("  ✓ Extracted using msiexec")
        except Exception as e:
            print(f"  msiexec extraction failed: {e}")

        # Method 2: Try 7-zip if available
        if not extraction_success:
            try:
                import shutil

                seven_zip = shutil.which("7z")
                if seven_zip:
                    print("  Attempting extraction with 7-zip...")
                    result = subprocess.run(
                        [seven_zip, "x", str(exe_path), f"-o{OPENSTUDIO_DIR}", "-y"],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )

                    if result.returncode == 0 and OPENSTUDIO_DIR.exists():
                        extraction_success = True
                        print("  ✓ Extracted using 7-zip")
            except Exception as e:
                print(f"  7-zip extraction failed: {e}")

        # Method 3: Try Windows built-in expand command
        if not extraction_success:
            try:
                print("  Attempting extraction with expand command...")
                result = subprocess.run(
                    ["expand", str(exe_path), str(OPENSTUDIO_DIR)],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode == 0 and OPENSTUDIO_DIR.exists():
                    extraction_success = True
                    print("  ✓ Extracted using expand")
            except Exception as e:
                print(f"  expand extraction failed: {e}")

        # Clean up installer file
        try:
            exe_path.unlink()
        except Exception:
            pass

        if extraction_success:
            # Verify extraction worked by looking for expected files
            expected_files = [
                OPENSTUDIO_DIR / "bin" / "openstudio.exe",
                OPENSTUDIO_DIR / "lib" / "python",
            ]

            if any(f.exists() for f in expected_files):
                print(f"  ✓ Windows OpenStudio installed to {OPENSTUDIO_DIR}")
                return True
            else:
                print("  ⚠️  Extraction appeared successful but expected files not found")

        # If all automatic methods failed, provide instructions
        print("  ⚠️  Automatic extraction failed. Manual steps required:")
        print(f"  1. Right-click {exe_path} and 'Run as Administrator'")
        print(f'  2. Or use: msiexec /a "{exe_path}" /qb TARGETDIR="{OPENSTUDIO_DIR}"')
        print(f"  3. Or extract with 7-Zip to: {OPENSTUDIO_DIR}")
        print("  Then run 'h2k-deps' again to verify installation.")
        return False

    else:  # Linux/Mac - tar.gz files
        tar_path = DEPS_DIR / "openstudio.tar.gz"
        if not download_file(url, tar_path, f"OpenStudio {os_version} for {system}"):
            return False

        try:
            # Extract tar.gz
            print(f"  Extracting to {OPENSTUDIO_DIR}...")
            with tarfile.open(tar_path, "r:gz") as tar:
                # The tar contains OpenStudio-3.9.0+hash/ folder, extract contents
                tar.extractall(DEPS_DIR)

            # Find the extracted folder (it has a hash in the name)
            extracted_dirs = [
                d
                for d in DEPS_DIR.iterdir()
                if d.is_dir() and d.name.startswith(f"OpenStudio-{os_version}")
            ]

            if extracted_dirs:
                # Move contents to our standard location
                extracted_dir = extracted_dirs[0]
                print(f"  Moving from {extracted_dir.name} to openstudio/")

                # If OPENSTUDIO_DIR exists, remove it first
                if OPENSTUDIO_DIR.exists():
                    import shutil

                    shutil.rmtree(OPENSTUDIO_DIR)

                extracted_dir.rename(OPENSTUDIO_DIR)
                print(f"  ✓ Installed to {OPENSTUDIO_DIR}")
            else:
                print("  ⚠️  Could not find extracted OpenStudio directory")
                return False

            # Clean up
            tar_path.unlink()
            return True

        except Exception as e:
            print(f"  ✗ Extraction failed: {e}")
            return False


def _write_installation_marker_to_dir(target_dir):
    """Write a marker file to track this installation in a specific directory."""
    marker_file = target_dir / ".h2k_hpxml_installation"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(marker_file, "w") as f:
            import datetime
            import json

            data = {
                "package_dir": str(PACKAGE_DIR),
                "installed_at": datetime.datetime.now().isoformat(),
                "version": get_package_version(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "deps_version": get_dependency_versions(),  # Track dependency versions
            }
            json.dump(data, f, indent=2)
    except Exception:
        pass  # Silently fail - marker is optional


def _write_installation_marker():
    """Write a marker file to track this installation."""
    _write_installation_marker_to_dir(DEPS_DIR)


def _is_package_installed():
    """Check if h2k-hpxml package is actually installed using metadata."""
    try:
        from importlib.metadata import distribution

        dist = distribution("h2k-hpxml")
        return True
    except Exception:
        # Package not found in metadata, check for editable install
        try:
            import site

            # Look for .egg-link files indicating editable install
            for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
                if not site_dir:
                    continue
                egg_link = Path(site_dir) / "h2k-hpxml.egg-link"
                if egg_link.exists():
                    return True
        except Exception:
            pass
        return False


def _check_and_cleanup_orphaned_deps():
    """
    Check if dependencies are orphaned (package uninstalled) and clean them up.

    This is called on import to detect if the package that created the deps
    has been uninstalled, leaving orphaned dependencies.
    """
    # Only check user directory deps (not env var or package-local)
    if os.environ.get("H2K_DEPS_DIR"):
        return  # Skip if using environment variable

    user_deps = _get_user_data_dir() / "deps"
    if not user_deps.exists():
        return  # No user deps to check

    marker_file = user_deps / ".h2k_hpxml_installation"
    if not marker_file.exists():
        return  # No marker, can't determine if orphaned

    try:
        import json

        with open(marker_file) as f:
            data = json.load(f)

        # Check if the package is still installed using multiple methods
        package_installed = _is_package_installed()

        # Also check if the original package directory still exists (for editable installs)
        original_package = Path(data.get("package_dir", ""))
        directory_exists = original_package and original_package.exists()

        # Dependencies are orphaned if:
        # 1. Package not in metadata AND directory doesn't exist (regular uninstall)
        # 2. OR if marker says it was a non-editable install but package not in metadata
        is_orphaned = False

        if not package_installed and not directory_exists:
            is_orphaned = True
            cleanup_reason = "Package uninstalled and directory removed"
        elif not package_installed and directory_exists:
            # Could be editable install that was uninstalled but directory remains
            # Check if this is actually our current running package
            if str(original_package) != str(PACKAGE_DIR):
                is_orphaned = True
                cleanup_reason = "Package uninstalled (different installation)"

        if is_orphaned:
            print(f"Note: Cleaning up orphaned h2k-hpxml dependencies from {user_deps}")
            print(f"({cleanup_reason})")

            # Clean up orphaned dependencies
            import shutil

            shutil.rmtree(user_deps)

            # Remove parent directory if empty
            parent = user_deps.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()

            print("✓ Orphaned dependencies cleaned up")
            return

        # Check if dependencies need updating (version mismatch)
        installed_deps_version = data.get("deps_version", {})
        current_deps_version = get_dependency_versions()

        if installed_deps_version != current_deps_version:
            print("Note: Dependency versions have changed, updating...")
            print(f"  Installed: {installed_deps_version}")
            print(f"  Required: {current_deps_version}")

            # Remove old dependencies to force reinstall
            import shutil

            if (user_deps / "OpenStudio-HPXML").exists():
                shutil.rmtree(user_deps / "OpenStudio-HPXML")
            if (user_deps / "openstudio").exists():
                shutil.rmtree(user_deps / "openstudio")

            # Update marker with new versions in the correct location
            _write_installation_marker_to_dir(user_deps)

    except Exception:
        pass  # Silently fail - cleanup is optional


def get_package_version():
    """Get the current package version."""
    try:
        from importlib.metadata import version

        return version("h2k-hpxml")
    except Exception:
        try:
            from .. import __version__

            return __version__
        except Exception:
            return "unknown"


def ensure_dependencies(verbose=False):
    """
    Check and install missing dependencies.
    Called automatically on package import.

    Args:
        verbose: If True, print installation location information
    """
    # First check for orphaned dependencies from uninstalled packages
    _check_and_cleanup_orphaned_deps()

    status = get_deps_status()

    # Report installation location if verbose or if installing
    if verbose or not (status["openstudio_hpxml"] and status["openstudio"]):
        # Check if we're using a fallback location
        if not os.environ.get("H2K_DEPS_DIR") and not _has_write_access(PACKAGE_DIR):
            print(f"Note: Installing dependencies to user directory: {DEPS_DIR}")
            print("(Package directory is not writable)")

    # Ensure deps directory exists
    if not status["deps_dir"]:
        DEPS_DIR.mkdir(parents=True, exist_ok=True)
        _write_installation_marker()  # Track this installation

    # Only install if missing
    if not status["openstudio_hpxml"]:
        install_openstudio_hpxml()

    # Try to install OpenStudio if missing
    if not status["openstudio"]:
        print(f"OpenStudio SDK not found. Attempting to install to {OPENSTUDIO_DIR}...")
        if not install_openstudio():
            print("Note: OpenStudio SDK installation requires manual steps or 'h2k-deps' command.")


def get_openstudio_path():
    """Get path to OpenStudio executable - bundled or system."""
    system = platform.system()
    versions = get_dependency_versions()
    os_version = versions["openstudio_version"]

    # First check for bundled OpenStudio in _deps
    # The structure is different after extraction: usr/local/openstudio-{version}/bin/openstudio
    bundled_paths = [
        OPENSTUDIO_DIR / "usr" / "local" / f"openstudio-{os_version}" / "bin" / "openstudio",
        (
            OPENSTUDIO_DIR / "bin" / "openstudio.exe"
            if system == "Windows"
            else OPENSTUDIO_DIR / "bin" / "openstudio"
        ),
    ]

    for exe_path in bundled_paths:
        if exe_path.exists():
            return str(exe_path)

    # Fallback to system installation
    system_path = shutil.which("openstudio")
    if system_path:
        return system_path

    # No OpenStudio found
    return None


def get_openstudio_hpxml_path():
    """Get path to bundled OpenStudio-HPXML."""
    # After extraction, the actual path is nested
    actual_path = OPENSTUDIO_HPXML_DIR / "OpenStudio-HPXML"
    if actual_path.exists():
        return str(actual_path)
    elif OPENSTUDIO_HPXML_DIR.exists():
        return str(OPENSTUDIO_HPXML_DIR)
    return None


def get_openstudio_python_path():
    """Get path to OpenStudio Python bindings."""
    # Check bundled OpenStudio first
    bundled_py_path = OPENSTUDIO_DIR / "lib" / "python"
    if bundled_py_path.exists():
        return str(bundled_py_path)

    # Check if bindings are already available
    try:
        import openstudio

        return None  # Already in Python path
    except ImportError:
        pass

    # Check common system locations
    system = platform.system()
    if system == "Linux":
        paths = [
            Path("/usr/local/lib/python3.12/dist-packages/"),
            Path("/usr/local/lib/python3.12/site-packages/"),
        ]
    elif system == "Windows":
        paths = [
            Path("C:/openstudio-3.9.0/lib/python"),
        ]
    else:  # macOS
        paths = [
            Path("/usr/local/lib/python3.12/site-packages/"),
        ]

    for path in paths:
        if path.exists() and (path / "openstudio").exists():
            return str(path)

    return None


# Configuration helper
def get_default_config():
    """Get default configuration with bundled paths."""
    config = {
        "hpxml_os_path": get_openstudio_hpxml_path() or "",
        "openstudio_binary": get_openstudio_path() or "openstudio",
    }

    # Add Python path if needed
    py_path = get_openstudio_python_path()
    if py_path:
        config["openstudio_python_path"] = py_path

    return config


def clean_user_dependencies():
    """
    Remove user-installed dependencies.

    This function removes dependencies installed in the user directory.
    Use with caution - this will require re-downloading dependencies.

    Returns:
        bool: True if cleanup successful, False otherwise
    """
    user_deps = _get_user_data_dir() / "deps"

    if not user_deps.exists():
        print("No user dependencies directory found.")
        return True

    try:
        import shutil

        print(f"Removing user dependencies directory: {user_deps}")
        shutil.rmtree(user_deps)
        print("✓ User dependencies removed successfully")

        # Also check for the parent directory if it's empty
        parent = user_deps.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
            print(f"✓ Removed empty directory: {parent}")

        return True
    except Exception as e:
        print(f"✗ Failed to remove dependencies: {e}")
        return False


def get_deps_size():
    """
    Calculate the size of installed dependencies.

    Returns:
        int: Size in bytes, or 0 if not installed
    """
    total_size = 0

    def get_dir_size(path):
        size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    size += os.path.getsize(filepath)
                except OSError:
                    pass
        return size

    if DEPS_DIR.exists():
        total_size = get_dir_size(DEPS_DIR)

    return total_size


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        # Cleanup mode
        print("H2K-HPXML Dependency Cleanup")
        print("=" * 40)

        info = get_installation_info()
        print(f"Dependencies location: {info['deps_dir']}")
        print(f"Installation type: {info['deps_dir_type']}")

        if info["status"]["openstudio_hpxml"] or info["status"]["openstudio"]:
            size_mb = get_deps_size() / (1024 * 1024)
            print(f"Size: {size_mb:.1f} MB")

            # Check for --force flag
            if len(sys.argv) > 2 and sys.argv[2] == "--force":
                print("\nRemoving dependencies (--force flag used)...")
                clean_user_dependencies()
            else:
                try:
                    response = input("\nRemove these dependencies? (y/N): ")
                    if response.lower() == "y":
                        clean_user_dependencies()
                    else:
                        print("Cleanup cancelled.")
                except (EOFError, KeyboardInterrupt):
                    print("\nCleanup cancelled.")
        else:
            print("No dependencies installed.")
    else:
        # Manual installation
        print("Installing h2k-hpxml dependencies...")
        install_openstudio_hpxml(force=True)
        install_openstudio(force=True)
        print("\nInstallation complete!")
        print(f"OpenStudio-HPXML: {get_openstudio_hpxml_path()}")
        print(f"OpenStudio: {get_openstudio_path()}")
        print("\nTo remove dependencies later, run:")
        print("  python -m h2k_hpxml.installer --clean")
