"""Unit tests for ConfigManager class."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from h2k_hpxml.config.manager import ConfigManager
from h2k_hpxml.config.manager import get_config_manager
from h2k_hpxml.config.manager import reset_config_manager
from h2k_hpxml.exceptions import ConfigurationError


def cleanup_user_configs():
    """Remove user config directory to ensure test isolation."""
    import platform
    import shutil

    try:
        # Compute the user config path directly to avoid circular imports
        if platform.system() == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                user_config_dir = Path(appdata) / "h2k_hpxml"
            else:
                user_config_dir = Path.home() / "AppData" / "Roaming" / "h2k_hpxml"
        else:
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                user_config_dir = Path(xdg_config_home) / "h2k_hpxml"
            else:
                user_config_dir = Path.home() / ".config" / "h2k_hpxml"

        if user_config_dir.exists():
            shutil.rmtree(user_config_dir)
    except (PermissionError, OSError):
        # If we can't remove it, that's okay for tests
        pass


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def setup_method(self):
        """Reset global config manager before each test."""
        reset_config_manager()
        # Save original working directory
        self._original_cwd = os.getcwd()

        # Clean up any existing user config files that could interfere with tests
        cleanup_user_configs()

    def teardown_method(self):
        """Restore original working directory after each test."""
        os.chdir(self._original_cwd)

        # Clean up user configs after each test to ensure isolation
        cleanup_user_configs()

    def test_config_manager_initialization_with_missing_file(self):
        """Test ConfigManager raises error when config file not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)  # Change to directory without config file

            with pytest.raises(ConfigurationError, match="Configuration file not found"):
                ConfigManager(auto_create=False)

    def test_config_manager_initialization_with_valid_file(self):
        """Test ConfigManager initializes correctly with valid config file."""
        config_content = """
[paths]
source_h2k_path = /test/input
hpxml_os_path = /test/openstudio
dest_hpxml_path = /test/output

[simulation]
flags = --test

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = DEBUG
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            config = ConfigManager(auto_create=False)

            assert config.get("paths", "source_h2k_path") == "/test/input"
            assert config.get("weather", "weather_library") == "test"
            assert config.log_level == "DEBUG"

    def test_simplified_config_loading(self):
        """Test simplified configuration loading without environment specificity."""
        config_content = """
[paths]
source_h2k_path = /project/input
hpxml_os_path = /project/openstudio
dest_hpxml_path = /project/output

[simulation]
flags = --add-component-loads

[weather]
weather_library = historic
weather_vintage = CWEC2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            # Test config loads regardless of environment parameter
            config_dev = ConfigManager(environment="dev", auto_create=False)
            config_prod = ConfigManager(environment="prod", auto_create=False)

            # Both should load the same config file and return same values
            assert config_dev.get("paths", "source_h2k_path") == "/project/input"
            assert config_prod.get("paths", "source_h2k_path") == "/project/input"
            assert config_dev.log_level == "INFO"
            assert config_prod.log_level == "INFO"

    def test_environment_variable_overrides(self):
        """Test environment variable overrides work correctly."""
        config_content = """
[paths]
source_h2k_path = /original/input
hpxml_os_path = /original/openstudio
dest_hpxml_path = /original/output

[simulation]
flags = --original

[weather]
weather_library = original
weather_vintage = ORIGINAL2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            # Set environment variables
            with patch.dict(
                os.environ,
                {"H2K_PATHS_SOURCE_H2K_PATH": "/env/input", "H2K_LOGGING_LOG_LEVEL": "ERROR"},
            ):
                config = ConfigManager(auto_create=False)

                # Check overrides work
                assert config.get("paths", "source_h2k_path") == "/env/input"
                assert config.log_level == "ERROR"

                # Check non-overridden values remain
                assert config.get("weather", "weather_library") == "original"

    def test_configuration_validation(self):
        """Test configuration validation catches missing required sections."""
        incomplete_config = """
[paths]
source_h2k_path = /test/input

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(incomplete_config)
            os.chdir(temp_dir)

            with pytest.raises(ConfigurationError, match="Missing required configuration section"):
                ConfigManager(auto_create=False)

    def test_path_validation_warnings(self):
        """Test path validation generates warnings for missing required paths."""
        config_content = """
[paths]
source_h2k_path = /nonexistent/input
hpxml_os_path = /nonexistent/openstudio
dest_hpxml_path = /test/output

[simulation]
flags = --test

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            with patch("h2k_hpxml.config.manager.logger") as mock_logger:
                ConfigManager(auto_create=False)

                # Should generate warnings for nonexistent required paths
                warning_calls = mock_logger.warning.call_args_list
                assert any("does not exist" in str(call) for call in warning_calls)

    def test_get_methods_with_fallbacks(self):
        """Test get methods with fallback values."""
        config_content = """
