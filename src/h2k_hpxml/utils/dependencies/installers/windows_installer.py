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
                d
                for d in Path(extract_temp_dir).iterdir()
                if d.is_dir() and "OpenStudio" in d.name
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
            click.echo(
                "⚠️ OpenStudio binary test timed out, but installation appears successful"
            )
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
        """Offer to add OpenStudio to PATH.

        Args:
            install_dir (Path): Installation directory
        """
        scripts_dir = install_dir / "bin"

        if not self.interactive and not self.install_quiet:
            return

        click.echo("\n" + "=" * 60)
        click.echo("🪟 Windows PATH Setup")
        click.echo("=" * 60)
        click.echo("\nTo use OpenStudio from any terminal, you can add it to your PATH.")
        click.echo(f"\nOpenStudio Scripts Location: {scripts_dir}")

        if self.interactive:
            click.echo("\nWould you like to add OpenStudio to your PATH?")
            click.echo("Note: This will modify your user environment variables.")
            response = click.prompt("Add to PATH?", type=click.Choice(['y', 'n']), default='n')

            if response == 'y':
                self._add_to_path(scripts_dir)
        elif self.install_quiet:
            # In quiet mode, automatically add to PATH
            self._add_to_path(scripts_dir)

    def _add_to_path(self, scripts_dir):
        """Add directory to Windows PATH.

        Args:
            scripts_dir (Path): Directory to add to PATH
        """
        try:
            # This requires PowerShell
            cmd = f'[Environment]::SetEnvironmentVariable("Path", $env:Path + ";{scripts_dir}", "User")'
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                click.echo("✅ OpenStudio added to PATH")
                click.echo("⚠️  Please restart your terminal for changes to take effect")
            else:
                click.echo(f"⚠️  Failed to add to PATH: {result.stderr}")
                self._show_manual_path_instructions(scripts_dir)

        except Exception as e:
            click.echo(f"⚠️  Failed to modify PATH: {e}")
            self._show_manual_path_instructions(scripts_dir)

    def _show_manual_path_instructions(self, scripts_dir):
        """Show manual instructions for adding to PATH.

        Args:
            scripts_dir (Path): Directory to add to PATH
        """
        click.echo("\n" + "=" * 60)
        click.echo("Manual PATH Setup Instructions")
        click.echo("=" * 60)
        click.echo("\n1. Open System Properties (Win + Pause/Break)")
        click.echo("2. Click 'Advanced system settings'")
        click.echo("3. Click 'Environment Variables'")
        click.echo("4. Under 'User variables', select 'Path' and click 'Edit'")
        click.echo("5. Click 'New' and add:")
        click.echo(f"   {scripts_dir}")
        click.echo("6. Click 'OK' to save")
        click.echo("7. Restart your terminal")
        click.echo("=" * 60)
