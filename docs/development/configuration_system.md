# H2K-HPXML Configuration System

This document describes the simplified configuration system implemented for the H2K-HPXML package.

## Overview

The configuration system uses a single configuration file approach designed for simplicity and maintainability. The complex multi-environment system has been simplified to use a single `conversionconfig.ini` file.

## Configuration File Hierarchy

The ConfigManager uses a hierarchical search to find configuration files, checking locations in priority order:

### Search Order (Highest to Lowest Priority)

1. **User Config Directory** (Recommended)
   - Linux/macOS: `~/.config/h2k_hpxml/config.ini`
   - Windows: `%APPDATA%/h2k_hpxml/config.ini`
   - Created via `os-setup --setup` or auto-created on first use

2. **Project Config Directory** (Searches up to 3 parent directories)
   - `config/conversionconfig.ini` - Standard location
   - Checked in current directory and up to 3 parent levels

3. **Legacy Location** (Backward Compatibility)
   - `conversionconfig.ini` - Project root (deprecated)

4. **Auto-Creation from Template**
   - If `auto_create=True` (default), creates user config from template
   - Template location: `config/defaults/conversionconfig.template.ini`
   - If `auto_create=False`, raises `ConfigurationError`

### Configuration File Location

The system uses configuration files in the following locations:
- **User config**: `~/.config/h2k_hpxml/config.ini` (primary)
- **Project config**: `config/conversionconfig.ini` (for development)
- **Template**: `config/defaults/conversionconfig.template.ini` (source template)

### Template-Based Auto-Creation
If no configuration is found and `auto_create=True`, the system automatically creates user configuration from the template:
- Template: `config/defaults/conversionconfig.template.ini`
- Destination: User config directory

## Environment Variable Overrides

Configuration values can be overridden using environment variables. The system parses environment variables with the prefix `H2K_` and splits on the first underscore to determine section and key.

**Format**: `H2K_SECTION_KEY=VALUE`

The parser:
1. Removes the `H2K_` prefix
2. Splits the remaining string on the first underscore `_`
3. First part becomes the section name (lowercased)
4. Second part becomes the key name (lowercased)

Examples:
```bash
# H2K_PATHS_SOURCE_H2K_PATH → section: "paths", key: "source_h2k_path"
export H2K_PATHS_SOURCE_H2K_PATH="/custom/h2k/files"

# H2K_SIMULATION_FLAGS → section: "simulation", key: "flags"
export H2K_SIMULATION_FLAGS="--add-component-loads --debug --annual-output-file-format csv"

# H2K_LOGGING_LOG_LEVEL → section: "logging", key: "log_level"
export H2K_LOGGING_LOG_LEVEL="DEBUG"

# H2K_WEATHER_WEATHER_VINTAGE → section: "weather", key: "weather_vintage"
export H2K_WEATHER_WEATHER_VINTAGE="CWEC2016"
```

## Configuration File Structure

