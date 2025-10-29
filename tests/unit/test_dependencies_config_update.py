"""
DEPRECATED: Config update functionality is no longer needed.

Dependencies are now auto-detected at runtime, so config files don't need
to store dependency paths. This file is kept as a placeholder but most tests
have been removed since the functionality is deprecated.

After refactoring, config-related methods were removed from DependencyManager
since they are now handled by ConfigManager or are no longer needed.
"""

from h2k_hpxml.utils.dependencies import DependencyManager


class TestConfigUpdate:
    """DEPRECATED: Config updates no longer needed - dependencies are auto-detected."""

    def test_config_update_methods_are_stubbed(self):
        """Test that DependencyManager no longer has config update methods (refactored out)."""
        manager = DependencyManager(interactive=False)

        # After refactoring, these methods were removed since config management
        # is now handled by ConfigManager, not DependencyManager
        assert not hasattr(
            manager, "_update_single_config_file"
        ), "Method removed during refactoring - config is handled by ConfigManager"
        assert not hasattr(
            manager, "_update_config_file"
        ), "Method removed during refactoring - dependencies are auto-detected"
        assert not hasattr(
            manager, "_find_all_config_files"
        ), "Method removed during refactoring - not needed in DependencyManager"

        # DependencyManager now focuses on dependency validation and installation
        assert hasattr(manager, "validate_all"), "Should have validate_all method"
        assert hasattr(manager, "install_dependencies"), "Should have install_dependencies method"