[paths]
source_h2k_path = /test/input
hpxml_os_path = /test/openstudio
dest_hpxml_path = /test/output

[simulation]
flags = --test

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = INFO
log_to_file = true
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            config = ConfigManager(auto_create=False)

            # Test get with fallback
            assert config.get("paths", "source_h2k_path", "fallback") == "/test/input"
            assert config.get("paths", "nonexistent", "fallback") == "fallback"

            # Test get_bool
            assert config.get_bool("logging", "log_to_file") is True
            assert config.get_bool("logging", "nonexistent", False) is False

            # Test get_int (add a numeric value to test)
            with patch.object(config.config, "getint", return_value=42):
                assert config.get_int("simulation", "timeout", 30) == 42
            assert config.get_int("simulation", "nonexistent", 30) == 30

    def test_get_path_method(self):
        """Test get_path method returns Path objects."""
        config_content = """
[paths]
source_h2k_path = /test/input
hpxml_os_path = /test/openstudio
dest_hpxml_path = output
relative_path = ./relative

[simulation]
flags = --test

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            config = ConfigManager(auto_create=False)

            # Test absolute path
            path = config.get_path("paths", "source_h2k_path")
            assert isinstance(path, Path)
            assert str(path) == "/test/input"

            # Test relative path resolution
            rel_path = config.get_path("paths", "relative_path")
            assert isinstance(rel_path, Path)
            assert rel_path.is_absolute()

            # Test nonexistent path
            none_path = config.get_path("paths", "nonexistent")
            assert none_path is None

    def test_property_accessors(self):
        """Test property accessors for common configuration values."""
        config_content = """
[paths]
source_h2k_path = /test/input
dest_hpxml_path = /test/output

[simulation]
flags = --debug --verbose

[weather]
weather_library = historic
weather_vintage = CWEC2020

[logging]
log_level = WARNING
log_to_file = false
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            config = ConfigManager(auto_create=False)

            # Test path properties
            assert str(config.source_h2k_path) == "/test/input"
            assert str(config.dest_hpxml_path) == "/test/output"

            # hpxml_os_path and openstudio_binary are now auto-detected (not in config)
            # In test environment with real OpenStudio installation, these should be found
            hpxml_path = config.hpxml_os_path
            assert hpxml_path is not None, "Should auto-detect HPXML installation path"

            openstudio_binary = config.openstudio_binary
            assert openstudio_binary is not None, "Should auto-detect OpenStudio binary path"

            # Test other properties
            assert config.simulation_flags == "--debug --verbose"
            assert config.weather_library == "historic"
            assert config.weather_vintage == "CWEC2020"
            assert config.log_level == "WARNING"
            assert config.log_to_file is False

    def test_resource_path_methods(self):
        """Test resource path helper methods."""
        config_content = """
[paths]
source_h2k_path = /test/input
hpxml_os_path = /test/openstudio
dest_hpxml_path = /test/output

[simulation]
flags = --test

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            config = ConfigManager(auto_create=False)

            # Test resource path method (will raise error for nonexistent resource)
            with pytest.raises(ConfigurationError, match="Resource file not found"):
                config.get_resource_path("nonexistent.xml")

            # Test template path method
            with pytest.raises(ConfigurationError, match="Resource file not found"):
                config.get_template_path("custom_template.xml")

    def test_section_access_methods(self):
        """Test section access methods."""
        config_content = """
[paths]
source_h2k_path = /test/input
hpxml_os_path = /test/openstudio
dest_hpxml_path = /test/output

