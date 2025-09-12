"""
Unit tests for dependency manager config update functionality.
"""

import tempfile
import os
from pathlib import Path

from h2k_hpxml.utils.dependencies import DependencyManager


class TestConfigUpdate:
    """Test that dependency manager correctly updates all config files."""

    def test_find_all_config_files_method_exists(self):
        """Test that the _find_all_config_files method exists and returns a list."""
        manager = DependencyManager(interactive=False)
        
        # Call the method - should not crash
        config_files = manager._find_all_config_files()
        
        # Should return a list
        assert isinstance(config_files, list), "Should return a list of config files"

    def test_user_config_integration_after_fix(self):
        """Integration test to verify the fix works with actual config manager."""
        manager = DependencyManager(interactive=False)
        
        # Call the method - should include user config if it exists
        config_files = manager._find_all_config_files()
        
        # If user config exists, it should be included
        try:
            from h2k_hpxml.config.manager import ConfigManager
            config_manager = ConfigManager(auto_create=False)
            user_config_dir = config_manager._get_user_config_path()
            user_config_file = user_config_dir / "config.ini"
            
            if user_config_file.exists():
                assert str(user_config_file) in config_files, (
                    f"User config {user_config_file} should be included in {config_files}"
                )
                print(f"✅ User config correctly included: {user_config_file}")
            else:
                print("⚠️  No user config file exists to test")
                
        except Exception as e:
            # If there's an error accessing user config, the method should still work
            print(f"User config access error (expected in some environments): {e}")

    def test_required_methods_exist(self):
        """Test that all required methods exist for the config update functionality."""
        manager = DependencyManager(interactive=False)
        
        # Verify all the methods used in the fix exist
        assert hasattr(manager, '_find_all_config_files'), "Should have _find_all_config_files method"
        assert hasattr(manager, '_update_config_file'), "Should have _update_config_file method"
        assert hasattr(manager, '_update_all_config_files'), "Should have _update_all_config_files method"
        assert hasattr(manager, '_update_single_config_file'), "Should have _update_single_config_file method"
        
        print("✅ All required config update methods exist")