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
import platform
from pathlib import Path

from ..exceptions import ConfigurationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """
    Centralized configuration manager for H2K-HPXML package.

    Supports loading configuration from:
    1. User config directory
    2. Project config files (conversionconfig.ini)
    3. Environment variables (H2K_*)
    4. Default values
    5. Environment-specific overrides
    """

    def __init__(
        self,
        config_file=None,
        environment="prod",
        auto_create=True,
    ):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to INI configuration file. If None, searches hierarchically
            environment: Environment profile (dev, test, prod)
            auto_create: Whether to auto-create user config from template if not found
        """
        self.environment = environment
        self.auto_create = auto_create
        self.config = configparser.ConfigParser()
        self._config_data = {}

        # Load configuration
        self._load_configuration(config_file)
        self._apply_environment_overrides()
        self._validate_configuration()

        logger.info(f"Configuration loaded for environment: {environment}")

    def _get_user_config_path(self):
        """
        Get user configuration directory path based on OS.

        Returns:
            Path to user configuration directory (~/.config/h2k_hpxml on Linux/macOS,
            %APPDATA%/h2k_hpxml on Windows)
        """
        if platform.system() == "Windows":
            # Use APPDATA on Windows
            appdata = os.environ.get("APPDATA")
            if appdata:
                return Path(appdata) / "h2k_hpxml"
            else:
                # Fallback to user home
                return Path.home() / "AppData" / "Roaming" / "h2k_hpxml"
        else:
            # Use XDG Base Directory on Linux/macOS
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                return Path(xdg_config_home) / "h2k_hpxml"
            else:
                return Path.home() / ".config" / "h2k_hpxml"

    def _load_configuration(self, config_file=None):
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

    def _find_config_file(self):
        """
        Find configuration file with hierarchical search.

        Search order (highest to lowest priority):
        1. User config directory
        2. Project config directory
        3. Create from template
        """
        # 1. User config directory
        user_config = self._get_user_config_path() / "config.ini"
        if user_config.exists():
            logger.info(f"Using user config: {user_config}")
            return user_config

        # 2. Project config directory (search up to 3 levels)
        current_dir = Path.cwd()
        for _ in range(3):
            # Check in config subdirectory first (new structure)
            config_dir = current_dir / "config"
            if config_dir.exists():
                config_path = config_dir / "conversionconfig.ini"
                if config_path.exists():
                    logger.info(f"Using project config from config directory: {config_path}")
                    return config_path

            # Fallback to old structure (backward compatibility)
            config_path = current_dir / "conversionconfig.ini"
            if config_path.exists():
                logger.info(f"Using legacy config location: {config_path}")
                return config_path
            current_dir = current_dir.parent

        # 3. Create from template (if auto_create is enabled)
        if self.auto_create:
            logger.info("No existing config found. Creating user config from template")
            return self._create_config_from_template()
        else:
            raise ConfigurationError(
                "Configuration file not found. Use 'h2k-deps --setup' to create user configuration."
            )

    def _apply_environment_overrides(self):
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

    def _validate_configuration(self):
        """Validate required configuration sections and keys."""
        required_sections = ["paths", "simulation", "weather", "logging"]
        required_keys = {
            "paths": ["dest_hpxml_path"],  # Removed hpxml_os_path - now auto-detected
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

    def _validate_paths(self):
        """Validate that configured paths exist or can be created."""
        paths_to_check = [
            ("source_h2k_path", True),   # Input path must exist
            # Removed ("hpxml_os_path", True) - now auto-detected, not in config
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

    def get(self, section, key, fallback=None):
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

    def get_bool(self, section, key, fallback=False):
        """Get boolean configuration value."""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
        except ValueError as e:
            raise ConfigurationError(f"Invalid boolean value for {section}.{key}: {e}")

    def get_int(self, section, key, fallback=0):
        """Get integer configuration value."""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
        except ValueError as e:
            raise ConfigurationError(f"Invalid integer value for {section}.{key}: {e}")

    def get_path(self, section, key, fallback=None):
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

    def get_section(self, section):
        """Get all key-value pairs from a configuration section."""
        if not self.config.has_section(section):
            return {}
        return dict(self.config.items(section))

    def has_section(self, section):
        """Check if configuration section exists."""
        return self.config.has_section(section)

    def has_option(self, section, key):
        """Check if configuration option exists."""
        return self.config.has_option(section, key)

    def get_resource_path(self, resource_name):
        """
        Get path to package resource file.

        Args:
            resource_name: Name of resource file (e.g., 'template_base.xml')

        Returns:
            Absolute path to resource file
        """
        resource_path = None

        # Strategy 1: Try pkg_resources for pip installations
        try:
            import pkg_resources
            resource_path = Path(pkg_resources.resource_filename('h2k_hpxml', f'resources/{resource_name}'))
            if resource_path.exists():
                return resource_path
        except (ImportError, FileNotFoundError):
            pass

        # Strategy 2: Fallback to relative path (for development)
        package_root = Path(__file__).parent.parent
        resource_path = package_root / "resources" / resource_name

        if not resource_path.exists():
            raise ConfigurationError(
                f"Resource file not found: {resource_name}\n"
                "Tried:\n"
                "1. pkg_resources (pip installation)\n"
                "2. Relative path (development mode)"
            )

        return resource_path

    def get_template_path(self, template_name="template_base.xml"):
        """Get path to HPXML template file."""
        return self.get_resource_path(template_name)

    def get_config_resource_path(self, config_name):
        """Get path to configuration resource file (e.g., config_locations.json)."""
        return self.get_resource_path(config_name)

    @property
    def source_h2k_path(self):
        """Source H2K files directory."""
        return self.get_path("paths", "source_h2k_path")

    @property
    def hpxml_os_path(self):
        """OpenStudio-HPXML installation directory (auto-detected)."""
        from ..utils.dependencies import get_hpxml_os_path
        
        hpxml_path = get_hpxml_os_path()
        if hpxml_path:
            logger.debug(f"Auto-detected OpenStudio-HPXML path: {hpxml_path}")
            return hpxml_path
            
        logger.warning("OpenStudio-HPXML installation not found")
        return None

    @property
    def dest_hpxml_path(self):
        """Destination directory for generated HPXML files."""
        return self.get_path("paths", "dest_hpxml_path")

    @property
    def openstudio_binary(self):
        """Path to OpenStudio binary (auto-detected)."""
        from ..utils.dependencies import get_openstudio_binary
        
        binary_path = get_openstudio_binary()
        if binary_path:
            logger.debug(f"Auto-detected OpenStudio binary: {binary_path}")
            return binary_path
            
        # Fall back to system openstudio if available
        import shutil
        system_path = shutil.which("openstudio")
        if system_path:
            logger.debug(f"Using system OpenStudio binary: {system_path}")
            return system_path
            
        logger.warning("OpenStudio binary not found")
        return "openstudio"  # Fallback for error handling

    @property
    def energyplus_binary(self):
        """Path to EnergyPlus binary (auto-detected)."""
        from ..utils.dependencies import get_energyplus_binary
        
        energyplus_path = get_energyplus_binary()
        if energyplus_path:
            logger.debug(f"Auto-detected EnergyPlus binary: {energyplus_path}")
            return energyplus_path
            
        # Fall back to system energyplus if available
        import shutil
        system_path = shutil.which("energyplus")
        if system_path:
            logger.debug(f"Using system EnergyPlus binary: {system_path}")
            return system_path
            
        logger.warning("EnergyPlus binary not found")
        return "energyplus"  # Fallback for error handling

    @property
    def simulation_flags(self):
        """OpenStudio-HPXML simulation flags."""
        return self.get("simulation", "flags", "")

    @property
    def weather_library(self):
        """Weather library to use (historic, etc.)."""
        return self.get("weather", "weather_library", "historic")

    @property
    def weather_vintage(self):
        """Weather vintage to use (CWEC2020, etc.)."""
        return self.get("weather", "weather_vintage", "CWEC2020")

    @property
    def log_level(self):
        """Logging level."""
        return self.get("logging", "log_level", "INFO")

    @property
    def log_to_file(self):
        """Whether to log to file."""
        return self.get_bool("logging", "log_to_file", True)

    def to_dict(self):
        """Convert configuration to nested dictionary."""
        result = {}
        for section_name in self.config.sections():
            result[section_name] = dict(self.config.items(section_name))
        return result

    def _create_config_from_template(self):
        """
        Create user configuration file from template.

        Returns:
            Path to created config file
        """
        # Get user config directory and ensure it exists
        user_config_dir = self._get_user_config_path()
        user_config_dir.mkdir(parents=True, exist_ok=True)

        # Use single config filename
        user_config_path = user_config_dir / "config.ini"

        # Find template file
        template_path = self._find_template_file("conversionconfig.template.ini")

        if template_path and template_path.exists():
            # Copy template to user config
            import shutil

            shutil.copy2(template_path, user_config_path)
            logger.info(f"Created user config from template: {user_config_path}")
        else:
            # Create minimal config if no template found
            self._create_minimal_config(user_config_path)
            logger.info(f"Created minimal user config: {user_config_path}")

        return user_config_path

    def _find_template_file(self, template_name):
        """
        Find template file in project or package resources.

        Args:
            template_name: Name of template file

        Returns:
            Path to template file if found
        """
        # Check project config/defaults directory
        current_dir = Path.cwd()
        for _ in range(3):
            defaults_dir = current_dir / "config" / "defaults"
            template_path = defaults_dir / template_name
            if template_path.exists():
                return template_path
            current_dir = current_dir.parent

        # Check package resources (future implementation)
        # package_templates = Path(__file__).parent.parent / "resources" / "templates"
        # template_path = package_templates / template_name
        # if template_path.exists():
        #     return template_path

        return None

    def _create_minimal_config(self, config_path):
        """
        Create minimal configuration file with default values.

        Args:
            config_path: Path where to create config file
        """
        minimal_config = configparser.ConfigParser()

        # Add required sections with minimal values
        minimal_config.add_section("paths")
        minimal_config.set("paths", "source_h2k_path", "examples")
        # Note: OpenStudio and OpenStudio-HPXML paths are automatically detected
        # No configuration needed - removed hpxml_os_path, openstudio_binary, energyplus_binary
        minimal_config.set("paths", "dest_hpxml_path", "output/hpxml/")
        minimal_config.set("paths", "dest_compare_data", "output/comparisons/")
        minimal_config.set("paths", "workflow_temp_path", "output/workflows/")

        minimal_config.add_section("simulation")
        minimal_config.set("simulation", "flags", "--add-component-loads --debug")

        minimal_config.add_section("weather")
        minimal_config.set("weather", "weather_library", "historic")
        minimal_config.set("weather", "weather_vintage", "CWEC2020")

        minimal_config.add_section("logging")
        minimal_config.set("logging", "log_level", "INFO")
        minimal_config.set("logging", "log_to_file", "true")
        minimal_config.set("logging", "log_file_path", "output/logs/h2k_hpxml.log")

        with open(config_path, "w") as f:
            f.write("# H2K-HPXML Configuration\n")
            f.write("# Auto-generated minimal configuration\n")
            f.write("# OpenStudio and OpenStudio-HPXML paths are automatically detected\n\n")
            minimal_config.write(f)


# Global configuration instance
_config_manager = None


def get_config_manager(
    config_file=None,
    environment="prod",
    auto_create=True,
):
    """
    Get global configuration manager instance.

    Args:
        config_file: Path to configuration file
        environment: Environment profile
        auto_create: Whether to auto-create user config from template if not found

    Returns:
        ConfigManager instance
    """
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigManager(config_file, environment, auto_create)

    return _config_manager


def reset_config_manager():
    """Reset global configuration manager (useful for testing)."""
    global _config_manager
    _config_manager = None
