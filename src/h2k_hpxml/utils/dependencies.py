#!/usr/bin/env python3
"""
Dependency Manager for h2k_hpxml.

This module provides automated detection, validation, and installation
of required dependencies for the h2k_hpxml package:
- OpenStudio (version 3.9.0) with Python bindings
- OpenStudio-HPXML (version v1.9.1)

Supports both Windows and Linux platforms with automatic fallback
installation methods.

Example:
    Basic usage::

        from h2k_hpxml.utils.dependencies import validate_dependencies

        # Interactive validation with prompts
        validate_dependencies()

        # Automatic installation without prompts
        validate_dependencies(auto_install=True)

        # Check only, no installation
        validate_dependencies(check_only=True)

Author: h2k_hpxml development team
"""

# CRITICAL: Set this FIRST before any imports to prevent auto-install in __init__.py
import os
os.environ['H2K_SKIP_AUTO_INSTALL'] = '1'

import configparser
import platform
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import click
from packaging import version


# Download function with SSL context support
def download_file(url, dest_path, desc=""):
    """Download file with progress indicator."""
    print(f"Downloading {desc or url}...")

    # Create SSL context that doesn't verify certificates (for corporate networks)
    # In production, you might want to make this configurable
    import ssl
    import urllib.request
    from urllib.request import urlretrieve

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


def safe_echo(message, **kwargs):
    """Echo with Unicode character replacement for Windows compatibility."""
    if isinstance(message, str):
        # Replace common Unicode characters with ASCII equivalents
        replacements = {
            "✅": "[OK]",
            "✓": "[OK]",
            "❌": "[ERROR]",
            "✗": "[ERROR]",
            "⚠️": "[WARNING]",
            "⚠": "[WARNING]",
            "🔍": "[SEARCH]",
            "🔄": "[PROCESSING]",
            "📥": "[DOWNLOAD]",
            "🎉": "[SUCCESS]",
            "🏠": "[HOUSE]",
            "🔧": "[TOOL]",
            "📋": "[LIST]",
            "🗑️": "[DELETE]",
            "🪟": "[WINDOWS]",
            "⏳": "[WAIT]",
            "ℹ️": "[INFO]",
        }
        for unicode_char, ascii_equiv in replacements.items():
            message = message.replace(unicode_char, ascii_equiv)
    return click.echo(message, **kwargs)


# Configure click for Unicode support on Windows
if platform.system() == "Windows":
    import locale

    # Get the system's preferred encoding
    preferred_encoding = locale.getpreferredencoding()

    # If we're using a limited encoding, try to use UTF-8
    if preferred_encoding.lower() in ["cp1252", "windows-1252", "charmap"]:
        try:
            # Try to use UTF-8 for output
            import sys

            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            # Store original echo and replace with safe version
            if not hasattr(click, "original_echo"):
                click.original_echo = click.echo
                click.echo = safe_echo


