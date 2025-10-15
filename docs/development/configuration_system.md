# H2K-HPXML Configuration System

This document describes the simplified configuration system implemented for the H2K-HPXML package.

## Overview

The configuration system uses a single configuration file approach designed for simplicity and maintainability. The complex multi-environment system has been simplified to use a single `conversionconfig.ini` file.

## Configuration File Location

The system uses a single configuration file:
- `config/conversionconfig.ini` - Main configuration file

### Template-Based Auto-Creation
If no configuration is found, the system automatically creates configuration from the template:
- `config/templates/conversionconfig.template.ini`

## Environment Variable Overrides

Configuration values can be overridden using environment variables with the format:
```
H2K_<SECTION>_<KEY>=<VALUE>
```

Examples:
```bash
export H2K_PATHS_SOURCE_H2K_PATH="/custom/h2k/files"
export H2K_SIMULATION_FLAGS="--add-component-loads --debug --annual-output-file-format csv"
export H2K_LOGGING_LOG_LEVEL="DEBUG"
```

## Configuration File Structure

### Core Sections

#### [paths]
- `source_h2k_path` - Directory containing H2K files to convert
- `hpxml_os_path` - OpenStudio-HPXML installation directory (auto-detected)
- `openstudio_binary` - OpenStudio binary path (auto-detected)
- `dest_hpxml_path` - Output directory for generated HPXML files
- `dest_compare_data` - Output directory for comparison data
- `workflow_temp_path` - Temporary directory for workflow files

#### [simulation]
- `flags` - OpenStudio-HPXML simulation flags

#### [weather]
- `weather_library` - Weather data library (historic, future, custom)
- `weather_vintage` - Weather data vintage (CWEC2020, CWEC2016, custom)

#### [nonh2k]
- `timestep` - Simulation timestep in minutes (60, 30, 15, etc.)
- `operable_window_avail_days` - Days operable windows are available

#### [logging]
- `log_level` - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_to_file` - Whether to write logs to file (true/false)
- `log_file_path` - Log file path

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

The template provides a user-friendly configuration file with extensive comments explaining each setting. It is located at `config/templates/conversionconfig.template.ini` and includes:

- Comprehensive comments for each configuration option
- Auto-detection placeholders for dependency paths
- Default values for all settings
- Cross-platform path examples

When creating configuration from the template, the system:
1. Copies the template to `config/conversionconfig.ini`
2. Updates auto-detected dependency paths while preserving comments
3. Uses string replacement to maintain comment formatting

## Cross-Platform Support

### Path Handling

- All paths are handled using `pathlib.Path` for cross-platform compatibility
- Relative paths are resolved relative to the configuration file directory
- Environment variables are expanded in path values

## Git Integration

### Project-Level Exclusions

The `.gitignore` file excludes the main configuration file to prevent git noise:

```gitignore
# Local configuration file (OS-specific paths)
config/conversionconfig.ini

# Keep templates in version control
!config/templates/
!config/**/*.template.ini
```

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
