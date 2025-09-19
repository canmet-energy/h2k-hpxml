"""
DEPRECATED: Config update functionality is no longer needed.

Dependencies are now auto-detected at runtime, so config files don't need
to store dependency paths. This file is kept as a placeholder but most tests
have been removed since the functionality is deprecated.
"""

from h2k_hpxml.utils.dependencies import DependencyManager


class TestConfigUpdate:
    """DEPRECATED: Config updates no longer needed - dependencies are auto-detected."""

    def test_config_update_methods_are_stubbed(self):
        """Test that config update methods exist but are stubbed out for backward compatibility."""
        manager = DependencyManager(interactive=False)

        # Methods should exist for backward compatibility
        assert hasattr(manager, '_update_single_config_file'), "Should have stubbed _update_single_config_file method"
        assert hasattr(manager, '_update_config_file'), "Should have stubbed _update_config_file method"
        assert hasattr(manager, '_find_all_config_files'), "Should have _find_all_config_files method"

        # Should be callable and return success (but do nothing)
        result = manager._update_config_file()
        assert result is True, "Should return True for backward compatibility"

        # find_all_config_files should still work (used for discovery)
        config_files = manager._find_all_config_files()
        assert isinstance(config_files, list), "Should return a list of config files"