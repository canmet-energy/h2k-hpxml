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

import os
import platform
import subprocess
import shutil
import tempfile
import zipfile
import urllib.request
import configparser
from pathlib import Path

import click
from packaging import version


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

    def __init__(self, interactive=True, skip_deps=False, auto_install=False):
        """
        Initialize dependency manager.
        
        Args:
            interactive (bool): Prompt user for installation choices.
                Default: True
            skip_deps (bool): Skip all dependency validation.
                Default: False  
            auto_install (bool): Automatically install missing dependencies
                without user prompts. Default: False
        """
        self.interactive = interactive
        self.skip_deps = skip_deps
        self.auto_install = auto_install
        
        # Platform detection
        system = platform.system().lower()
        self.is_windows = system == "windows"
        self.is_linux = system == "linux"

    @property
    def default_hpxml_path(self):
        """
        Get platform-appropriate default OpenStudio-HPXML installation path.
        
        Returns:
            Path: Default installation path for OpenStudio-HPXML
                - Windows: C:/OpenStudio-HPXML
                - Linux/Unix: /OpenStudio-HPXML
        """
        if self.is_windows:
            return Path("C:/OpenStudio-HPXML")
        return Path("/OpenStudio-HPXML")

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
                "❌ Dependencies not satisfied and running in "
                "non-interactive mode", 
                err=True
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
            
            if version.parse(installed_version) >= version.parse(
                self.REQUIRED_OPENSTUDIO_VERSION
            ):
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
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return False

    def _test_openstudio_command(self):
        """Test if 'openstudio' command works in PATH."""
        try:
            result = subprocess.run(
                ["openstudio", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return False

    def _get_openstudio_paths(self):
        """
        Get platform-specific OpenStudio installation paths.
        
        Returns:
            list: List of potential OpenStudio binary paths
        """
        if self.is_windows:
            return self._get_windows_paths()
        return self._get_linux_paths()

    def _get_windows_paths(self):
        """Get Windows-specific OpenStudio paths."""
        paths = []
        program_files_dirs = [
            os.environ.get('PROGRAMFILES', r'C:\Program Files'),
            os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)')
        ]
        
        for pf_dir in program_files_dirs:
            paths.extend([
                os.path.join(pf_dir, 'OpenStudio', 'bin', 'openstudio.exe'),
                os.path.join(
                    pf_dir,
                    f'OpenStudio {self.REQUIRED_OPENSTUDIO_VERSION}',
                    'bin',
                    'openstudio.exe'
                ),
            ])
        
        # Additional common paths
        paths.extend([
            r'C:\openstudio\bin\openstudio.exe',
            f'C:\\openstudio-{self.REQUIRED_OPENSTUDIO_VERSION}\\bin\\openstudio.exe',
        ])
        
        return paths

    def _get_linux_paths(self):
        """Get Linux-specific OpenStudio paths."""
        return [
            '/usr/local/bin/openstudio',
            '/usr/bin/openstudio',
            '/opt/openstudio/bin/openstudio',
            os.path.expanduser('~/openstudio/bin/openstudio'),
        ]

    def _check_openstudio_hpxml(self):
        """
        Check if OpenStudio-HPXML is installed.
        
        Returns:
            bool: True if OpenStudio-HPXML is available
        """
        # Check environment variable first
        hpxml_path = os.environ.get('OPENSTUDIO_HPXML_PATH')
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
            click.echo(
                f"❌ OpenStudio-HPXML workflow script missing: {workflow_script}"
            )
            return False
        
        # Try to detect version
        version_info = self._detect_hpxml_version(hpxml_path)
        if version_info:
            click.echo(
                f"✅ OpenStudio-HPXML: {version_info} at {hpxml_path}"
            )
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
                    content = file_path.read_text(encoding='utf-8')
                    # Look for version patterns
                    import re
                    patterns = [
                        r'v?(\d+\.\d+\.\d+)',
                        r'Version\s+(\d+\.\d+\.\d+)',
                        r'version\s*=\s*[\'"]([^"\']+)[\'"]'
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
                click.echo(
                    "⚠️  Continuing without all dependencies. "
                    "Errors may occur."
                )
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
            f"Download from: {self.OPENSTUDIO_BASE_URL}/"
            f"v{self.REQUIRED_OPENSTUDIO_VERSION}/"
        )
        
        if self.is_windows:
            click.echo("- Download: OpenStudio-*-Windows.exe")
            click.echo("- Run installer as administrator")
            click.echo("- Add to PATH if not automatically added")
        else:
            click.echo(
                "- Ubuntu/Debian: Download .deb package and run: "
                "sudo dpkg -i package.deb"
            )
            click.echo(
                "- Other Linux: Download .tar.gz and extract to "
                "/usr/local/openstudio"
            )

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
        """Install OpenStudio on Windows by opening browser to installer."""
        installer_url = (
            f"{self.OPENSTUDIO_BASE_URL}/"
            f"v{self.REQUIRED_OPENSTUDIO_VERSION}/"
            f"OpenStudio-{self.REQUIRED_OPENSTUDIO_VERSION}+"
            f"{self.OPENSTUDIO_BUILD_HASH}-Windows.exe"
        )
        
        click.echo(f"Windows OpenStudio installer: {installer_url}")
        click.echo(
            "\n⚠️  Automatic installation on Windows requires "
            "administrator privileges."
        )
        click.echo(
            "Please download and run the installer manually, "
            "or grant administrator access."
        )
        
        if click.confirm("Download installer automatically?"):
            try:
                import webbrowser
                webbrowser.open(installer_url)
                click.echo("✅ Installer download started in browser")
                click.echo("Please run the installer and restart this application.")
                return False
            except Exception as e:
                click.echo(f"❌ Failed to open browser: {e}")
                click.echo(f"Please manually download: {installer_url}")
                return False
        
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
        return (
            os.path.exists('/etc/debian_version') or
            shutil.which('apt-get') is not None
        )

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
            urllib.request.urlretrieve(deb_url, deb_path)
            
            click.echo("Installing OpenStudio (requires sudo)...")
            subprocess.run(['sudo', 'dpkg', '-i', deb_path], check=True)
            
            # Install dependencies if needed
            subprocess.run(
                ['sudo', 'apt-get', 'install', '-f', '-y'],
                check=False
            )
            
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
            urllib.request.urlretrieve(tarball_url, tarball_path)
            
            # Extract to /usr/local/openstudio
            install_dir = Path("/usr/local/openstudio")
            
            click.echo(f"Extracting to {install_dir} (requires sudo)...")
            subprocess.run(['sudo', 'mkdir', '-p', str(install_dir)], check=True)
            subprocess.run([
                'sudo', 'tar', '-xzf', tarball_path,
                '-C', str(install_dir), '--strip-components=1'
            ], check=True)
            
            # Create symlink to bin directory
            bin_link = Path("/usr/local/bin/openstudio")
            openstudio_bin = install_dir / "bin" / "openstudio"
            
            if openstudio_bin.exists():
                subprocess.run([
                    'sudo', 'ln', '-sf', str(openstudio_bin), str(bin_link)
                ], check=False)
            
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
                
                click.echo(f"Downloading from: {download_url}")
                urllib.request.urlretrieve(download_url, zip_path)
                
                # Extract to target location
                target_path = self.default_hpxml_path
                if target_path.exists():
                    click.echo(f"Removing existing installation: {target_path}")
                    if not self.is_windows:
                        subprocess.run(['sudo', 'rm', '-rf', str(target_path)], check=True)
                    else:
                        shutil.rmtree(target_path)
                
                # Create parent directory with sudo if needed
                if not self.is_windows:
                    subprocess.run(['sudo', 'mkdir', '-p', str(target_path.parent)], check=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Extract with temporary directory first
                extract_temp_dir = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_temp_dir, exist_ok=True)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_temp_dir)
                
                # Find the extracted OpenStudio-HPXML folder
                extracted_folders = [
                    d for d in Path(extract_temp_dir).iterdir()
                    if d.is_dir() and "OpenStudio-HPXML" in d.name
                ]
                
                if not extracted_folders:
                    raise Exception("No OpenStudio-HPXML folder found in extracted archive")
                
                source_folder = extracted_folders[0]
                
                # Move to final location with sudo if needed
                if not self.is_windows:
                    subprocess.run(['sudo', 'cp', '-r', str(source_folder), str(target_path)], check=True)
                    # Set read/write/execute permissions for ALL users (777 for directories, 666 for files)
                    subprocess.run(['sudo', 'find', str(target_path), '-type', 'd', '-exec', 'chmod', '777', '{}', '+'], check=True)
                    subprocess.run(['sudo', 'find', str(target_path), '-type', 'f', '-exec', 'chmod', '666', '{}', '+'], check=True)
                    # Make Ruby scripts executable for all users
                    subprocess.run(['sudo', 'find', str(target_path), '-name', '*.rb', '-exec', 'chmod', '777', '{}', '+'], check=True)
                else:
                    shutil.copytree(source_folder, target_path)
                
                # Update conversionconfig.ini with the installation path
                self._update_config_file(target_path)
                
                click.echo(
                    f"✅ OpenStudio-HPXML installed to: {target_path}"
                )
                return True
                
        except Exception as e:
            click.echo(f"❌ OpenStudio-HPXML installation failed: {e}")
            return False

    def _update_config_file(self, hpxml_path):
        """
        Update conversionconfig.ini with OpenStudio-HPXML installation path.
        
        Args:
            hpxml_path (Path): Path to OpenStudio-HPXML installation
        """
        # Find conversionconfig.ini file
        config_path = self._find_config_file()
        if not config_path:
            click.echo("⚠️  conversionconfig.ini not found, skipping config update")
            return False
        
        try:
            # Read current config
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Update hpxml_os_path
            if not config.has_section('paths'):
                config.add_section('paths')
            
            # Ensure path ends with / for consistency
            path_str = str(hpxml_path).replace('\\', '/') 
            if not path_str.endswith('/'):
                path_str += '/'
            
            config.set('paths', 'hpxml_os_path', path_str)
            
            # Write updated config
            with open(config_path, 'w') as config_file:
                config.write(config_file)
            
            click.echo(f"✅ Updated conversionconfig.ini: hpxml_os_path = {path_str}")
            return True
            
        except Exception as e:
            click.echo(f"⚠️  Failed to update conversionconfig.ini: {e}")
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
            config_file = parent / 'conversionconfig.ini'
            if config_file.exists():
                return str(config_file)
        
        # Also check common project locations
        common_locations = [
            Path(__file__).parent.parent.parent.parent / 'conversionconfig.ini',  # Project root
            Path('/workspaces/h2k_hpxml/conversionconfig.ini'),  # Codespace location
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
        
        click.echo(f"\nThe following will be uninstalled:")
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
        """Uninstall OpenStudio on Windows."""
        click.echo("🪟 Windows OpenStudio uninstall:")
        click.echo("   • Go to Windows Settings > Apps & Features")
        click.echo("   • Search for 'OpenStudio' and uninstall")
        click.echo("   • Or use Control Panel > Programs and Features")
        
        if self.interactive:
            click.echo("\n⏳ Please uninstall OpenStudio using Windows settings...")
            input("Press Enter when OpenStudio has been uninstalled...")
        
        # Check if still installed
        return not self._check_openstudio()

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
            result = subprocess.run(
                ['dpkg', '-l', '*openstudio*'], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0 or 'openstudio' not in result.stdout.lower():
                click.echo("ℹ️  No OpenStudio .deb packages found.")
                return True
            
            # Extract package names
            lines = result.stdout.split('\n')
            packages = []
            for line in lines:
                if 'ii' in line and 'openstudio' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append(parts[1])
            
            if not packages:
                click.echo("ℹ️  No installed OpenStudio packages found.")
                return True
            
            # Uninstall packages
            for package in packages:
                click.echo(f"Removing package: {package}")
                subprocess.run(['sudo', 'dpkg', '-r', package], check=True)
            
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
            Path("/usr/local/bin/openstudio")
        ]
        
        removed_any = False
        
        for path in install_paths:
            if path.exists():
                try:
                    if path.is_file():
                        subprocess.run(['sudo', 'rm', '-f', str(path)], check=True)
                        click.echo(f"Removed file: {path}")
                    else:
                        subprocess.run(['sudo', 'rm', '-rf', str(path)], check=True)
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
            hpxml_path = os.environ.get('OPENSTUDIO_HPXML_PATH')
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
                subprocess.run(['sudo', 'rm', '-rf', str(hpxml_path)], check=True)
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
            if not config.has_section('paths'):
                config.add_section('paths')
            
            config.set('paths', 'hpxml_os_path', '/path/to/OpenStudio-HPXML/')
            
            # Write updated config
            with open(config_path, 'w') as config_file:
                config.write(config_file)
            
            click.echo("✅ Updated conversionconfig.ini (set placeholder path)")
            
        except Exception as e:
            click.echo(f"⚠️  Failed to update conversionconfig.ini: {e}")


def validate_dependencies(interactive=True, skip_deps=False, check_only=False,
                         auto_install=False):
    """
    Convenience function to validate h2k_hpxml dependencies.
    
    Args:
        interactive (bool): Whether to prompt user for installation choices.
            Default: True
        skip_deps (bool): Skip all dependency validation. Default: False
        check_only (bool): Only check dependencies, don't install.
            Default: False
        auto_install (bool): Automatically install missing dependencies
            without prompts. Default: False
    
    Returns:
        bool: True if all dependencies are satisfied or successfully
            installed, False otherwise
    
    Example:
        >>> # Interactive validation with prompts
        >>> validate_dependencies()
        
        >>> # Automatic installation
        >>> validate_dependencies(auto_install=True)
        
        >>> # Check only, no installation
        >>> validate_dependencies(check_only=True)
    """
    manager = DependencyManager(
        interactive=interactive,
        skip_deps=skip_deps,
        auto_install=auto_install
    )
    
    if check_only:
        return manager.check_only()
    else:
        return manager.validate_all()


def main():
    """Main entry point for standalone dependency checking."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check and install h2k_hpxml dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check-only           # Only check dependencies
  %(prog)s --auto-install         # Automatically install missing deps  
  %(prog)s --uninstall            # Uninstall OpenStudio and OpenStudio-HPXML
  %(prog)s --non-interactive      # Don't prompt for installation
        """
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check dependencies, don't install"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Don't prompt for installation"
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency validation"
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Automatically install missing dependencies"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall OpenStudio and OpenStudio-HPXML dependencies"
    )
    
    args = parser.parse_args()
    
    # Handle uninstall option
    if args.uninstall:
        manager = DependencyManager(interactive=not args.non_interactive)
        success = manager.uninstall_dependencies()
    else:
        success = validate_dependencies(
            interactive=not args.non_interactive,
            skip_deps=args.skip_deps,
            check_only=args.check_only,
            auto_install=args.auto_install
        )
    
    import sys
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()