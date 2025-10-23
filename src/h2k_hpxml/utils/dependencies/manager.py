#!/usr/bin/env python3
"""
Dependency Manager for h2k_hpxml.

Manages detection, validation, and installation of OpenStudio and OpenStudio-HPXML.
"""

# CRITICAL: Set this FIRST before any imports to prevent auto-install
import os

os.environ["H2K_SKIP_AUTO_INSTALL"] = "1"

import configparser
import platform
from pathlib import Path

import click

# Import from our modular structure
from .download_utils import download_file
from .platform_utils import (
    load_dependency_config,
    get_user_data_dir,
    get_openstudio_paths,
    get_default_hpxml_path,
    get_default_openstudio_path,
)
from .validators import (
    check_openstudio,
    check_openstudio_hpxml,
)
from .installers.windows_installer import WindowsInstaller
from .installers.linux_installer import LinuxInstaller
from .installers.hpxml_installer import HPXMLInstaller


class DependencyManager:
    """
    Manages detection, validation, and installation of h2k_hpxml dependencies.

    This class handles OpenStudio and OpenStudio-HPXML dependencies across
    Windows and Linux platforms, providing automated installation with
    appropriate fallback methods.

    Attributes:
        REQUIRED_OPENSTUDIO_VERSION (str): Required OpenStudio version (loaded from pyproject.toml)
        REQUIRED_HPXML_VERSION (str): Required OpenStudio-HPXML version (loaded from pyproject.toml)
        OPENSTUDIO_BUILD_HASH (str): OpenStudio build hash (loaded from pyproject.toml)
        interactive (bool): Whether to prompt user for installation choices
        skip_deps (bool): Whether to skip all dependency validation
        install_quiet (bool): Whether to automatically install missing deps
    """

    # GitHub release URLs
    OPENSTUDIO_BASE_URL = "https://github.com/NREL/OpenStudio/releases/download"
    HPXML_BASE_URL = "https://github.com/NREL/OpenStudio-HPXML/releases/download"

    def __init__(
        self,
        interactive=True,
        skip_deps=False,
        install_quiet=False,
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
            install_quiet (bool): Automatically install missing dependencies
                without user prompts. Default: False
            hpxml_path (str|Path): Custom OpenStudio-HPXML installation path.
                Overrides environment variables and defaults. Default: None
            openstudio_path (str|Path): Custom OpenStudio installation path hint.
                Used for installation targeting. Default: None
        """
        self.interactive = interactive
        self.skip_deps = skip_deps
        self.install_quiet = install_quiet

        # Load dependency configuration from pyproject.toml
        self._config = load_dependency_config()
        self.REQUIRED_OPENSTUDIO_VERSION = self._config["openstudio_version"]
        self.REQUIRED_HPXML_VERSION = self._config["openstudio_hpxml_version"]
        self.OPENSTUDIO_BUILD_HASH = self._config["openstudio_sha"]

        # Platform detection
        system = platform.system().lower()
        self.is_windows = system == "windows"
        self.is_linux = system == "linux"

        # Store custom paths
        self._custom_hpxml_path = Path(hpxml_path) if hpxml_path else None
        self._custom_openstudio_path = Path(openstudio_path) if openstudio_path else None

    @property
    def default_hpxml_path(self):
        """
        Get platform-appropriate default OpenStudio-HPXML installation path.

        Supports environment variables and custom paths:
        1. Custom path provided in constructor
        2. OPENSTUDIO_HPXML_PATH environment variable
        3. Platform-appropriate user directory with version

        Returns:
            Path: Default installation path for OpenStudio-HPXML
        """
        # 1. Use custom path if provided
        if self._custom_hpxml_path:
            return self._custom_hpxml_path

        # 2. Check OPENSTUDIO_HPXML_PATH environment variable
        env_path = os.environ.get("OPENSTUDIO_HPXML_PATH")
        if env_path:
            return Path(env_path)

        # 3. Use platform_utils helper
        return get_default_hpxml_path(self.REQUIRED_HPXML_VERSION, None)

    @property
    def default_openstudio_path(self):
        """
        Get platform-appropriate default OpenStudio installation path.

        Supports environment variables and custom paths:
        1. Custom path provided in constructor
        2. OPENSTUDIO_PATH environment variable
        3. Platform-appropriate user directory with version

        Returns:
            Path: Default installation path for OpenStudio
        """
        # 1. Use custom path if provided
        if self._custom_openstudio_path:
            return self._custom_openstudio_path

        # 2. Check OPENSTUDIO_PATH environment variable
        env_path = os.environ.get("OPENSTUDIO_PATH")
        if env_path:
            return Path(env_path)

        # 3. Use platform_utils helper
        return get_default_openstudio_path(self.REQUIRED_OPENSTUDIO_VERSION, None)

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

        openstudio_ok = check_openstudio(self)
        hpxml_ok = check_openstudio_hpxml(self)

        if openstudio_ok and hpxml_ok:
            click.echo("✅ All dependencies satisfied!")
            return True

        # Handle missing dependencies
        if self.install_quiet:
            return self._handle_install_quiet(openstudio_ok, hpxml_ok)
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

        openstudio_ok = check_openstudio(self)
        hpxml_ok = check_openstudio_hpxml(self)

        if openstudio_ok and hpxml_ok:
            click.echo("\n🎉 All dependencies satisfied!")
            return True

        # Report missing dependencies
        missing = []
        if not openstudio_ok:
            missing.append("OpenStudio CLI")
        if not hpxml_ok:
            missing.append("OpenStudio-HPXML")

        click.echo(f"\n❌ Missing: {', '.join(missing)}")
        click.echo("Run with dependency installation to fix these issues.")
        return False

    def install_dependencies(self):
        """
        Install all missing dependencies.

        Returns:
            bool: True if all installations succeeded, False otherwise
        """
        click.echo("📦 Dependency Installer")
        click.echo("=" * 30)

        success = True

        # Check what's currently installed
        openstudio_ok = check_openstudio(self)
        hpxml_ok = check_openstudio_hpxml(self)

        # Install OpenStudio if missing
        if not openstudio_ok:
            click.echo("\n📥 Installing OpenStudio...")
            if not self._install_openstudio():
                success = False
        else:
            click.echo("\n✅ OpenStudio already installed")

        # Install OpenStudio-HPXML if missing
        if not hpxml_ok:
            click.echo("\n📥 Installing OpenStudio-HPXML...")
            if not self._install_openstudio_hpxml():
                success = False
        else:
            click.echo("\n✅ OpenStudio-HPXML already installed")

        if success:
            click.echo("\n✅ All dependencies installed successfully!")
            return True
        else:
            click.echo("\n❌ Some dependencies failed to install.")
            return False

    def uninstall_dependencies(self):
        """
        Uninstall OpenStudio and OpenStudio-HPXML dependencies.

        Returns:
            bool: True if uninstall completed successfully, False otherwise
        """
        click.echo("🗑️  Dependency Uninstaller")
        click.echo("=" * 30)

        # Check what's currently installed
        openstudio_installed = check_openstudio(self)
        hpxml_installed = check_openstudio_hpxml(self)

        if not openstudio_installed and not hpxml_installed:
            click.echo("ℹ️  No dependencies found to uninstall.")
            return True

        # Show what will be uninstalled
        to_uninstall = []
        if openstudio_installed:
            to_uninstall.append("OpenStudio CLI")
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
            # Bootstrap a ConfigManager that is allowed to auto-create config
            temp_config = ConfigManager(auto_create=True)
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
            else:
                # Create minimal config if no template found
                temp_config._create_minimal_config(user_config_file)
                click.echo(f"✅ User configuration created (minimal) at: {user_config_file}")

            return True

        except Exception as e:
            click.echo(f"❌ Failed to setup user configuration: {e}")
            return False

    def _copy_template_with_path_updates(self, template_path, user_config_file):
        """
        Copy template file to user config while preserving comments.

        Args:
            template_path (Path): Source template file
            user_config_file (Path): Destination user config file
        """
        # Read template content
        template_content = template_path.read_text(encoding="utf-8")

        # Write content to user config file (paths are now auto-detected at runtime)
        user_config_file.write_text(template_content, encoding="utf-8")
        click.echo(f"   Copied template to: {user_config_file}")

    # =========================================================================
    # Private helper methods - Installation handlers
    # =========================================================================

    def _handle_install_quiet(self, openstudio_ok, hpxml_ok):
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
            return check_openstudio(self) and check_openstudio_hpxml(self)

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
                return self._handle_install_quiet(openstudio_ok, hpxml_ok)
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
            click.echo("- Download: OpenStudio-*-Windows.tar.gz (portable)")
            click.echo("- Extract to a directory (no admin rights required)")
            click.echo("- Add bin/ directory to PATH if desired")
        else:
            click.echo("- Ubuntu/Debian: Download .deb package and run: sudo dpkg -i package.deb")
            click.echo("- Other Linux: Download .tar.gz and extract to ~/.local/share/")

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

    # =========================================================================
    # Private helper methods - Installation delegation to installer classes
    # =========================================================================

    def _install_openstudio(self):
        """
        Install OpenStudio automatically based on platform.

        Delegates to platform-specific installer classes.

        Returns:
            bool: True if installation successful, False otherwise
        """
        try:
            if self.is_windows:
                installer = WindowsInstaller(
                    self.REQUIRED_OPENSTUDIO_VERSION,
                    self.OPENSTUDIO_BUILD_HASH,
                    interactive=self.interactive,
                    install_quiet=self.install_quiet,
                )
                return installer.install()
            elif self.is_linux:
                installer = LinuxInstaller(
                    self.REQUIRED_OPENSTUDIO_VERSION,
                    self.OPENSTUDIO_BUILD_HASH,
                    self.default_openstudio_path,
                    interactive=self.interactive,
                    install_quiet=self.install_quiet,
                )
                return installer.install()
            else:
                click.echo(f"❌ Unsupported platform: {platform.system()}")
                return False
        except Exception as e:
            click.echo(f"❌ OpenStudio installation failed: {e}")
            return False

    def _install_openstudio_hpxml(self):
        """
        Install OpenStudio-HPXML by downloading and extracting zip file.

        Delegates to HPXMLInstaller class.

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        try:
            installer = HPXMLInstaller(
                self.REQUIRED_HPXML_VERSION,
                self.default_hpxml_path,
                interactive=self.interactive,
                install_quiet=self.install_quiet,
            )
            return installer.install()
        except Exception as e:
            click.echo(f"❌ OpenStudio-HPXML installation failed: {e}")
            return False

    def _uninstall_openstudio(self):
        """
        Uninstall OpenStudio based on platform.

        Delegates to platform-specific installer classes.

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        try:
            if self.is_windows:
                installer = WindowsInstaller(
                    self.REQUIRED_OPENSTUDIO_VERSION,
                    self.OPENSTUDIO_BUILD_HASH,
                    interactive=self.interactive,
                    install_quiet=self.install_quiet,
                )
                return installer.uninstall()
            elif self.is_linux:
                installer = LinuxInstaller(
                    self.REQUIRED_OPENSTUDIO_VERSION,
                    self.OPENSTUDIO_BUILD_HASH,
                    self.default_openstudio_path,
                    interactive=self.interactive,
                    install_quiet=self.install_quiet,
                )
                return installer.uninstall()
            else:
                click.echo(f"❌ Unsupported platform: {platform.system()}")
                return False
        except Exception as e:
            click.echo(f"❌ OpenStudio uninstall failed: {e}")
            return False

    def _uninstall_openstudio_hpxml(self):
        """
        Uninstall OpenStudio-HPXML by removing the installation directory.

        Delegates to HPXMLInstaller class.

        Returns:
            bool: True if uninstall successful, False otherwise
        """
        try:
            installer = HPXMLInstaller(
                self.REQUIRED_HPXML_VERSION,
                self.default_hpxml_path,
                interactive=self.interactive,
                install_quiet=self.install_quiet,
            )
            return installer.uninstall()
        except Exception as e:
            click.echo(f"❌ OpenStudio-HPXML uninstall failed: {e}")
            return False