The configuration file uses INI format with the following sections. Note that dependency paths (OpenStudio, OpenStudio-HPXML, EnergyPlus) are **NOT** stored in the config file - they are auto-detected at runtime (see [Auto-Detected Properties](#auto-detected-properties-vs-configuration-keys) section).

### Core Sections

#### [paths]
- `source_h2k_path` - Directory containing H2K files to convert (default: `examples`)
- `dest_hpxml_path` - Output directory for generated HPXML files (default: `output/hpxml/`)
- `dest_compare_data` - Output directory for comparison data (default: `output/comparisons/`)
- `workflow_temp_path` - Temporary directory for workflow files (default: `output/workflows/`)

**Note**: OpenStudio and OpenStudio-HPXML paths are automatically detected and are NOT configured here. See [Auto-Detected Properties](#auto-detected-properties-vs-configuration-keys).

#### [simulation]
- `flags` - OpenStudio-HPXML simulation flags (default: `--add-component-loads --debug`)
  - Common flags: `--add-component-loads`, `--debug`, `--annual-output-file-format csv`

#### [weather]
- `weather_library` - Weather data library (default: `historic`)
  - Options: `historic`, `future`, `custom`
- `weather_vintage` - Weather data vintage (default: `CWEC2020`)
  - Options: `CWEC2020`, `CWEC2016`, `custom`

#### [nonh2k]
- `timestep` - Simulation timestep in minutes (default: `60`)
  - Options: 60 (hourly), 30, 15, 10, 6, 5, 4, 3, 2, 1
- `operable_window_avail_days` - Days operable windows are available (default: `3`)
  - Range: 0-365, affects cooling energy calculations

#### [logging]
- `log_level` - Logging level (default: `INFO`)
  - Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `log_to_file` - Whether to write logs to file (default: `true`)
  - Boolean: true/false
- `log_file_path` - Log file path (default: `output/logs/h2k_hpxml.log`)
  - Used when `log_to_file = true`

## Auto-Detected Properties vs Configuration Keys

The ConfigManager provides auto-detected properties for dependency paths that are **NOT** stored in the configuration file. These properties dynamically detect installed dependencies at runtime.

### Auto-Detected Properties

These are accessible as properties on the ConfigManager instance but are NOT in the config file:

#### `config.openstudio_binary`
- Auto-detects OpenStudio CLI binary path
- Search order:
  1. Installed via `os-setup` (user-specific locations)
  2. System PATH (`which openstudio`)
  3. Fallback: `"openstudio"` (for error handling)
- Implementation: Calls `utils.dependencies.get_openstudio_binary()`

#### `config.hpxml_os_path`
- Auto-detects OpenStudio-HPXML installation directory
- Search locations:
  1. Environment variable: `OPENSTUDIO_HPXML_PATH`
  2. User installation paths (via `os-setup`)
  3. System-wide installations
- Implementation: Calls `utils.dependencies.get_hpxml_os_path()`

#### `config.energyplus_binary`
- Auto-detects EnergyPlus binary path
- Search order:
  1. Bundled with OpenStudio installation
  2. System PATH (`which energyplus`)
  3. Fallback: `"energyplus"` (for error handling)
- Implementation: Calls `utils.dependencies.get_energyplus_binary()`

### Why Auto-Detection?

- **Cross-platform compatibility**: Paths differ across Windows, Linux, macOS
- **Flexible installation**: Supports system-wide and user-specific installs
- **Simpler configuration**: Users don't need to manually configure dependency paths
- **Automatic updates**: When dependencies are reinstalled, paths are auto-detected

### Example Usage

```python
from h2k_hpxml.config.manager import ConfigManager

config = ConfigManager()

# These are read from config file
source_path = config.get("paths", "source_h2k_path")  # From config file
log_level = config.get("logging", "log_level")       # From config file

# These are auto-detected properties (NOT in config file)
openstudio_bin = config.openstudio_binary  # Auto-detected at runtime
hpxml_path = config.hpxml_os_path          # Auto-detected at runtime
energyplus_bin = config.energyplus_binary  # Auto-detected at runtime
```

## ConfigManager Initialization

The `ConfigManager` class is the main interface for configuration management. It provides flexible initialization options for different use cases.

### Constructor Parameters

```python
ConfigManager(
    config_file=None,
    environment="prod",
    auto_create=True
)
```

**Parameters**:
- `config_file` (str or Path, optional): Explicit path to configuration file
  - If `None`, performs hierarchical search (see [Configuration File Hierarchy](#configuration-file-hierarchy))
  - If provided, uses specified file directly (no search)

- `environment` (str, default="prod"): Environment profile name
  - Currently used for logging context
  - Future: May support environment-specific overrides

- `auto_create` (bool, default=True): Auto-create user config from template if not found
  - `True`: Creates `~/.config/h2k_hpxml/config.ini` from template automatically
  - `False`: Raises `ConfigurationError` if config not found
  - Recommended: `False` for tests, `True` for production use

### Usage Examples

#### Default Initialization (Recommended)
```python
from h2k_hpxml.config.manager import ConfigManager

# Uses hierarchical search, auto-creates if needed
config = ConfigManager()
```

#### Explicit Config File
```python
from pathlib import Path

# Use specific config file (no search)
config = ConfigManager(config_file="/path/to/custom/config.ini")
```

#### Test Environment (No Auto-Create)
```python
# For testing - don't create config files
config = ConfigManager(auto_create=False)
```

#### Development Environment
```python
# Use project config explicitly
from pathlib import Path

project_config = Path.cwd() / "config" / "conversionconfig.ini"
config = ConfigManager(config_file=project_config, environment="dev")
```

### Initialization Process

When `ConfigManager()` is instantiated:
1. **Load Configuration**
   - If `config_file` provided: Use that file
   - If `config_file=None`: Perform hierarchical search
   - If not found and `auto_create=True`: Create from template
   - If not found and `auto_create=False`: Raise `ConfigurationError`

2. **Apply Environment Overrides**
   - Parse environment variables with `H2K_` prefix
   - Override config values with environment variables

3. **Validate Configuration**
   - Check required sections exist: `[paths]`, `[simulation]`, `[weather]`, `[logging]`
   - Check required keys exist: `dest_hpxml_path`, `weather_library`, `weather_vintage`, `log_level`
   - Warn about non-existent paths (non-fatal)

4. **Ready for Use**
   - Configuration is loaded and cached
   - Auto-detected properties available
   - Environment overrides applied

## Configuration Management Commands

### Setup Commands

```bash
# Create configuration from template
os-setup --setup

# Non-interactive setup (for CI/CD)
os-setup --setup --non-interactive
```

### Update Commands

```bash
# Update dependency paths in configuration
os-setup --update-config
```

### Utility Commands

```bash
# Check dependency status only
os-setup --check-only

# Auto-install missing dependencies
os-setup --auto-install

# Interactive dependency management
os-setup
```

## Template System

The template provides a user-friendly configuration file with extensive comments explaining each setting. It is located at `config/defaults/conversionconfig.template.ini` and includes:

- Comprehensive comments for each configuration option
- Default values for all settings
- Cross-platform path examples
- Note about auto-detected dependency paths

### Template Location

The system searches for the template in the following locations:
1. `config/defaults/conversionconfig.template.ini` (project structure)
2. Searches up to 3 parent directories from current working directory
3. Falls back to creating minimal config if template not found

### Template Creation Process

When creating user configuration from the template (`os-setup --setup` or auto-creation), the system:
1. Locates the template file in `config/defaults/`
2. Copies the template to user config directory:
   - Linux/macOS: `~/.config/h2k_hpxml/config.ini`
   - Windows: `%APPDATA%/h2k_hpxml/config.ini`
3. Preserves all comments and default values
4. User can then customize paths and settings as needed

**Note**: Dependency paths (OpenStudio, HPXML) are NOT in the template - they are auto-detected at runtime.

## Cross-Platform Support

### Path Handling

- All paths are handled using `pathlib.Path` for cross-platform compatibility
- Relative paths are resolved relative to the configuration file directory
- Environment variables are expanded in path values

## Git Integration

### Project-Level Exclusions

The `.gitignore` file excludes local configuration files to prevent git noise while keeping templates in version control:

```gitignore
# Local configuration file (OS-specific paths)
config/conversionconfig.ini

# Keep defaults directory and templates in version control
!config/defaults/
!config/**/*.template.ini
```

### User Config Files

User configuration files are stored outside the project directory and are automatically excluded from version control:
- Linux/macOS: `~/.config/h2k_hpxml/config.ini`
- Windows: `%APPDATA%/h2k_hpxml/config.ini`

### What Goes in Version Control

**Included**:
- Template file: `config/defaults/conversionconfig.template.ini`
- Defaults directory: `config/defaults/`

**Excluded**:
- Project config: `config/conversionconfig.ini` (developer-specific)
- User config: `~/.config/h2k_hpxml/config.ini` (outside repo)
- Legacy config: `conversionconfig.ini` in project root (deprecated)

## Error Handling

### Missing Configuration

If no configuration is found and auto-creation is disabled:
```
ConfigurationError: Configuration file not found.
Use 'os-setup --setup' to create configuration from template.
```

### Invalid Configuration

The system validates:
- Required sections and keys
- Path existence (with warnings for missing paths)
- Boolean and integer value formats

### Dependency Detection Failures

When dependencies cannot be detected:
- User is prompted to install manually
- Configuration templates include placeholder paths
- Clear error messages guide resolution

## Simplified Design Benefits

The simplified single-file configuration approach provides:
- Reduced complexity and maintenance overhead
- Clearer configuration management
- Easier setup and deployment
- Elimination of environment-specific confusion
- Single source of truth for all settings

## Testing Considerations

### Test Isolation

Tests use `auto_create=False` to prevent configuration interference:
```python
config_manager = ConfigManager(auto_create=False)
```

### Environment Variable Testing

```python
with patch.dict(os.environ, {'H2K_PATHS_SOURCE_H2K_PATH': '/test/path'}):
    config = ConfigManager()
    assert config.get('paths', 'source_h2k_path') == '/test/path'
```

### Cross-Platform Testing

The system includes tests for:
- Path resolution and normalization
- Environment variable expansion
- Template creation and updates

## Performance Considerations

- Configuration is loaded once at startup and cached
- Template processing uses string replacement for speed
- File system operations are minimized through caching
- Environment variable lookups are performed only during initialization
