#!/usr/bin/env python3
"""
OpenStudio-HPXML installer.

Handles installation and uninstallation of OpenStudio-HPXML.
"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import click

from .base import BaseInstaller
from ..download_utils import download_file


class HPXMLInstaller(BaseInstaller):
    """Installer for OpenStudio-HPXML."""

    HPXML_BASE_URL = "https://github.com/NREL/OpenStudio-HPXML/releases/download"

    def __init__(self, required_version, default_path, interactive=True, install_quiet=False):
        """Initialize HPXML installer.

        Args:
            required_version (str): Required HPXML version (e.g., "v1.9.1")
            default_path (Path): Default installation path
            interactive (bool): Whether to prompt user for input
            install_quiet (bool): Whether to suppress output
        """
        super().__init__(interactive, install_quiet)
        self.required_version = required_version
        self.default_path = Path(default_path)

    def install(self, target_path=None):
        """Install OpenStudio-HPXML by downloading and extracting zip file.

        Args:
            target_path (Path): Installation target directory (uses default if None)

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        if target_path is None:
            target_path = self.default_path

        download_url = (
            f"{self.HPXML_BASE_URL}/"
            f"{self.required_version}/"
            f"OpenStudio-HPXML-{self.required_version}.zip"
        )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "OpenStudio-HPXML.zip")

                # Download ZIP file
                if not download_file(download_url, zip_path, "OpenStudio-HPXML"):
                    raise Exception("Download failed")

                # Remove existing installation if present
                if target_path.exists():
                    click.echo(f"Removing existing installation: {target_path}")
                    self._remove_existing_installation(target_path)

                # Create parent directory
                self._create_target_directory(target_path)

                # Extract ZIP file
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

                click.echo(f"✅ OpenStudio-HPXML installed to: {target_path}")
                return True

        except Exception as e:
            click.echo(f"❌ OpenStudio-HPXML installation failed: {e}")
            return False

    def uninstall(self, install_path=None):
        """Uninstall OpenStudio-HPXML by removing the installation directory.

        Args:
            install_path (Path): Installation directory to remove (uses default if None)

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        try:
            # Use provided path or check environment variable
            if install_path is None:
                hpxml_path = os.environ.get("OPENSTUDIO_HPXML_PATH")
                if hpxml_path:
                    install_path = Path(hpxml_path)
                else:
                    install_path = self.default_path

            if not install_path.exists():
                click.echo("ℹ️  OpenStudio-HPXML not found or already uninstalled.")
                return True

            click.echo(f"Removing OpenStudio-HPXML from: {install_path}")

            # Remove directory with appropriate permissions
            if not self.is_windows:
                subprocess.run(["sudo", "rm", "-rf", str(install_path)], check=True)
            else:
                shutil.rmtree(install_path)

            click.echo("✅ OpenStudio-HPXML uninstalled successfully")
            return True

        except Exception as e:
            click.echo(f"❌ OpenStudio-HPXML uninstall failed: {e}")
            return False

    def validate(self):
        """Validate that OpenStudio-HPXML is properly installed.

        Returns:
            bool: True if installation is valid, False otherwise
        """
        if not self.default_path.exists():
            return False

        # Check for required workflow script
        workflow_script = self.default_path / "workflow" / "run_simulation.rb"
        return workflow_script.exists()

    def _remove_existing_installation(self, target_path):
        """Remove existing OpenStudio-HPXML installation.

        Args:
            target_path (Path): Path to remove
        """
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
        """Create target directory for installation.

        Args:
            target_path (Path): Directory to create
        """
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
        """Install OpenStudio-HPXML from source to target location.

        Args:
            source_folder (Path): Source directory containing extracted files
            target_path (Path): Target installation directory
        """
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
