# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

This is the H2K-HPXML translation tool - a Canadian government project (CMHC/NRCan) that converts Hot2000 (H2K) building energy models to US DOE's HPXML format for EnergyPlus simulation. The goal is to provide sub-hourly energy analysis for Canada's 6,000+ housing archetypes.

**Project Status**: Phase 1 (loads) and Phase 2 (HVAC systems) complete. Phase 3 (multi-unit residential buildings) pending.

**Branch Strategy**:
- `main` - Production branch for pull requests
- Feature branches - For development work

**Python Version**: Requires Python 3.12+

## Essential Commands

### Development Setup

#### Local Development
```bash
# Install in development mode
uv pip install -e .

# Setup configuration and dependencies
os-setup --setup
os-setup --auto-install

# Verify setup
os-setup --check-only
```

#### Docker Development
```bash
# Using DevContainer (recommended for VS Code users)
# Open project in VS Code and select "Reopen in Container"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest --run-baseline                 # Generate baseline data (WARNING: overwrites golden files)

# Run tests in parallel (faster execution)
pytest -n auto                       # Auto-detect number of CPU cores
pytest -n 4                          # Use 4 parallel workers
pytest tests/integration/test_regression.py -n auto  # Parallel regression tests only

# Generate baseline data (alternative method)
uv run python tests/utils/generate_baseline_data.py  # Direct script execution

# Clean up cache files and temporary data (cross-platform)
uv run python tools/cleanup.py              # Removes __pycache__, tool caches, temp files

# Run single test
pytest tests/unit/test_core_translator.py::TestH2KToHPXML::test_valid_translation_modes -v

# Test interactive demo (cross-platform)
python3 tests/utils/demo_test_automation.py           # Cross-platform demo test with scripted input
python3 tests/utils/demo_test_automation.py --cleanup # Clean up demo test files
pytest tests/integration/test_demo.py                 # Pytest integration tests for demo
```

### Code Quality
```bash
# Install development dependencies first
uv pip install -e ".[dev]"

# Testing
pytest                              # Run all tests
pytest tests/unit/                  # Unit tests only
pytest tests/integration/           # Integration tests only
pytest -n auto                     # Run tests in parallel (faster)
pytest -v                          # Verbose output
pytest -x                          # Stop on first failure

# Code formatting and linting
black src/ tests/                   # Format code (line length: 100)
ruff check src/ tests/              # Lint code
ruff check --fix src/ tests/        # Auto-fix linting issues
```

### Main CLI Tools
```bash
# H2K to HPXML conversion (single file)
h2k-hpxml input.h2k [--output output.xml]

# H2K to HPXML conversion (entire folder - parallel processing)
h2k-hpxml /path/to/h2k/files/
# Note: Automatically uses (CPU cores - 1) threads for parallel processing

# Advanced conversion options
h2k-hpxml input.h2k --debug --hourly ALL --do-not-sim

# Show credits
h2k-hpxml --credits

# Interactive demo (bilingual learning tool)
h2k-demo                             # Guided demo with example files
h2k-demo --lang fr                   # French version
h2k-hpxml --demo                     # Alternative demo command

# Resilience analysis
h2k-resilience input.h2k [--run-simulation] [--outage-days N] \
  [--output-path PATH] [--clothing-factor-summer F] [--clothing-factor-winter F]

# Dependency management
os-setup                             # Interactive dependency management
os-setup --check-only               # Verify setup without installing
os-setup --test-installation        # Run quick test to verify setup
```

## Architecture Overview

### Source Code Structure
```
src/h2k_hpxml/
├── cli/                    # Command-line interfaces
│   ├── convert.py         # Main h2k-hpxml CLI
│   ├── resilience.py      # h2k-resilience CLI
│   └── demo.py            # h2k-demo CLI (bilingual)
├── core/                   # Core translation engine
│   ├── translator.py      # Main h2ktohpxml() orchestration
│   ├── model.py           # ModelData class (state tracking)
│   ├── h2k_parser.py      # H2K data extraction utilities
│   ├── input_validation.py
│   ├── template_loader.py
│   ├── hpxml_assembly.py
│   └── processors/        # Translation pipeline stages
│       ├── building.py
│       ├── weather.py
│       ├── enclosure.py
│       └── systems.py
├── components/            # Individual component translators
│   ├── walls.py, windows.py, doors.py, etc.
│   └── hvac/             # HVAC system translators
├── config/               # Configuration management
│   ├── manager.py        # ConfigManager class
│   └── defaults/         # Template config files
├── resources/            # Data files and templates
│   ├── template_base.xml # Base HPXML template
│   ├── weather/          # EPW weather files
│   └── *.json           # Mapping configurations
├── analysis/             # Post-simulation analysis
│   └── annual.py
├── utils/                # Utilities and helpers
│   └── dependencies.py   # os-setup CLI
└── examples/             # Sample H2K files
```

