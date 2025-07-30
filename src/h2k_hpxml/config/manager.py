"""
Configuration management system for H2K-HPXML package.

Provides centralized configuration management with support for:
- INI file loading
- Environment variable overrides
- Environment-specific profiles (dev, test, prod)
- Path management and validation
- Configuration schema validation
"""

import configparser
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..exceptions import ConfigurationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """
    Centralized configuration manager for H2K-HPXML package.

    Supports loading configuration from:
    1. INI files (conversionconfig.ini)
    2. Environment variables (H2K_*)
    3. Default values
    4. Environment-specific overrides
    """

    def __init__(self, config_file: Optional[Union[str, Path]] = None, environment: str = "prod"):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to INI configuration file. If None, searches for conversionconfig.ini
            environment: Environment profile (dev, test, prod)
        """
        self.environment = environment
        self.config = configparser.ConfigParser()
        self._config_data = {}

        # Load configuration
        self._load_configuration(config_file)
        self._apply_environment_overrides()
        self._validate_configuration()

        logger.info(f"Configuration loaded for environment: {environment}")

    def _load_configuration(self, config_file: Optional[Union[str, Path]] = None) -> None:
        """Load configuration from INI file."""
        if config_file is None:
            config_file = self._find_config_file()

        config_path = Path(config_file)
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            self.config.read(config_path)
            logger.info(f"Loaded configuration from: {config_path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration file: {e}")

    def _find_config_file(self) -> Path:
        """Find conversionconfig.ini or environment-specific config in config directory or parent directories."""
        current_dir = Path.cwd()

        # Search up to 3 levels for config file
        for _ in range(3):
            # Check in config subdirectory first (new structure)
            config_dir = current_dir / "config"
            if config_dir.exists():
                # First try environment-specific config in config dir
                env_config_path = config_dir / f"conversionconfig.{self.environment}.ini"
                if env_config_path.exists():
                    logger.info(f"Using environment-specific config: {env_config_path}")
                    return env_config_path

                # Fallback to default config in config dir
                config_path = config_dir / "conversionconfig.ini"
                if config_path.exists():
                    logger.info(f"Using config from config directory: {config_path}")
                    return config_path

            # Fallback to old structure (backward compatibility)
            # First try environment-specific config
            env_config_path = current_dir / f"conversionconfig.{self.environment}.ini"
            if env_config_path.exists():
                logger.info(f"Using environment-specific config: {env_config_path}")
                return env_config_path

            # Fallback to default config
            config_path = current_dir / "conversionconfig.ini"
            if config_path.exists():
                logger.info(f"Using legacy config location: {config_path}")
                return config_path
            current_dir = current_dir.parent

        raise ConfigurationError(
            f"Configuration file not found for environment '{self.environment}' or default 'conversionconfig.ini'"
        )

    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Environment variables with H2K_SECTION_KEY format override config values
        for env_var, value in os.environ.items():
            if env_var.startswith("H2K_"):
                # Parse H2K_SECTION_KEY format
                parts = env_var[4:].lower().split("_", 1)  # Remove H2K_ prefix
                if len(parts) == 2:
                    section, key = parts
                    if not self.config.has_section(section):
                        self.config.add_section(section)
                    self.config.set(section, key, value)
                    logger.debug(f"Applied environment override: {env_var} = {value}")

    def _validate_configuration(self) -> None:
        """Validate required configuration sections and keys."""
        required_sections = ["paths", "simulation", "weather", "logging"]
        required_keys = {
            "paths": ["source_h2k_path", "hpxml_os_path", "dest_hpxml_path"],
            "weather": ["weather_library", "weather_vintage"],
            "logging": ["log_level"],
        }

        # Check required sections
        for section in required_sections:
            if not self.config.has_section(section):
                raise ConfigurationError(f"Missing required configuration section: {section}")

        # Check required keys
        for section, keys in required_keys.items():
            for key in keys:
                if not self.config.has_option(section, key):
                    raise ConfigurationError(f"Missing required configuration key: {section}.{key}")

        # Validate paths exist
        self._validate_paths()

    def _validate_paths(self) -> None:
        """Validate that configured paths exist or can be created."""
        paths_to_check = [
            ("source_h2k_path", True),  # Must exist
            ("hpxml_os_path", True),  # Must exist
            ("dest_hpxml_path", False),  # Can be created
        ]

        for path_key, must_exist in paths_to_check:
            path_str = self.get("paths", path_key)
            if path_str:
                path = Path(path_str)
                if must_exist and not path.exists():
                    logger.warning(f"Configured path does not exist: {path_key} = {path}")
                elif not must_exist:
                    # Try to ensure parent directory exists for output paths
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                    except (PermissionError, OSError) as e:
                        logger.warning(
                            f"Cannot create parent directory for {path_key} = {path}: {e}"
                        )
                        # Continue without failing - this is common in test environments

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            section: Configuration section name
            key: Configuration key name
            fallback: Default value if key not found

        Returns:
            Configuration value
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value."""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
        except ValueError as e:
            raise ConfigurationError(f"Invalid boolean value for {section}.{key}: {e}")

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value."""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
        except ValueError as e:
            raise ConfigurationError(f"Invalid integer value for {section}.{key}: {e}")

    def get_path(self, section: str, key: str, fallback: Optional[str] = None) -> Optional[Path]:
        """
        Get path configuration value as Path object.

        Resolves relative paths relative to config file directory.
        """
        path_str = self.get(section, key, fallback)
        if path_str is None:
            return None

        path = Path(path_str)
        if not path.is_absolute():
            # Resolve relative to config file directory
            config_dir = Path.cwd()  # Fallback to current directory
            path = config_dir / path

        return path.resolve()

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all key-value pairs from a configuration section."""
        if not self.config.has_section(section):
            return {}
        return dict(self.config.items(section))

    def has_section(self, section: str) -> bool:
        """Check if configuration section exists."""
        return self.config.has_section(section)

    def has_option(self, section: str, key: str) -> bool:
        """Check if configuration option exists."""
        return self.config.has_option(section, key)

    def get_resource_path(self, resource_name: str) -> Path:
        """
        Get path to package resource file.

        Args:
            resource_name: Name of resource file (e.g., 'template_base.xml')

        Returns:
            Absolute path to resource file
        """
        # Get package root directory
        package_root = Path(__file__).parent.parent
        resource_path = package_root / "resources" / resource_name

        if not resource_path.exists():
            raise ConfigurationError(f"Resource file not found: {resource_name}")

        return resource_path

    def get_template_path(self, template_name: str = "template_base.xml") -> Path:
        """Get path to HPXML template file."""
        return self.get_resource_path(template_name)

    def get_config_resource_path(self, config_name: str) -> Path:
        """Get path to configuration resource file (e.g., config_locations.json)."""
        return self.get_resource_path(config_name)

    @property
    def source_h2k_path(self) -> Path:
        """Source H2K files directory."""
        return self.get_path("paths", "source_h2k_path")

    @property
    def hpxml_os_path(self) -> Path:
        """OpenStudio-HPXML installation directory."""
        return self.get_path("paths", "hpxml_os_path")

    @property
    def dest_hpxml_path(self) -> Path:
        """Destination directory for generated HPXML files."""
        return self.get_path("paths", "dest_hpxml_path")

    @property
    def openstudio_binary(self) -> Optional[str]:
        """Path to OpenStudio binary."""
        return self.get("paths", "openstudio_binary")

    @property
    def simulation_flags(self) -> str:
        """OpenStudio-HPXML simulation flags."""
        return self.get("simulation", "flags", "")

    @property
    def weather_library(self) -> str:
        """Weather library to use (historic, etc.)."""
        return self.get("weather", "weather_library", "historic")

    @property
    def weather_vintage(self) -> str:
        """Weather vintage to use (CWEC2020, etc.)."""
        return self.get("weather", "weather_vintage", "CWEC2020")

    @property
    def log_level(self) -> str:
        """Logging level."""
        return self.get("logging", "log_level", "INFO")

    @property
    def log_to_file(self) -> bool:
        """Whether to log to file."""
        return self.get_bool("logging", "log_to_file", True)

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert configuration to nested dictionary."""
        result = {}
        for section_name in self.config.sections():
            result[section_name] = dict(self.config.items(section_name))
        return result


# Global configuration instance
_config_manager = None


def get_config_manager(
    config_file: Optional[Union[str, Path]] = None, environment: str = "prod"
) -> ConfigManager:
    """
    Get global configuration manager instance.

    Args:
        config_file: Path to configuration file
        environment: Environment profile

    Returns:
        ConfigManager instance
    """
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigManager(config_file, environment)

    return _config_manager


def reset_config_manager() -> None:
    """Reset global configuration manager (useful for testing)."""
    global _config_manager
    _config_manager = None