[simulation]
flags = --test
timeout = 300

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            config = ConfigManager(auto_create=False)

            # Test get_section
            paths_section = config.get_section("paths")
            assert "source_h2k_path" in paths_section
            assert paths_section["source_h2k_path"] == "/test/input"

            # Test has_section
            assert config.has_section("paths") is True
            assert config.has_section("nonexistent") is False

            # Test has_option
            assert config.has_option("paths", "source_h2k_path") is True
            assert config.has_option("paths", "nonexistent") is False

    def test_to_dict_method(self):
        """Test converting configuration to dictionary."""
        config_content = """
[paths]
source_h2k_path = /test/input
hpxml_os_path = /test/openstudio
dest_hpxml_path = /test/output

[simulation]
flags = --test

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            config = ConfigManager(auto_create=False)
            config_dict = config.to_dict()

            assert "paths" in config_dict
            assert "weather" in config_dict
            assert "logging" in config_dict
            assert config_dict["paths"]["source_h2k_path"] == "/test/input"
            assert config_dict["weather"]["weather_library"] == "test"


class TestGlobalConfigManager:
    """Test cases for global configuration manager functions."""

    def setup_method(self):
        """Reset global config manager before each test."""
        reset_config_manager()
        # Save original working directory
        self._original_cwd = os.getcwd()

        # Clean up any existing user config files that could interfere with tests
        cleanup_user_configs()

    def teardown_method(self):
        """Restore original working directory after each test."""
        os.chdir(self._original_cwd)

        # Clean up user configs after each test to ensure isolation
        cleanup_user_configs()

    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton instance."""
        config_content = """
[paths]
source_h2k_path = /test/input
hpxml_os_path = /test/openstudio
dest_hpxml_path = /test/output

[simulation]
flags = --test

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            # Get config manager twice
            config1 = get_config_manager()
            config2 = get_config_manager()

            # Should be the same instance
            assert config1 is config2

    def test_reset_config_manager(self):
        """Test that reset_config_manager clears singleton."""
        config_content = """
[paths]
source_h2k_path = /test/input
hpxml_os_path = /test/openstudio
dest_hpxml_path = /test/output

[simulation]
flags = --test

[weather]
weather_library = test
weather_vintage = TEST2020

[logging]
log_level = INFO
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "conversionconfig.ini"
            config_path.write_text(config_content)
            os.chdir(temp_dir)

            # Get initial config manager
            config1 = get_config_manager()

            # Reset and get new one
            reset_config_manager()
            config2 = get_config_manager()

            # Should be different instances
            assert config1 is not config2

    def test_user_config_auto_creation(self):
        """Test that user config is auto-created when no config files exist."""
        import shutil
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)  # Change to directory without config file

            # Mock the user config path to use a temporary directory
            mock_user_config_dir = Path(temp_dir) / "user_config"

            with patch.object(
                ConfigManager, "_get_user_config_path", return_value=mock_user_config_dir
            ):
                # This should auto-create the user config
                config = ConfigManager(auto_create=True)

                # Verify config was created
                user_config_file = mock_user_config_dir / "config.ini"
                assert user_config_file.exists()

                # Verify it has the expected minimal configuration
                assert config.get("paths", "source_h2k_path") == "examples"
                assert config.get("weather", "weather_library") == "historic"
                assert config.get("logging", "log_level") == "INFO"

    def test_user_config_priority_over_project_config(self):
        """Test that user config takes priority over project config."""
        import tempfile
        from unittest.mock import patch

        # Create project config
        project_config = """
[paths]
source_h2k_path = /project/input
hpxml_os_path = /project/openstudio
dest_hpxml_path = /project/output

[simulation]
flags = --project

[weather]
weather_library = project
weather_vintage = PROJECT2020

[logging]
log_level = INFO
"""

        # Create user config content
        user_config = """
[paths]
source_h2k_path = /user/input
hpxml_os_path = /user/openstudio
dest_hpxml_path = /user/output

[simulation]
flags = --user

[weather]
weather_library = user
weather_vintage = USER2020

[logging]
log_level = DEBUG
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create project config file
            project_config_path = Path(temp_dir) / "conversionconfig.ini"
            project_config_path.write_text(project_config)
            os.chdir(temp_dir)

            # Create user config directory and file
            mock_user_config_dir = Path(temp_dir) / "user_config"
            mock_user_config_dir.mkdir()
            user_config_path = mock_user_config_dir / "config.ini"
            user_config_path.write_text(user_config)

            with patch.object(
                ConfigManager, "_get_user_config_path", return_value=mock_user_config_dir
            ):
                config = ConfigManager(auto_create=False)

                # Should use user config values, not project config values
                assert config.get("paths", "source_h2k_path") == "/user/input"
                assert config.get("weather", "weather_library") == "user"
                assert config.log_level == "DEBUG"