### Translation Pipeline
The core translation follows this flow:
1. **Input Validation** (`core/input_validation.py`) - Validates H2K file and config
2. **Template Loading** (`core/template_loader.py`) - Loads base HPXML template and parses H2K XML
3. **Processing Pipeline** (`core/translator.py` orchestrates):
   - **Building Details** (`core/processors/building.py`) - Basic building info
   - **Weather Data** (`core/processors/weather.py`) - Climate file mapping
   - **Enclosure Components** (`core/processors/enclosure.py`) - Walls, windows, doors, etc.
   - **Systems & Loads** (`core/processors/systems.py`) - HVAC, DHW, lighting, appliances
4. **HPXML Assembly** (`core/hpxml_assembly.py`) - Final XML generation with mode-specific adjustments

**Performance Note**: When processing folders, the CLI uses `concurrent.futures.ThreadPoolExecutor` with (CPU cores - 1) threads to process multiple H2K files in parallel, dramatically improving batch processing performance.

### Key Modules

**Core Translation Engine**:
- `core/translator.py` - Main orchestration function `h2ktohpxml()`
- `core/model.py` - `ModelData` class for tracking building info and counters during translation
- `core/h2k_parser.py` - Utility functions for extracting data from H2K dictionaries

**Component Translation**:
- `components/` - Individual component translators (walls, windows, HVAC systems, etc.)
- Each follows pattern: extract from H2K → validate → create HPXML structure → return list of components

**Configuration & Resources**:
- `config/manager.py` - `ConfigManager` class for handling `conversionconfig.ini`
- `resources/` - Contains JSON mapping files and HPXML template
- Weather data files and mapping configurations

### Data Flow Architecture
- H2K data stored as nested dictionaries (parsed from XML)
- HPXML data built as nested dictionaries (converted to XML at end)
- `ModelData` instance passed through all processors to track state and counters
- Configuration loaded once and passed to all processors

## Important Development Notes

### Type Hints Status
The project uses selective type hints across modules. Mypy is configured with relaxed strictness in `pyproject.toml` to avoid blocking development. New code may include pragmatic annotations where they add clarity; avoid introducing type-check noise.

### Configuration System
- Single configuration file: `config/conversionconfig.ini`
- Template file: `config/defaults/conversionconfig.template.ini`
- Managed by `ConfigManager` class with environment variable overrides
- Key sections: `[paths]`, `[simulation]`, `[weather]`, `[logging]`

### Testing Strategy
- **Unit tests**: Component-level testing with mocked data
- **Integration tests**: Full translation pipeline with real H2K files
- **Regression tests**: Compare against baseline "golden files" 
- **Resilience tests**: CLI functionality testing
- Use `--run-baseline` flag to regenerate golden files (use with caution)
- Alternative: `uv run python tests/utils/generate_baseline_data.py` for direct baseline generation

### Package Structure
- Do NOT delete empty `__init__.py` files - they're required for Python package imports
- `src/h2k_hpxml/analysis/__init__.py` - Required for package structure (analysis/annual.py is imported)
- All subdirectories under `src/h2k_hpxml/` need `__init__.py` to be importable

### Weather Data Handling
- Weather files stored in `resources/weather/` and `utils/` (zip files)
- Mapping between H2K weather locations and EnergyPlus weather files
- Two vintages supported: CWEC2020 (default) and EWY2020
- Historic weather library configuration

### Common Development Patterns

When adding new component translators:
1. Follow existing component patterns in `components/`
2. Use `ModelData` methods for counters (`model_data.increment_counter("wall")`)
3. Add validation with warnings (`model_data.add_warning_message()`)
4. Return list of HPXML component dictionaries
5. Use `h2k_parser` utility functions for data extraction