class DependencyManager:
    """
    Manages detection, validation, and installation of h2k_hpxml dependencies.

    This class handles OpenStudio and OpenStudio-HPXML dependencies across
    Windows and Linux platforms, providing automated installation with
    appropriate fallback methods.

    Attributes:
        REQUIRED_OPENSTUDIO_VERSION (str): Required OpenStudio version
        REQUIRED_HPXML_VERSION (str): Required OpenStudio-HPXML version
        interactive (bool): Whether to prompt user for installation choices
        skip_deps (bool): Whether to skip all dependency validation
        auto_install (bool): Whether to automatically install missing deps
    """

    # Required dependency versions
    REQUIRED_OPENSTUDIO_VERSION = "3.9.0"
    REQUIRED_HPXML_VERSION = "v1.9.1"

    # GitHub release URLs
    OPENSTUDIO_BASE_URL = "https://github.com/NREL/OpenStudio/releases/download"
    HPXML_BASE_URL = "https://github.com/NREL/OpenStudio-HPXML/releases/download"

    # Build hash for OpenStudio 3.9.0 binaries
    OPENSTUDIO_BUILD_HASH = "c77fbb9569"

    def __init__(
        self,
        interactive=True,
        skip_deps=False,
        auto_install=False,
        hpxml_path=None,
        openstudio_path=None,
    ):
        """
        Initialize dependency manager with configurable paths.

        Args:
            interactive (bool): Prompt user for installation choices.
                Default: True
            skip_deps (bool): Skip all dependency validation.
                Default: False
            auto_install (bool): Automatically install missing dependencies
                without user prompts. Default: False
            hpxml_path (str|Path): Custom OpenStudio-HPXML installation path.
                Overrides environment variables and defaults. Default: None
            openstudio_path (str|Path): Custom OpenStudio installation path hint.
                Used for installation targeting. Default: None
        """
        self.interactive = interactive
        self.skip_deps = skip_deps
        self.auto_install = auto_install

        # Platform detection
        system = platform.system().lower()
        self.is_windows = system == "windows"
        self.is_linux = system == "linux"

        # Store custom paths
        self._custom_hpxml_path = Path(hpxml_path) if hpxml_path else None
        self._custom_openstudio_path = Path(openstudio_path) if openstudio_path else None

    def _get_user_data_dir(self):
        """Get platform-appropriate user data directory without external dependencies."""
        if self.is_windows:
            appdata = os.environ.get("APPDATA", os.path.expanduser("~/AppData/Roaming"))
            return Path(appdata) / "h2k_hpxml"
        else:
            # Linux/Unix: use XDG_DATA_HOME or ~/.local/share
            xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
            return Path(xdg_data) / "h2k_hpxml"

    def _has_write_access(self, path):
        """Check if we have write access to a directory."""
        try:
            test_path = Path(path)
            if not test_path.exists():
                # Check parent directory
                return (
                    self._has_write_access(test_path.parent)
                    if test_path.parent != test_path
                    else False
                )
            return os.access(str(test_path), os.W_OK)
        except (PermissionError, OSError):
            return False

    @property
    def default_hpxml_path(self):
        """
        Get platform-appropriate default OpenStudio-HPXML installation path.

        Supports environment variables and user-writable fallbacks:
        1. Custom path provided in constructor
        2. OPENSTUDIO_HPXML_PATH environment variable
        3. System default with user fallback if no write access

        Returns:
            Path: Default installation path for OpenStudio-HPXML
        """
        # 1. Use custom path if provided
        if self._custom_hpxml_path:
            return self._custom_hpxml_path

        # 2. Check environment variable
        env_path = os.environ.get("OPENSTUDIO_HPXML_PATH")
        if env_path:
            return Path(env_path)

        # 3. Use platform-appropriate defaults with user fallback
        if self.is_windows:
            system_path = Path("C:/OpenStudio-HPXML")
            user_path = self._get_user_data_dir() / "OpenStudio-HPXML"
        else:
            system_path = Path("/OpenStudio-HPXML")
            user_path = Path.home() / ".local" / "share" / "OpenStudio-HPXML"

        # Return system path if it exists and is readable, or if we have write access to create it
        if system_path.exists():
            if os.access(str(system_path), os.R_OK):
                return system_path
        elif self._has_write_access(system_path.parent):
            return system_path

        # Fallback to user-writable path
        return user_path

    def validate_all(self):
        """
        Validate all required dependencies.

        Checks for OpenStudio and OpenStudio-HPXML installations,
        handling missing dependencies based on configuration.

        Returns:
            bool: True if all dependencies are satisfied or successfully
                installed, False otherwise
        """
        if self.skip_deps:
            click.echo("Skipping dependency validation (--skip-deps)")
            return True

        click.echo("🔍 Checking dependencies...")

        openstudio_ok = self._check_openstudio()
        hpxml_ok = self._check_openstudio_hpxml()

        # Update config file with current dependency paths
        # (even if some dependencies are missing to reflect current state)
        self._update_config_file()

        if openstudio_ok and hpxml_ok:
            click.echo("✅ All dependencies satisfied!")
            return True

        # Handle missing dependencies
        if self.auto_install:
            return self._handle_auto_install(openstudio_ok, hpxml_ok)
        elif self.interactive:
            return self._handle_interactive_install(openstudio_ok, hpxml_ok)
        else:
            click.echo(
                "❌ Dependencies not satisfied and running in non-interactive mode", err=True
            )
            return False

    def check_only(self):
        """
        Check dependencies without installing anything.

        Returns:
            bool: True if all dependencies are satisfied, False otherwise
        """
        click.echo("🔍 Dependency Check Report")
        click.echo("=" * 30)

        openstudio_ok = self._check_openstudio()
        hpxml_ok = self._check_openstudio_hpxml()

        if openstudio_ok and hpxml_ok:
            click.echo("\n🎉 All dependencies satisfied!")
            return True

        # Report missing dependencies
        missing = []
        if not openstudio_ok:
            missing.append("OpenStudio")
        if not hpxml_ok:
            missing.append("OpenStudio-HPXML")

        click.echo(f"\n❌ Missing: {', '.join(missing)}")
        click.echo("Run with dependency installation to fix these issues.")
        return False

    def _check_openstudio(self):
        """
        Check if OpenStudio is installed with correct version.

        Checks both Python bindings and CLI binary availability.

        Returns:
            bool: True if OpenStudio is available with correct version
        """
        return self._check_python_bindings() and self._check_cli_binary()

    def _check_python_bindings(self):
        """Check OpenStudio Python bindings."""
        try:
            import openstudio

            installed_version = openstudio.openStudioVersion()

            if version.parse(installed_version) >= version.parse(self.REQUIRED_OPENSTUDIO_VERSION):
                click.echo(f"✅ OpenStudio Python bindings: v{installed_version}")
                return True

            click.echo(
                f"❌ OpenStudio Python bindings outdated: "
                f"v{installed_version} < v{self.REQUIRED_OPENSTUDIO_VERSION}"
            )
            return False

        except ImportError:
            click.echo("❌ OpenStudio Python bindings not found")
            return False
        except Exception as e:
            click.echo(f"❌ Error checking OpenStudio Python bindings: {e}")
            return False

    def _check_cli_binary(self):
        """Check OpenStudio CLI binary availability."""
        # Try common installation paths
        for openstudio_path in self._get_openstudio_paths():
            if self._test_binary_path(openstudio_path):
                click.echo(f"✅ OpenStudio CLI: {openstudio_path}")
                return True

        # Try openstudio command in PATH
        if self._test_openstudio_command():
            click.echo("✅ OpenStudio CLI found in PATH")
            return True

        click.echo("⚠️  OpenStudio CLI not found")
        return False

    def _test_binary_path(self, path):
        """Test if OpenStudio binary exists and runs."""
        if not os.path.exists(path):
            return False

        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return False

    def _test_openstudio_command(self):
        """Test if 'openstudio' command works in PATH."""
        try:
            result = subprocess.run(
                ["openstudio", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return False

    def _get_openstudio_paths(self):
        """
        Get platform-specific OpenStudio installation paths.

        Supports environment variables for path customization:
        - OPENSTUDIO_PATH: Custom OpenStudio installation directory

        Returns:
            list: List of potential OpenStudio binary paths
        """
        paths = []

        # 1. Check for custom path from constructor
        if self._custom_openstudio_path:
            if self.is_windows:
                paths.append(str(self._custom_openstudio_path / "bin" / "openstudio.exe"))
            else:
                paths.append(str(self._custom_openstudio_path / "bin" / "openstudio"))

        # 2. Check environment variable
        env_path = os.environ.get("OPENSTUDIO_PATH")
        if env_path:
            env_path = Path(env_path)
            if self.is_windows:
                paths.append(str(env_path / "bin" / "openstudio.exe"))
            else:
                paths.append(str(env_path / "bin" / "openstudio"))

        # 3. Add platform-specific default paths
        if self.is_windows:
            paths.extend(self._get_windows_paths())
        else:
            paths.extend(self._get_linux_paths())

        return paths

    def _get_windows_paths(self):
        """Get Windows-specific OpenStudio paths with user-writable alternatives and portable installations."""
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
                        f"OpenStudio {self.REQUIRED_OPENSTUDIO_VERSION}",
                        "bin",
                        "openstudio.exe",
                    ),
                ]
            )

        # System-wide C:\ installations
        paths.extend(
            [
                r"C:\openstudio\bin\openstudio.exe",
                f"C:\\openstudio-{self.REQUIRED_OPENSTUDIO_VERSION}\\bin\\openstudio.exe",
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
                    f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}",
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
                f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}",
                "bin",
                "openstudio.exe",
            ),
            # Generic portable installation in LOCALAPPDATA
            os.path.join(local_appdata, "OpenStudio", "bin", "openstudio.exe"),
            # User profile installation
            os.path.join(user_profile, "OpenStudio", "bin", "openstudio.exe"),
            # h2k_hpxml managed installation
            os.path.join(str(self._get_user_data_dir()), "OpenStudio", "bin", "openstudio.exe"),
            # Alternative locations with build hash
            os.path.join(
                local_appdata,
                f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}+{self.OPENSTUDIO_BUILD_HASH}",
                "bin",
                "openstudio.exe",
            ),
        ]

        # Prioritize portable installations by putting them first
        return portable_paths + paths

    def _get_linux_paths(self):
        """Get Linux-specific OpenStudio paths with user-writable alternatives."""
        paths = [
            # System-wide installations
            "/usr/local/bin/openstudio",
            "/usr/bin/openstudio",
            "/opt/openstudio/bin/openstudio",
            # User-specific installations
            os.path.expanduser("~/openstudio/bin/openstudio"),
            os.path.expanduser("~/.local/bin/openstudio"),
            os.path.expanduser("~/.local/openstudio/bin/openstudio"),
        ]

        # Add version-specific paths
        version = self.REQUIRED_OPENSTUDIO_VERSION
        paths.extend(
            [
                f"/usr/local/openstudio-{version}/bin/openstudio",
                f"/opt/openstudio-{version}/bin/openstudio",
                os.path.expanduser(f"~/openstudio-{version}/bin/openstudio"),
                os.path.expanduser(f"~/.local/openstudio-{version}/bin/openstudio"),
            ]
        )

        return paths

    def _check_openstudio_hpxml(self):
        """
        Check if OpenStudio-HPXML is installed.

        Returns:
            bool: True if OpenStudio-HPXML is available
        """
        # Check environment variable first
        hpxml_path = os.environ.get("OPENSTUDIO_HPXML_PATH")
        if hpxml_path:
            hpxml_path = Path(hpxml_path)
        else:
            hpxml_path = self.default_hpxml_path

        if not hpxml_path.exists():
            click.echo(f"❌ OpenStudio-HPXML not found at: {hpxml_path}")
            return False

        # Check for required workflow script
        workflow_script = hpxml_path / "workflow" / "run_simulation.rb"
        if not workflow_script.exists():
            click.echo(f"❌ OpenStudio-HPXML workflow script missing: {workflow_script}")
            return False

        # Try to detect version
        version_info = self._detect_hpxml_version(hpxml_path)
        if version_info:
            click.echo(f"✅ OpenStudio-HPXML: {version_info} at {hpxml_path}")
        else:
            click.echo(f"✅ OpenStudio-HPXML found at: {hpxml_path}")

        return True

    def _detect_hpxml_version(self, hpxml_path):
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
                    import re

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

    def _handle_auto_install(self, openstudio_ok, hpxml_ok):
        """Handle automatic installation of missing dependencies."""
        click.echo("🔄 Auto-installing missing dependencies...")

        success = True

        if not openstudio_ok:
            click.echo("\n📥 Installing OpenStudio...")
            if not self._install_openstudio():
                success = False

        if not hpxml_ok:
            click.echo("\n📥 Installing OpenStudio-HPXML...")
            if not self._install_openstudio_hpxml():
                success = False

        if success:
            click.echo("\n✅ All dependencies installed successfully!")
            # Re-validate to confirm installation
            return self._check_openstudio() and self._check_openstudio_hpxml()

        click.echo("\n❌ Some dependencies failed to install.")
        return False

    def _handle_interactive_install(self, openstudio_ok, hpxml_ok):
        """Handle interactive installation with user prompts."""
        missing = []
        if not openstudio_ok:
            missing.append("OpenStudio")
        if not hpxml_ok:
            missing.append("OpenStudio-HPXML")

        click.echo(f"\n❌ Missing dependencies: {', '.join(missing)}")
        click.echo("\nOptions:")
        click.echo("1. Automatically install missing dependencies")
        click.echo("2. Show manual installation instructions")
        click.echo("3. Continue without dependencies (may cause errors)")
        click.echo("4. Exit")

        while True:
            try:
                choice = click.prompt("Choose an option [1-4]", type=int)
            except click.Abort:
                click.echo("Installation cancelled.")
                return False

            if choice == 1:
                return self._handle_auto_install(openstudio_ok, hpxml_ok)
            elif choice == 2:
                self._show_manual_instructions(missing)
                return False
            elif choice == 3:
                click.echo("⚠️  Continuing without all dependencies. Errors may occur.")
                return True
            elif choice == 4:
                click.echo("Installation cancelled.")
                return False
            else:
                click.echo("Invalid choice. Please select 1-4.")

    def _show_manual_instructions(self, missing_deps):
        """Show manual installation instructions for missing dependencies."""
        click.echo("\n📋 Manual Installation Instructions")
        click.echo("=" * 50)

        if "OpenStudio" in missing_deps:
            self._show_openstudio_instructions()

        if "OpenStudio-HPXML" in missing_deps:
            self._show_hpxml_instructions()

    def _show_openstudio_instructions(self):
        """Show OpenStudio manual installation instructions."""
        click.echo(f"\n🔧 OpenStudio v{self.REQUIRED_OPENSTUDIO_VERSION}")
        click.echo(
            f"Download from: {self.OPENSTUDIO_BASE_URL}/v{self.REQUIRED_OPENSTUDIO_VERSION}/"
        )

        if self.is_windows:
            click.echo("- Download: OpenStudio-*-Windows.exe")
            click.echo("- Run installer as administrator")
            click.echo("- Add to PATH if not automatically added")
        else:
            click.echo("- Ubuntu/Debian: Download .deb package and run: sudo dpkg -i package.deb")
            click.echo("- Other Linux: Download .tar.gz and extract to /usr/local/openstudio")

    def _show_hpxml_instructions(self):
        """Show OpenStudio-HPXML manual installation instructions."""
        click.echo(f"\n🏠 OpenStudio-HPXML {self.REQUIRED_HPXML_VERSION}")
        click.echo(
            f"Download from: {self.HPXML_BASE_URL}/"
            f"{self.REQUIRED_HPXML_VERSION}/"
            f"OpenStudio-HPXML-{self.REQUIRED_HPXML_VERSION}.zip"
        )
        click.echo(f"- Extract to: {self.default_hpxml_path}")

        if self.is_windows:
            click.echo("- Ensure workflow\\run_simulation.rb exists")
        else:
            click.echo("- Ensure workflow/run_simulation.rb exists")

    def _install_openstudio(self):
        """
        Install OpenStudio automatically based on platform.

        Returns:
            bool: True if installation successful, False otherwise
        """
        try:
            if self.is_windows:
                return self._install_openstudio_windows()
            elif self.is_linux:
                return self._install_openstudio_linux()
            else:
                click.echo(f"❌ Unsupported platform: {platform.system()}")
                return False
        except Exception as e:
            click.echo(f"❌ OpenStudio installation failed: {e}")
            return False

    def _install_openstudio_windows(self):
        """Install OpenStudio on Windows using portable tar.gz (no admin rights required)."""
        tarball_url = (
            f"{self.OPENSTUDIO_BASE_URL}/"
            f"v{self.REQUIRED_OPENSTUDIO_VERSION}/"
            f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}+"
            f"{self.OPENSTUDIO_BUILD_HASH}-Windows.tar.gz"
        )

        # Default to user's local app data (no admin needed)
        default_install_dir = Path(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local"))
        )
        install_dir = default_install_dir / f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}"

        # Alternative locations if preferred
        if not self._has_write_access(default_install_dir):
            install_dir = (
                Path(os.environ.get("USERPROFILE", os.path.expanduser("~"))) / "OpenStudio"
            )
            if not self._has_write_access(install_dir.parent):
                install_dir = self._get_user_data_dir() / "OpenStudio"

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tarball_path = os.path.join(temp_dir, "openstudio.tar.gz")

                click.echo("Downloading OpenStudio portable version...")
                click.echo(f"URL: {tarball_url}")
                click.echo(f"Installing to: {install_dir}")

                # Use download_file function with SSL context for certificate issues
                if not download_file(tarball_url, tarball_path, "OpenStudio portable version"):
                    raise Exception("Download failed")

                # Remove existing installation if present
                if install_dir.exists():
                    click.echo(f"Removing existing installation: {install_dir}")
                    shutil.rmtree(install_dir)

                # Create installation directory
                install_dir.parent.mkdir(parents=True, exist_ok=True)

                # Extract tar.gz file
                click.echo("Extracting OpenStudio...")
                import tarfile

                with tarfile.open(tarball_path, "r:gz") as tar:
                    # Extract to a temporary location first to handle nested folder structure
                    extract_temp_dir = os.path.join(temp_dir, "extracted")
                    os.makedirs(extract_temp_dir, exist_ok=True)
                    tar.extractall(extract_temp_dir)

                    # Find the extracted OpenStudio folder (may have build hash in name)
                    extracted_folders = [
                        d
                        for d in Path(extract_temp_dir).iterdir()
                        if d.is_dir() and "OpenStudio" in d.name
                    ]

                    if not extracted_folders:
                        raise Exception("No OpenStudio folder found in extracted archive")

                    source_folder = extracted_folders[0]

                    # Move to final installation location
                    shutil.copytree(source_folder, install_dir)

                # Verify installation
                binary_path = install_dir / "bin" / "openstudio.exe"
                if not binary_path.exists():
                    raise Exception(f"OpenStudio binary not found at {binary_path}")

                # Test that the binary works
                try:
                    result = subprocess.run(
                        [str(binary_path), "--version"], capture_output=True, text=True, timeout=30
                    )
                    if result.returncode != 0:
                        raise Exception(f"OpenStudio binary test failed: {result.stderr}")
                    click.echo(f"✅ OpenStudio binary verified: {result.stdout.strip()}")
                except subprocess.TimeoutExpired:
                    click.echo(
                        "⚠️ OpenStudio binary test timed out, but installation appears successful"
                    )

                click.echo(f"✅ OpenStudio installed successfully to: {install_dir}")

                # Provide PATH instructions
                bin_path = install_dir / "bin"
                click.echo("\n📝 To add OpenStudio to your PATH (optional):")
                click.echo("   1. Open System Properties > Environment Variables")
                click.echo("   2. Edit the 'Path' variable for your user")
                click.echo(f"   3. Add: {bin_path}")
                click.echo("\n   Or run in PowerShell as Administrator:")
                click.echo(
                    f'   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";{bin_path}", [EnvironmentVariableTarget]::User)'
                )

                return True

        except Exception as e:
            click.echo(f"❌ OpenStudio installation failed: {e}")
            # Clean up partial installation
            if install_dir.exists():
                try:
                    shutil.rmtree(install_dir)
                    click.echo(f"🧹 Cleaned up partial installation at {install_dir}")
                except Exception as cleanup_error:
                    click.echo(f"⚠️ Failed to clean up {install_dir}: {cleanup_error}")
            return False

    def _install_openstudio_linux(self):
        """Install OpenStudio on Linux using appropriate package manager."""
        try:
            if self._is_debian_based():
                return self._install_openstudio_deb()
            else:
                return self._install_openstudio_tarball()
        except Exception as e:
            click.echo(f"❌ Linux OpenStudio installation failed: {e}")
            return False

    def _is_debian_based(self):
        """Check if running on Debian-based system."""
        return os.path.exists("/etc/debian_version") or shutil.which("apt-get") is not None

    def _install_openstudio_deb(self):
        """Install OpenStudio using .deb package."""
        deb_url = (
            f"{self.OPENSTUDIO_BASE_URL}/"
            f"v{self.REQUIRED_OPENSTUDIO_VERSION}/"
            f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}+"
            f"{self.OPENSTUDIO_BUILD_HASH}-Ubuntu-22.04-x86_64.deb"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            deb_path = os.path.join(temp_dir, "openstudio.deb")

            click.echo("Downloading OpenStudio .deb package...")
            # Use download_file function with SSL context for certificate issues
            if not download_file(deb_url, deb_path, "OpenStudio .deb package"):
                raise Exception("Download failed")

            click.echo("Installing OpenStudio (requires sudo)...")
            subprocess.run(["sudo", "dpkg", "-i", deb_path], check=True)

            # Install dependencies if needed
            subprocess.run(["sudo", "apt-get", "install", "-f", "-y"], check=False)

            click.echo("✅ OpenStudio installed successfully")
            return True

    def _install_openstudio_tarball(self):
        """Install OpenStudio from tarball."""
        tarball_url = (
            f"{self.OPENSTUDIO_BASE_URL}/"
            f"v{self.REQUIRED_OPENSTUDIO_VERSION}/"
            f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}+"
            f"{self.OPENSTUDIO_BUILD_HASH}-Ubuntu-22.04-x86_64.tar.gz"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            tarball_path = os.path.join(temp_dir, "openstudio.tar.gz")

            click.echo("Downloading OpenStudio tarball...")
            # Use download_file function with SSL context for certificate issues
            if not download_file(tarball_url, tarball_path, "OpenStudio tarball"):
                raise Exception("Download failed")

            # Extract to /usr/local/openstudio
            install_dir = Path("/usr/local/openstudio")

            click.echo(f"Extracting to {install_dir} (requires sudo)...")
            subprocess.run(["sudo", "mkdir", "-p", str(install_dir)], check=True)
            subprocess.run(
                [
                    "sudo",
                    "tar",
                    "-xzf",
                    tarball_path,
                    "-C",
                    str(install_dir),
                    "--strip-components=1",
                ],
                check=True,
            )

            # Create symlink to bin directory
            bin_link = Path("/usr/local/bin/openstudio")
            openstudio_bin = install_dir / "bin" / "openstudio"

            if openstudio_bin.exists():
                subprocess.run(
                    ["sudo", "ln", "-sf", str(openstudio_bin), str(bin_link)], check=False
                )

            click.echo("✅ OpenStudio installed successfully")
            return True

    def _install_openstudio_hpxml(self):
        """Install OpenStudio-HPXML by downloading and extracting zip file."""
        download_url = (
            f"{self.HPXML_BASE_URL}/"
            f"{self.REQUIRED_HPXML_VERSION}/"
            f"OpenStudio-HPXML-{self.REQUIRED_HPXML_VERSION}.zip"
        )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "OpenStudio-HPXML.zip")

                # Use download_file function with SSL context for certificate issues
                if not download_file(download_url, zip_path, "OpenStudio-HPXML"):
                    raise Exception("Download failed")

                # Extract to target location
                target_path = self.default_hpxml_path
                if target_path.exists():
                    click.echo(f"Removing existing installation: {target_path}")
                    self._remove_existing_installation(target_path)

                # Create parent directory
                self._create_target_directory(target_path)

                # Extract with temporary directory first
                extract_temp_dir = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_temp_dir, exist_ok=True)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_temp_dir)

                # Find the extracted OpenStudio-HPXML folder
                extracted_folders = [
                    d
                    for d in Path(extract_temp_dir).iterdir()
                    if d.is_dir() and "OpenStudio-HPXML" in d.name
                ]

                if not extracted_folders:
                    raise Exception("No OpenStudio-HPXML folder found in extracted archive")

                source_folder = extracted_folders[0]

                # Move to final location
                self._install_to_target(source_folder, target_path)

                # Update conversionconfig.ini with the installation path
                self._update_config_file(target_path)

                click.echo(f"✅ OpenStudio-HPXML installed to: {target_path}")
                return True

        except Exception as e:
            click.echo(f"❌ OpenStudio-HPXML installation failed: {e}")
            return False

    def _remove_existing_installation(self, target_path):
        """Remove existing OpenStudio-HPXML installation."""
        if not self.is_windows:
            # Try with sudo first, then fallback to regular removal
            try:
                subprocess.run(["sudo", "rm", "-rf", str(target_path)], check=True, timeout=30)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                try:
                    shutil.rmtree(target_path)
                except PermissionError:
                    click.echo(
                        f"⚠️  Could not remove {target_path}. Please remove manually or run with sudo."
                    )
                    raise
        else:
            shutil.rmtree(target_path)

    def _create_target_directory(self, target_path):
        """Create target directory for installation."""
        if not self.is_windows:
            # Try with sudo first, then fallback to user directory
            try:
                subprocess.run(
                    ["sudo", "mkdir", "-p", str(target_path.parent)], check=True, timeout=30
                )
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                # Fallback: create in user directory
                target_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)

    def _install_to_target(self, source_folder, target_path):
        """Install OpenStudio-HPXML from source to target location."""
        if not self.is_windows:
            # Try with sudo for system installation
            try:
                subprocess.run(
                    ["sudo", "cp", "-r", str(source_folder), str(target_path)],
                    check=True,
                    timeout=60,
                )
                # Set appropriate permissions
                subprocess.run(
                    [
                        "sudo",
                        "find",
                        str(target_path),
                        "-type",
                        "d",
                        "-exec",
                        "chmod",
                        "777",
                        "{}",
                        "+",
                    ],
                    check=True,
                    timeout=30,
                )
                subprocess.run(
                    [
                        "sudo",
                        "find",
                        str(target_path),
                        "-type",
                        "f",
                        "-exec",
                        "chmod",
                        "666",
                        "{}",
                        "+",
                    ],
                    check=True,
                    timeout=30,
                )
                subprocess.run(
                    [
                        "sudo",
                        "find",
                        str(target_path),
                        "-name",
                        "*.rb",
                        "-exec",
                        "chmod",
                        "777",
                        "{}",
                        "+",
                    ],
                    check=True,
                    timeout=30,
                )
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                # Fallback: user installation
                click.echo("⚠️  sudo installation failed, installing to user directory")
                shutil.copytree(source_folder, target_path)
                # Set user permissions
                for root, dirs, files in os.walk(target_path):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), 0o755)
                    for f in files:
                        file_path = os.path.join(root, f)
                        if f.endswith(".rb"):
                            os.chmod(file_path, 0o755)
                        else:
                            os.chmod(file_path, 0o644)
        else:
            shutil.copytree(source_folder, target_path)

    def setup_user_config(self):
        """
        Set up user configuration from template.

        Returns:
            bool: True if setup successful, False otherwise
        """
        from ..config.manager import ConfigManager

        click.echo("🔧 Setting up user configuration")

        # Create user config from template without interfering with project discovery
        try:
            # Create a temporary ConfigManager to get the user config path
            temp_config = ConfigManager(auto_create=False)
            user_config_path = temp_config._get_user_config_path()
            user_config_path.mkdir(parents=True, exist_ok=True)

            # Use single config filename
            user_config_file = user_config_path / "config.ini"

            # Find and copy template from project directory
            template_name = "conversionconfig.template.ini"
            template_path = temp_config._find_template_file(template_name)

            if template_path and template_path.exists():
                # Copy template to user config, preserving comments
                self._copy_template_with_path_updates(template_path, user_config_file)
                click.echo(f"✅ User configuration created from template at: {user_config_file}")
                click.echo(f"✅ Template source: {template_path.name}")
            else:
                # Create minimal config if no template found
                temp_config._create_minimal_config(user_config_file)
                click.echo(f"✅ User configuration created (minimal) at: {user_config_file}")
                # Update with detected dependency paths for minimal config
                self._update_user_config_file(user_config_file)
            return True

        except Exception as e:
            click.echo(f"❌ Failed to setup user configuration: {e}")
            return False

    def _copy_template_with_path_updates(self, template_path, user_config_file):
        """
        Copy template file to user config while preserving comments and updating paths.

        Args:
            template_path (Path): Source template file
            user_config_file (Path): Destination user config file
        """
        # Detect paths first
        openstudio_binary = self._detect_openstudio_binary()
        detected_hpxml_path = self._detect_hpxml_path(None)

        # Read template content
        template_content = template_path.read_text(encoding="utf-8")

        # Update paths in template content while preserving comments
        updated_content = template_content

        # Update OpenStudio-HPXML path
        if detected_hpxml_path:
            path_str = str(detected_hpxml_path).replace("\\", "/")
            if not path_str.endswith("/"):
                path_str += "/"
            updated_content = updated_content.replace(
                "hpxml_os_path = ", f"hpxml_os_path = {path_str}"
            )

        # Update OpenStudio binary path
        if openstudio_binary:
            updated_content = updated_content.replace(
                "openstudio_binary = ", f"openstudio_binary = {openstudio_binary}"
            )

        # Write updated content to user config file
        user_config_file.write_text(updated_content, encoding="utf-8")

        if detected_hpxml_path:
            click.echo(f"   Updated OpenStudio-HPXML path: {path_str}")
        if openstudio_binary:
            click.echo(f"   Updated OpenStudio binary path: {openstudio_binary}")

    def _update_config_file(self, hpxml_path=None, user_only=False):
        """
        Update configuration files with dependency installation paths.

        Args:
            hpxml_path (Path, optional): Path to OpenStudio-HPXML installation.
                                       If None, uses current default_hpxml_path
            user_only (bool): If True, only update user config files
        """
        if user_only:
            return self._update_user_configs_only(hpxml_path)
        else:
            return self._update_all_config_files(hpxml_path)

    def _update_user_configs_only(self, hpxml_path=None):
        """Update only user configuration files."""
        from ..config.manager import ConfigManager

        # Find user config files
        config_manager = ConfigManager(auto_create=False)
        user_config_dir = config_manager._get_user_config_path()

        if not user_config_dir.exists():
            click.echo("⚠️  No user configuration directory found")
            return False

        user_config_files = []
        for config_name in ["config.ini"]:
            config_file = user_config_dir / config_name
            if config_file.exists():
                user_config_files.append(str(config_file))

        if not user_config_files:
            click.echo("⚠️  No user configuration files found")
            return False

        # Detect and prepare paths
        openstudio_binary = self._detect_openstudio_binary()
        detected_hpxml_path = self._detect_hpxml_path(hpxml_path)

        updated_files = []
        failed_files = []

        # Update each user config file
        for config_path in user_config_files:
            try:
                success = self._update_single_config_file(
                    config_path, detected_hpxml_path, openstudio_binary
                )
                if success:
                    updated_files.append(config_path)
                else:
                    failed_files.append(config_path)
            except Exception as e:
                click.echo(f"⚠️  Failed to update {config_path}: {e}")
                failed_files.append(config_path)

        # Report results
        if updated_files:
            click.echo(f"✅ Updated {len(updated_files)} user configuration file(s):")
            for file_path in updated_files:
                click.echo(f"   • {file_path}")

        if failed_files:
            click.echo(f"⚠️  Failed to update {len(failed_files)} user configuration file(s):")
            for file_path in failed_files:
                click.echo(f"   • {file_path}")

        return len(updated_files) > 0

    def _update_all_config_files(self, hpxml_path=None):
        """Update all configuration files (project and user)."""
        # Find all configuration files
        config_files = self._find_all_config_files()
        if not config_files:
            click.echo("⚠️  No configuration files found, skipping config update")
            return False

        # Detect and prepare paths for all files
        openstudio_binary = self._detect_openstudio_binary()
        detected_hpxml_path = self._detect_hpxml_path(hpxml_path)

        updated_files = []
        failed_files = []

        # Update each configuration file
        for config_path in config_files:
            try:
                success = self._update_single_config_file(
                    config_path, detected_hpxml_path, openstudio_binary
                )
                if success:
                    updated_files.append(config_path)
                else:
                    failed_files.append(config_path)
            except Exception as e:
                click.echo(f"⚠️  Failed to update {config_path}: {e}")
                failed_files.append(config_path)

        # Report results
        if updated_files:
            click.echo(f"✅ Updated {len(updated_files)} configuration file(s):")
            for file_path in updated_files:
                click.echo(f"   • {file_path}")

        if failed_files:
            click.echo(f"⚠️  Failed to update {len(failed_files)} configuration file(s):")
            for file_path in failed_files:
                click.echo(f"   • {file_path}")

        return len(updated_files) > 0

    def _update_user_config_file(self, user_config_file):
        """Update a specific user config file with detected paths."""
        openstudio_binary = self._detect_openstudio_binary()
        detected_hpxml_path = self._detect_hpxml_path(None)

        success = self._update_single_config_file(
            str(user_config_file), detected_hpxml_path, openstudio_binary
        )
        if success:
            click.echo("✅ Updated user configuration with detected paths")
        else:
            click.echo("⚠️  Failed to update user configuration with paths")
        return success

    def _find_all_config_files(self):
        """
        Find all configuration files (main and environment-specific).

        Returns:
            list: List of paths to configuration files found
        """
        config_files = []

        # Start from current working directory and search upward
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            # Check for config directory
            config_dir = parent / "config"
            if config_dir.exists():
                # Look for all config files in config directory
                for config_name in ["conversionconfig.ini"]:
                    config_file = config_dir / config_name
                    if config_file.exists():
                        config_files.append(str(config_file))

            # Also check parent directory for legacy locations
            for config_name in ["conversionconfig.ini"]:
                config_file = parent / config_name
                if config_file.exists():
                    config_files.append(str(config_file))

        # Also check common project locations
        common_locations = [
            Path(__file__).parent.parent.parent.parent / "config",  # Project root/config
            Path("/workspaces/h2k_hpxml/config"),  # Codespace location
        ]

        for location in common_locations:
            if location.exists():
                for config_name in ["conversionconfig.ini"]:
                    config_file = location / config_name
                    if config_file.exists() and str(config_file) not in config_files:
                        config_files.append(str(config_file))

        return config_files

    def _detect_openstudio_binary(self):
        """Detect OpenStudio binary path."""
        openstudio_paths = self._get_openstudio_paths()
        for os_path in openstudio_paths:
            if Path(os_path).exists():
                return os_path
        return ""

    def _detect_hpxml_path(self, hpxml_path):
        """Detect OpenStudio-HPXML path."""
        if hpxml_path:
            return hpxml_path

        # Check environment variable first
        env_hpxml_path = os.environ.get("OPENSTUDIO_HPXML_PATH")
        if env_hpxml_path and Path(env_hpxml_path).exists():
            return Path(env_hpxml_path)

        # Check if default path exists
        default_path = self.default_hpxml_path
        if default_path.exists():
            # Verify it has the required workflow script
            workflow_script = default_path / "workflow" / "run_simulation.rb"
            if workflow_script.exists():
                return default_path

        return None

    def _update_single_config_file(self, config_path, detected_hpxml_path, openstudio_binary):
        """Update a single configuration file with detected paths."""
        try:
            # Read current config
            config = configparser.ConfigParser()
            config.read(config_path)

            # Ensure paths section exists
            if not config.has_section("paths"):
                config.add_section("paths")

            # Update OpenStudio-HPXML path
            if detected_hpxml_path:
                path_str = str(detected_hpxml_path).replace("\\", "/")
                if not path_str.endswith("/"):
                    path_str += "/"
                config.set("paths", "hpxml_os_path", path_str)
                click.echo(f"   Updated OpenStudio-HPXML path: {path_str}")
            else:
                click.echo("   ⚠️  OpenStudio-HPXML not found - keeping existing setting")

            # Update OpenStudio binary path
            if openstudio_binary:
                config.set("paths", "openstudio_binary", openstudio_binary)
                click.echo(f"   Updated OpenStudio binary path: {openstudio_binary}")
            else:
                # Clear the setting if not found
                config.set("paths", "openstudio_binary", "")
                click.echo("   ⚠️  OpenStudio binary not found - cleared setting")

            # Write updated config
            with open(config_path, "w") as config_file:
                config.write(config_file)

            return True

        except Exception as e:
            click.echo(f"   ⚠️  Error updating {config_path}: {e}")
            return False

    def _find_config_file(self):
        """
        Find conversionconfig.ini file by searching upward from current directory.

        Returns:
            str or None: Path to conversionconfig.ini if found, None otherwise
        """
        # Start from current working directory and search upward
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            config_file = parent / "conversionconfig.ini"
            if config_file.exists():
                return str(config_file)

        # Also check common project locations
        common_locations = [
            Path(__file__).parent.parent.parent.parent / "conversionconfig.ini",  # Project root
            Path("/workspaces/h2k_hpxml/conversionconfig.ini"),  # Codespace location
        ]

        for location in common_locations:
            if location.exists():
                return str(location)

        return None

    def uninstall_dependencies(self):
        """
        Uninstall OpenStudio and OpenStudio-HPXML dependencies.

        Returns:
            bool: True if uninstall completed successfully, False otherwise
        """
        click.echo("🗑️  Dependency Uninstaller")
        click.echo("=" * 30)

        # Check what's currently installed
        openstudio_installed = self._check_openstudio()
        hpxml_installed = self._check_openstudio_hpxml()

        if not openstudio_installed and not hpxml_installed:
            click.echo("ℹ️  No dependencies found to uninstall.")
            return True

        # Show what will be uninstalled
        to_uninstall = []
        if openstudio_installed:
            to_uninstall.append("OpenStudio (Python bindings and CLI)")
        if hpxml_installed:
            to_uninstall.append("OpenStudio-HPXML")

        click.echo("\nThe following will be uninstalled:")
        for item in to_uninstall:
            click.echo(f"  • {item}")

        # Safety confirmation
        if self.interactive:
            click.echo("\n⚠️  Warning: This will permanently remove the installed dependencies.")
            if not click.confirm("Do you want to continue?"):
                click.echo("Uninstall cancelled.")
                return False

        # Perform uninstall
        success = True

        if hpxml_installed:
            click.echo("\n🗑️  Uninstalling OpenStudio-HPXML...")
            if not self._uninstall_openstudio_hpxml():
                success = False

        if openstudio_installed:
            click.echo("\n🗑️  Uninstalling OpenStudio...")
            if not self._uninstall_openstudio():
                success = False

        if success:
            click.echo("\n✅ All dependencies uninstalled successfully!")
        else:
            click.echo("\n❌ Some dependencies failed to uninstall.")

        return success

    def _uninstall_openstudio(self):
        """
        Uninstall OpenStudio based on platform.

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        try:
            if self.is_windows:
                return self._uninstall_openstudio_windows()
            elif self.is_linux:
                return self._uninstall_openstudio_linux()
            else:
                click.echo(f"❌ Unsupported platform: {platform.system()}")
                return False
        except Exception as e:
            click.echo(f"❌ OpenStudio uninstall failed: {e}")
            return False

    def _uninstall_openstudio_windows(self):
        """Uninstall OpenStudio on Windows (both installer and portable versions)."""
        uninstalled_any = False

        # Check for portable installations first
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        local_appdata = os.environ.get(
            "LOCALAPPDATA", os.path.join(user_profile, "AppData", "Local")
        )

        portable_paths = [
            # Version-specific portable installation (our default location)
            Path(local_appdata) / f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}",
            # Generic portable installation in LOCALAPPDATA
            Path(local_appdata) / "OpenStudio",
            # User profile installation
            Path(user_profile) / "OpenStudio",
            # h2k_hpxml managed installation
            self._get_user_data_dir() / "OpenStudio",
            # Alternative locations with build hash
            Path(local_appdata)
            / f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}+{self.OPENSTUDIO_BUILD_HASH}",
        ]

        click.echo("🔍 Checking for portable OpenStudio installations...")

        for path in portable_paths:
            if path.exists():
                try:
                    # Verify it's actually an OpenStudio installation
                    binary_path = path / "bin" / "openstudio.exe"
                    if binary_path.exists():
                        click.echo(f"📁 Found portable installation: {path}")
                        shutil.rmtree(path)
                        click.echo(f"✅ Removed portable installation: {path}")
                        uninstalled_any = True
                    else:
                        click.echo(f"⏭️ Skipping {path} (not an OpenStudio installation)")
                except Exception as e:
                    click.echo(f"⚠️ Failed to remove {path}: {e}")

        if not uninstalled_any:
            click.echo("ℹ️ No portable OpenStudio installations found")

        # Check if there are still MSI installations present
        msi_found = False
        program_files_dirs = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        ]

        for pf_dir in program_files_dirs:
            msi_paths = [
                Path(pf_dir) / "OpenStudio",
                Path(pf_dir) / f"OpenStudio {self.REQUIRED_OPENSTUDIO_VERSION}",
            ]

            for msi_path in msi_paths:
                if msi_path.exists():
                    msi_found = True
                    break

            if msi_found:
                break

        # Show MSI uninstall instructions if MSI installations found
        if msi_found:
            click.echo("\n🪟 MSI-based OpenStudio installation detected:")
            click.echo("   To uninstall MSI installations:")
            click.echo("   • Go to Windows Settings > Apps & Features")
            click.echo("   • Search for 'OpenStudio' and uninstall")
            click.echo("   • Or use Control Panel > Programs and Features")

            if self.interactive:
                click.echo("\n⏳ Please uninstall MSI-based OpenStudio using Windows settings...")
                input("Press Enter when done (or if you want to keep the MSI installation)...")

        # Final check - see if OpenStudio is still detected
        still_installed = self._check_openstudio()

        if not still_installed:
            if uninstalled_any or msi_found:
                click.echo("✅ OpenStudio uninstallation completed successfully!")
            return True
        else:
            if uninstalled_any:
                click.echo(
                    "✅ Portable installations removed, but other OpenStudio installations remain"
                )
                return True
            else:
                click.echo("⚠️ OpenStudio is still detected. Manual removal may be required.")
                return False

    def _uninstall_openstudio_linux(self):
        """Uninstall OpenStudio on Linux."""
        try:
            if self._is_debian_based():
                return self._uninstall_openstudio_deb()
            else:
                return self._uninstall_openstudio_tarball()
        except Exception as e:
            click.echo(f"❌ Linux OpenStudio uninstall failed: {e}")
            return False

    def _uninstall_openstudio_deb(self):
        """Uninstall OpenStudio .deb package on Debian-based systems."""
        try:
            # Find OpenStudio packages
            result = subprocess.run(["dpkg", "-l", "*openstudio*"], capture_output=True, text=True)

            if result.returncode != 0 or "openstudio" not in result.stdout.lower():
                click.echo("ℹ️  No OpenStudio .deb packages found.")
                return True

            # Extract package names
            lines = result.stdout.split("\n")
            packages = []
            for line in lines:
                if "ii" in line and "openstudio" in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append(parts[1])

            if not packages:
                click.echo("ℹ️  No installed OpenStudio packages found.")
                return True

            # Uninstall packages
            for package in packages:
                click.echo(f"Removing package: {package}")
                subprocess.run(["sudo", "dpkg", "-r", package], check=True)

            click.echo("✅ OpenStudio .deb packages removed successfully")
            return True

        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Failed to remove OpenStudio packages: {e}")
            return False

    def _uninstall_openstudio_tarball(self):
        """Uninstall OpenStudio installed from tarball."""
        install_paths = [
            Path("/usr/local/openstudio"),
            Path("/opt/openstudio"),
            Path("/usr/local/bin/openstudio"),
        ]

        removed_any = False

        for path in install_paths:
            if path.exists():
                try:
                    if path.is_file():
                        subprocess.run(["sudo", "rm", "-f", str(path)], check=True)
                        click.echo(f"Removed file: {path}")
                    else:
                        subprocess.run(["sudo", "rm", "-rf", str(path)], check=True)
                        click.echo(f"Removed directory: {path}")
                    removed_any = True
                except subprocess.CalledProcessError:
                    click.echo(f"⚠️  Failed to remove: {path}")

        if removed_any:
            click.echo("✅ OpenStudio tarball installation removed")
        else:
            click.echo("ℹ️  No OpenStudio tarball installation found")

        return True

    def _uninstall_openstudio_hpxml(self):
        """
        Uninstall OpenStudio-HPXML by removing the installation directory.

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        try:
            # Check environment variable first
            hpxml_path = os.environ.get("OPENSTUDIO_HPXML_PATH")
            if hpxml_path:
                hpxml_path = Path(hpxml_path)
            else:
                hpxml_path = self.default_hpxml_path

            if not hpxml_path.exists():
                click.echo("ℹ️  OpenStudio-HPXML not found or already uninstalled.")
                return True

            click.echo(f"Removing OpenStudio-HPXML from: {hpxml_path}")

            # Remove directory with appropriate permissions
            if not self.is_windows:
                subprocess.run(["sudo", "rm", "-rf", str(hpxml_path)], check=True)
            else:
                shutil.rmtree(hpxml_path)

            # Update config file to remove the path
            self._update_config_file_uninstall()

            click.echo("✅ OpenStudio-HPXML uninstalled successfully")
            return True

        except Exception as e:
            click.echo(f"❌ OpenStudio-HPXML uninstall failed: {e}")
            return False

    def _update_config_file_uninstall(self):
        """Update conversionconfig.ini to set placeholder hpxml_os_path after uninstall."""
        config_path = self._find_config_file()
        if not config_path:
            return

        try:
            # Read current config
            config = configparser.ConfigParser()
            config.read(config_path)

            # Update hpxml_os_path to placeholder value
            if not config.has_section("paths"):
                config.add_section("paths")

            config.set("paths", "hpxml_os_path", "/path/to/OpenStudio-HPXML/")

            # Write updated config
            with open(config_path, "w") as config_file:
                config.write(config_file)

            click.echo("✅ Updated conversionconfig.ini (set placeholder path)")

        except Exception as e:
            click.echo(f"⚠️  Failed to update conversionconfig.ini: {e}")


