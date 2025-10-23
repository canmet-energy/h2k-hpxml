#!/usr/bin/env python3
"""
OpenStudio Windows installer.

Handles Windows-specific installation using portable tar.gz (no admin rights required).
"""

import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import click

from .base import BaseInstaller
from ..download_utils import download_file
from ..platform_utils import get_user_data_dir, has_write_access


class WindowsInstaller(BaseInstaller):
    """Windows-specific OpenStudio installer using portable tar.gz."""

    OPENSTUDIO_BASE_URL = "https://github.com/NREL/OpenStudio/releases/download"

    def __init__(self, required_version, build_hash, interactive=True, install_quiet=False):
        """Initialize Windows installer.

        Args:
            required_version (str): Required OpenStudio version (e.g., "3.9.0")
            build_hash (str): OpenStudio build hash (e.g., "bb29e94a73")
            interactive (bool): Whether to prompt user for input
            install_quiet (bool): Whether to suppress output
        """
        super().__init__(interactive, install_quiet)
        self.required_version = required_version
        self.build_hash = build_hash

    def install(self, target_path=None):
        """Install OpenStudio using portable tar.gz (no admin rights required).

        Args:
            target_path (Path): Installation directory (auto-determined if None)

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        tarball_url = (
            f"{self.OPENSTUDIO_BASE_URL}/"
            f"v{self.required_version}/"
            f"OpenStudio-{self.required_version}+"
            f"{self.build_hash}-Windows.tar.gz"
        )

        # Determine installation directory
        install_dir = self._determine_install_dir(target_path)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tarball_path = os.path.join(temp_dir, "openstudio.tar.gz")

                click.echo("Downloading OpenStudio portable version...")
                click.echo(f"URL: {tarball_url}")
                click.echo(f"Installing to: {install_dir}")

                # Download tarball
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
                self._extract_tarball(tarball_path, temp_dir, install_dir)

                # Verify installation
                if not self._verify_installation(install_dir):
                    raise Exception("Installation verification failed")

                click.echo(f"✅ OpenStudio installed successfully to: {install_dir}")

                # Offer to add to PATH
                if self.interactive or self.install_quiet:
                    self._offer_path_setup(install_dir)

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

    def uninstall(self, install_path=None):
        """Uninstall OpenStudio from Windows.

        Args:
            install_path (Path): Installation directory to remove (auto-detected if None)

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        try:
            # Find installation directory
            if install_path is None:
                install_path = self._find_installation()

            if install_path is None or not install_path.exists():
                click.echo("ℹ️ OpenStudio not found or already uninstalled.")
                return True

            click.echo(f"Removing OpenStudio from: {install_path}")
            shutil.rmtree(install_path)
            click.echo("✅ OpenStudio uninstalled successfully")
            return True

        except Exception as e:
            click.echo(f"❌ OpenStudio uninstall failed: {e}")
            return False

    def validate(self):
        """Validate that OpenStudio is properly installed.

        Returns:
            bool: True if installation is valid, False otherwise
        """
        install_dir = self._find_installation()
        if install_dir is None:
            return False

        binary_path = install_dir / "bin" / "openstudio.exe"
        return binary_path.exists()

    def _determine_install_dir(self, target_path):
        """Determine the installation directory.

        Args:
            target_path (Path): Requested target path (None for auto-detect)

        Returns:
            Path: Installation directory
        """
        if target_path:
            return Path(target_path)

        # Default to user's local app data (no admin needed)
        default_install_dir = Path(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local"))
        )
        install_dir = default_install_dir / f"OpenStudio-{self.required_version}"

        # Alternative locations if preferred
        if not has_write_access(default_install_dir):
            install_dir = (
                Path(os.environ.get("USERPROFILE", os.path.expanduser("~"))) / "OpenStudio"
            )
            if not has_write_access(install_dir.parent):
                install_dir = get_user_data_dir() / "OpenStudio"

        return install_dir

    def _extract_tarball(self, tarball_path, temp_dir, install_dir):
        """Extract tarball to installation directory.

        Args:
            tarball_path (str): Path to tarball file
            temp_dir (str): Temporary directory for extraction
            install_dir (Path): Final installation directory
        """
        with tarfile.open(tarball_path, "r:gz") as tar:
            # Extract to a temporary location first to handle nested folder structure
            extract_temp_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_temp_dir, exist_ok=True)
            tar.extractall(extract_temp_dir)

            # Find the extracted OpenStudio folder (may have build hash in name)
            extracted_folders = [
                d for d in Path(extract_temp_dir).iterdir() if d.is_dir() and "OpenStudio" in d.name
            ]

            if not extracted_folders:
                raise Exception("No OpenStudio folder found in extracted archive")

            source_folder = extracted_folders[0]

            # Move to final installation location
            shutil.copytree(source_folder, install_dir)

    def _verify_installation(self, install_dir):
        """Verify that installation was successful.

        Args:
            install_dir (Path): Installation directory

        Returns:
            bool: True if verification passed, False otherwise
        """
        binary_path = install_dir / "bin" / "openstudio.exe"
        if not binary_path.exists():
            click.echo(f"❌ OpenStudio binary not found at {binary_path}")
            return False

        # Test that the binary works
        try:
            result = subprocess.run(
                [str(binary_path), "--version"], capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                click.echo(f"❌ OpenStudio binary test failed: {result.stderr}")
                return False
            click.echo(f"✅ OpenStudio binary verified: {result.stdout.strip()}")
            return True
        except subprocess.TimeoutExpired:
            click.echo("⚠️ OpenStudio binary test timed out, but installation appears successful")
            return True
        except Exception as e:
            click.echo(f"❌ OpenStudio binary test failed: {e}")
            return False

    def _find_installation(self):
        """Find existing OpenStudio installation.

        Returns:
            Path or None: Installation directory if found, None otherwise
        """
        # Check common installation locations
        possible_locations = [
            Path(os.environ.get("LOCALAPPDATA", "")) / f"OpenStudio-{self.required_version}",
            Path(os.environ.get("USERPROFILE", "")) / "OpenStudio",
            get_user_data_dir() / "OpenStudio",
        ]

        for location in possible_locations:
            if location.exists() and (location / "bin" / "openstudio.exe").exists():
                return location

        return None

    def _offer_path_setup(self, install_dir):
        """Offer to configure OpenStudio environment variables.

        Args:
            install_dir (Path): Installation directory
        """
        scripts_dir = install_dir / "bin"

        if not self.interactive and not self.install_quiet:
            return

        click.echo("\n" + "=" * 60)
        click.echo("🪟 Windows Environment Setup")
        click.echo("=" * 60)
        click.echo(
            "\nTo use OpenStudio from any terminal, environment variables need to be configured."
        )
        click.echo(f"\nOpenStudio Location: {install_dir}")

        if self.interactive:
            click.echo("\nWould you like to configure OpenStudio environment variables?")
            click.echo("Note: This will modify your user environment variables.")
            click.echo("Variables to set: PATH, RUBYLIB, ENERGYPLUS_EXE_PATH")
            response = click.prompt(
                "Configure environment?", type=click.Choice(["y", "n"]), default="n"
            )

            if response == "y":
                self._configure_environment(install_dir)
        elif self.install_quiet:
            # In quiet mode, automatically configure environment
            self._configure_environment(install_dir)

    def _configure_environment(self, install_dir):
        """Configure Windows environment variables for OpenStudio.

        Sets PATH, RUBYLIB, and ENERGYPLUS_EXE_PATH.

        Args:
            install_dir (Path): Installation directory
        """
        scripts_dir = install_dir / "bin"
        ruby_dir = install_dir / "Ruby"
        energyplus_dir = install_dir / "EnergyPlus"

        success = True

        # Set PATH
        if not self._set_env_var("Path", f"$env:Path + ';{scripts_dir}'"):
            success = False

        # Set RUBYLIB
        if not self._set_env_var("RUBYLIB", f"'{ruby_dir}'"):
            success = False

        # Set ENERGYPLUS_EXE_PATH
        if not self._set_env_var("ENERGYPLUS_EXE_PATH", f"'{energyplus_dir}'"):
            success = False

        if success:
            click.echo("\n✅ Environment variables configured successfully")
            click.echo("⚠️  Please restart your terminal for changes to take effect")
            click.echo("\n📋 Variables set:")
            click.echo(f"   • PATH (includes {scripts_dir})")
            click.echo(f"   • RUBYLIB = {ruby_dir}")
            click.echo(f"   • ENERGYPLUS_EXE_PATH = {energyplus_dir}")
        else:
            self._show_manual_env_instructions(install_dir)

    def _set_env_var(self, var_name, var_value):
        """Set a Windows user environment variable using PowerShell.

        Args:
            var_name (str): Environment variable name
            var_value (str): PowerShell expression for the value

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cmd = f'[Environment]::SetEnvironmentVariable("{var_name}", {var_value}, "User")'
            result = subprocess.run(
                ["powershell", "-Command", cmd], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                click.echo(f"✅ {var_name} configured")
                return True
            else:
                click.echo(f"⚠️  Failed to set {var_name}: {result.stderr}")
                return False

        except Exception as e:
            click.echo(f"⚠️  Failed to set {var_name}: {e}")
            return False

    def _show_manual_env_instructions(self, install_dir):
        """Show manual instructions for configuring environment variables.

        Args:
            install_dir (Path): Installation directory
        """
        scripts_dir = install_dir / "bin"
        ruby_dir = install_dir / "Ruby"
        energyplus_dir = install_dir / "EnergyPlus"

        click.echo("\n" + "=" * 70)
        click.echo("Manual Environment Variables Setup Instructions")
        click.echo("=" * 70)
        click.echo("\n1. Open System Properties (Win + Pause/Break)")
        click.echo("2. Click 'Advanced system settings'")
        click.echo("3. Click 'Environment Variables'")
        click.echo("\n4. Configure PATH:")
        click.echo("   - Under 'User variables', select 'Path' and click 'Edit'")
        click.echo("   - Click 'New' and add:")
        click.echo(f"     {scripts_dir}")
        click.echo("\n5. Add RUBYLIB:")
        click.echo("   - Click 'New' under 'User variables'")
        click.echo("   - Variable name: RUBYLIB")
        click.echo(f"   - Variable value: {ruby_dir}")
        click.echo("\n6. Add ENERGYPLUS_EXE_PATH:")
        click.echo("   - Click 'New' under 'User variables'")
        click.echo("   - Variable name: ENERGYPLUS_EXE_PATH")
        click.echo(f"   - Variable value: {energyplus_dir}")
        click.echo("\n7. Click 'OK' to save all changes")
        click.echo("8. Restart your terminal")
        click.echo("=" * 70)
