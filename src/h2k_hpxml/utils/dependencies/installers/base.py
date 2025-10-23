#!/usr/bin/env python3
"""
Base installer class for dependency management.

Provides abstract interface that platform-specific installers must implement.
"""

import platform
from abc import ABC
from abc import abstractmethod


class BaseInstaller(ABC):
    """Abstract base class for dependency installers.

    Provides common interface for installing, uninstalling, and validating
    dependencies across different platforms.

    Attributes:
        interactive (bool): Whether to prompt user for input
        install_quiet (bool): Whether to suppress output during installation
        is_windows (bool): True if running on Windows
        is_linux (bool): True if running on Linux
    """

    def __init__(self, interactive=True, install_quiet=False):
        """Initialize installer.

        Args:
            interactive (bool): Prompt user for installation choices
            install_quiet (bool): Suppress output during installation
        """
        self.interactive = interactive
        self.install_quiet = install_quiet
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux"

    @abstractmethod
    def install(self, target_path):
        """Install the dependency to the specified path.

        Args:
            target_path (Path): Installation target directory

        Returns:
            bool: True if installation succeeded, False otherwise
        """
        pass

    @abstractmethod
    def uninstall(self, install_path):
        """Uninstall the dependency from the specified path.

        Args:
            install_path (Path): Installation directory to remove

        Returns:
            bool: True if uninstallation succeeded, False otherwise
        """
        pass

    @abstractmethod
    def validate(self):
        """Validate that the dependency is properly installed.

        Returns:
            bool: True if dependency is valid, False otherwise
        """
        pass

    def show_manual_instructions(self):
        """Show manual installation instructions to the user.

        This is an optional method that subclasses can override
        to provide platform-specific manual installation instructions.
        The default implementation does nothing.
        """
        # Optional method - subclasses may override
        return None