def validate_dependencies(
    interactive=True,
    skip_deps=False,
    check_only=False,
    auto_install=False,
    hpxml_path=None,
    openstudio_path=None,
):
    """
    Convenience function to validate h2k_hpxml dependencies.

    Args:
        interactive (bool): Whether to prompt user for installation choices.
            Default: True
        skip_deps (bool): Skip all dependency validation. Default: False
        check_only (bool): Only check dependencies, don't install.
            Default: False
        auto_install (bool): Automatically install missing dependencies.
            Default: False
        hpxml_path (str|Path): Custom OpenStudio-HPXML installation path.
            Default: None (use environment variables or defaults)
        openstudio_path (str|Path): Custom OpenStudio installation path.
            Default: None (use environment variables or defaults)

    Returns:
        bool: True if all dependencies are satisfied or successfully
            installed, False otherwise

    Example:
        >>> # Interactive validation with prompts
        >>> validate_dependencies()

        >>> # Automatic installation with custom paths
        >>> validate_dependencies(auto_install=True, interactive=False, hpxml_path="/custom/hpxml")

        >>> # Check only, no installation
        >>> validate_dependencies(check_only=True)
    """
    manager = DependencyManager(
        interactive=interactive,
        skip_deps=skip_deps,
        auto_install=auto_install,
        hpxml_path=hpxml_path,
        openstudio_path=openstudio_path,
    )

    if check_only:
        return manager.check_only()
    else:
        return manager.validate_all()