When modifying core translation:
1. Update relevant processor in `core/processors/`
2. Consider impact on both SOC and ASHRAE140 translation modes
3. Test with various H2K file types (house vs. MURB)
4. Update golden files if output format changes

### Dependencies
Critical external dependencies:
- **OpenStudio SDK** (3.9.0) - Building energy modeling platform
- **OpenStudio-HPXML** (v1.9.1) - NREL's HPXML implementation 
- **EnergyPlus** - Simulation engine (managed via OpenStudio)

Managed via `os-setup` command which auto-detects and installs on Windows/Linux:

#### Windows Installation (Portable)
- **No admin rights required** - Uses portable tar.gz installation
- **Installation location**: `%LOCALAPPDATA%\OpenStudio-3.9.0`
- **Fallback location**: `%USERPROFILE%\OpenStudio` if LOCALAPPDATA not writable
- **Size**: ~500MB extracted
- **Automatic PATH setup**: Optional PowerShell command provided
- **Uninstall**: Simply delete the installation folder

#### Linux Installation
- **Ubuntu/Debian**: Downloads and installs .deb package
- **Other Linux**: Extracts tar.gz to `/usr/local/openstudio`
- **Requires sudo**: For system-wide installation

**Note**: Docker images have all dependencies pre-installed.

## Docker Support

### Container Architecture
This repository provides a VS Code DevContainer for development. There is currently no root Dockerfile in the repository for building production/development images directly.

### Quick Docker Usage
```bash
# VS Code DevContainer (recommended for development)
# Open the project in VS Code and select "Reopen in Container"
```

### Docker Files Structure
- `.devcontainer/Dockerfile` - DevContainer image definition
- `.devcontainer/devcontainer.json` - VS Code DevContainer configuration

All Docker containers include pre-installed OpenStudio and dependencies, eliminating manual setup.

## Common Issues & Troubleshooting

### Installation Issues
- **OpenStudio not found**: Run `os-setup --auto-install` or use Docker containers
  - **Windows**: Now uses portable tar.gz installation (no admin rights required)
  - **Installation location**: `%LOCALAPPDATA%\OpenStudio-3.9.0` or `%USERPROFILE%\OpenStudio`
  - **No admin privileges needed**: Portable installation extracts to user directory
- **Missing dependencies**: Ensure you installed with `uv pip install -e ".[dev]"` for development (or `pip install -e ".[dev]"` if not using uv)
- **Config file issues**: Check `config/conversionconfig.ini` exists in project root

### Testing Issues
- **Golden file mismatches**: Expected when output format changes. Review changes carefully before running `--run-baseline`
- **Weather file errors**: Ensure weather data is downloaded via `os-setup` 
- **Path issues**: Use absolute paths in configuration files

### Docker Issues
- **Volume mount errors**: Ensure local directories exist before mounting
- **DevContainer issues**: Update VS Code and Docker extensions

### Development Tips
- Always run tests before committing: `pytest`
- Format code with: `black src/ tests/` (line length: 100 characters)
- Check for issues with: `ruff check src/ tests/`
- Use DevContainer for consistent development environment (includes all dependencies)
- Review `docs/DOCKER.md` for detailed Docker usage
- macOS users: Docker is the recommended development environment (auto-install not supported)

## Project Documentation

### Key Documentation Files
- `README.md` - Project overview and quick start guide
- `docs/DOCKER.md` - Comprehensive Docker usage guide
- `docs/` - Additional documentation and examples
- `CLAUDE.md` - This file (AI assistant instructions)

### Configuration Files
- `config/conversionconfig.ini` - Main configuration file
- `config/defaults/conversionconfig.template.ini` - Configuration template
- `pyproject.toml` - Python project configuration
- `.devcontainer/devcontainer.json` - VS Code DevContainer settings

### Resource Files
- `src/h2k_hpxml/resources/template_base.xml` - Base HPXML template
- `src/h2k_hpxml/resources/weather/` - Weather data files
- `src/h2k_hpxml/resources/` - Mapping JSONs (`config_locations.json`, `config_selection.json`, `config_numeric.json`, `config_foundations.json`)
- `src/h2k_hpxml/examples/` - Example H2K input files
- `tests/fixtures/expected_outputs/` - Baseline golden files