def main():
    """Main entry point for standalone dependency checking."""
    import os
    # Prevent auto-install when running h2k-deps CLI
    os.environ['H2K_SKIP_AUTO_INSTALL'] = '1'
    
    import argparse

    parser = argparse.ArgumentParser(
        description="Check and install h2k_hpxml dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Check dependencies and prompt to install if missing
  %(prog)s --check-only           # Only check dependencies, don't install
  %(prog)s --install-quiet        # Install missing dependencies without prompts
  %(prog)s --setup                # Set up user configuration from template
  %(prog)s --update-config        # Update all config files with detected paths
  %(prog)s --update-config --global   # Update user config files only
  %(prog)s --uninstall            # Uninstall OpenStudio and OpenStudio-HPXML
        """,
    )

    parser.add_argument(
        "--check-only", action="store_true", help="Only check dependencies, don't install"
    )
    parser.add_argument(
        "--install-quiet", action="store_true", help="Install missing dependencies without prompts"
    )
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency validation")
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall OpenStudio and OpenStudio-HPXML dependencies",
    )
    parser.add_argument(
        "--setup", action="store_true", help="Set up user configuration from templates"
    )
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Update configuration file with detected dependency paths",
    )
    parser.add_argument(
        "--global",
        dest="update_global",
        action="store_true",
        help="Update user configuration files only (use with --update-config)",
    )
    parser.add_argument(
        "--local",
        dest="update_local",
        action="store_true",
        help="Update project configuration files only (use with --update-config)",
    )
    parser.add_argument(
        "--hpxml-path", type=str, metavar="PATH", help="Custom OpenStudio-HPXML installation path"
    )
    parser.add_argument(
        "--openstudio-path", type=str, metavar="PATH", help="Custom OpenStudio installation path"
    )

    args = parser.parse_args()

    # Handle setup option
    if args.setup:
        manager = DependencyManager(
            interactive=True,  # Setup is always interactive
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
        )
        success = manager.setup_user_config()
        if success:
            click.echo("✅ User configuration setup completed!")
        else:
            click.echo("❌ Failed to setup user configuration")
    # Handle uninstall option
    elif args.uninstall:
        manager = DependencyManager(
            interactive=True,  # Uninstall is always interactive for safety
            hpxml_path=args.hpxml_path,
            openstudio_path=args.openstudio_path,
        )
        success = manager.uninstall_dependencies()
    # Handle update-config option
    elif args.update_config:
        manager = DependencyManager(
            interactive=False, hpxml_path=args.hpxml_path, openstudio_path=args.openstudio_path
        )
        click.echo("🔄 Updating configuration with detected dependency paths...")

        # Determine update scope
        user_only = args.update_global and not args.update_local
        if args.update_global and args.update_local:
            click.echo("⚠️  Both --global and --local specified, updating all configs")
            user_only = False
        elif args.update_local:
            click.echo(
                "ℹ️  --local specified, but user config takes priority. Consider using --global for user configs."
            )
            user_only = False

        success = manager._update_config_file(user_only=user_only)
        if success:
            click.echo("✅ Configuration file updated successfully!")
        else:
            click.echo("❌ Failed to update configuration file")
    else:
        # Determine mode: check-only, install-quiet, or interactive (default)
        if args.check_only:
            success = validate_dependencies(
                check_only=True,
                hpxml_path=args.hpxml_path,
                openstudio_path=args.openstudio_path,
            )
        elif args.install_quiet:
            success = validate_dependencies(
                interactive=False,
                auto_install=True,
                skip_deps=args.skip_deps,
                hpxml_path=args.hpxml_path,
                openstudio_path=args.openstudio_path,
            )
        else:
            # Default interactive mode
            success = validate_dependencies(
                interactive=True,
                skip_deps=args.skip_deps,
                hpxml_path=args.hpxml_path,
                openstudio_path=args.openstudio_path,
            )

    import sys

    sys.exit(0 if success else 1)

# Compatibility functions for legacy installer.py imports
def get_openstudio_path():
    """Get path to OpenStudio executable - bundled or system."""
    import platform
    import shutil
    
    # Use DependencyManager to find OpenStudio
    manager = DependencyManager()
    paths = manager._get_openstudio_paths()
    
    # Check each potential path
    for path in paths:
        if Path(path).exists():
            return str(path)
    
    # Fallback to system installation
    system_path = shutil.which("openstudio")
    if system_path:
        return system_path
    
    # No OpenStudio found
    return None


def get_openstudio_hpxml_path():
    """Get path to OpenStudio-HPXML installation."""
    # Use DependencyManager to find HPXML path
    manager = DependencyManager()
    hpxml_path = manager.default_hpxml_path
    
    if hpxml_path.exists():
        return str(hpxml_path)
    
    return None


if __name__ == "__main__":
    main()
