# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

This is the H2K-HPXML translation tool - a Canadian government project (CMHC/NRCan) that converts Hot2000 (H2K) building energy models to US DOE's HPXML format for EnergyPlus simulation. The goal is to provide sub-hourly energy analysis for Canada's 6,000+ housing archetypes.

**Project Status**: Phase 1 (loads) and Phase 2 (HVAC systems) complete. Phase 3 (multi-unit residential buildings) pending.

**Branch Strategy**: 
- `main` - Production branch for pull requests
- Feature branches - For development work

## Essential Commands

### Development Setup

#### Local Development
```bash
# Install in development mode
uv pip install -e .

# Setup configuration and dependencies
h2k-deps --setup
h2k-deps --auto-install

# Verify setup
h2k-deps --check-only
```

#### Docker Development
```bash
# Using DevContainer (recommended for VS Code users)
# Open project in VS Code and select "Reopen in Container"

# Or use Docker Compose
docker-compose --profile dev up    # Start development container
docker-compose run h2k-hpxml-dev bash    # Interactive shell

# Test Docker builds
./docker/test_container.sh         # Run comprehensive container tests
```

### Testing
```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest --run-baseline                 # Generate baseline data (WARNING: overwrites golden files)

# Run single test
pytest tests/unit/test_core_translator.py::TestH2KToHPXML::test_valid_translation_modes -v
```

### Code Quality
```bash
# Install development dependencies first
uv pip install -e ".[dev]"

# Formatting and linting
black src/ tests/                    # Auto-format code
ruff check src/ tests/               # Linting
mypy src/h2k_hpxml/core/            # Type checking (note: type hints were removed from most files)

# Run all quality checks
black --check src/ tests/ && ruff check src/ tests/ && mypy src/h2k_hpxml/core/
```

### Main CLI Tools
```bash
# H2K to HPXML conversion (single file)
h2k2hpxml input.h2k [--output output.xml]

# H2K to HPXML conversion (entire folder - parallel processing) 
h2k2hpxml /path/to/h2k/files/
# Note: Automatically uses (CPU cores - 1) threads for parallel processing

# Advanced conversion options
h2k2hpxml input.h2k --debug --hourly ALL --do-not-sim

# Show credits
h2k2hpxml --credits

# Resilience analysis
h2k-resilience input.h2k [--scenarios SCENARIOS]

# Dependency management  
h2k-deps                             # Interactive dependency management
```

## Architecture Overview

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
**Recent Change**: All type hints have been systematically removed from the codebase to eliminate 400+ Mypy errors. This includes:
- All function parameter and return type annotations removed
- All variable type annotations removed  
- `@dataclass` converted to regular classes with `__init__` methods
- `typing` imports removed from all files
- Current Mypy errors reduced to ~132 (mostly var-annotated issues)

### Configuration System
- Single configuration file: `config/conversionconfig.ini`
- Template file: `config/templates/conversionconfig.template.ini`
- Managed by `ConfigManager` class with environment variable overrides
- Key sections: `[paths]`, `[simulation]`, `[weather]`, `[logging]`

### Testing Strategy
- **Unit tests**: Component-level testing with mocked data
- **Integration tests**: Full translation pipeline with real H2K files
- **Regression tests**: Compare against baseline "golden files" 
- **Resilience tests**: CLI functionality testing
- Use `--run-baseline` flag to regenerate golden files (use with caution)

### Empty Files to Keep
- `src/h2k_hpxml/analysis/__init__.py` - Required for package structure (analysis/annual.py is imported)
- Do NOT delete empty `__init__.py` files - they're needed for Python packages

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

Managed via `h2k-deps` command which auto-detects and installs on Windows/Linux.
**Note**: Docker images have all dependencies pre-installed.

## Docker Support

### Container Architecture
The project provides comprehensive Docker support with multiple build targets:

- **Production Container** (`canmet/h2k-hpxml:latest`) - Optimized for running translations (~870MB)
- **Development Container** - Full development environment with tools (~1.3GB)
- **DevContainer** - VS Code integrated development with Docker-in-Docker support

### Quick Docker Usage
```bash
# Production usage
docker run -v $(pwd)/data:/data canmet/h2k-hpxml:latest input.h2k

# Development with Docker Compose
docker-compose --profile dev up
docker-compose run h2k-hpxml-dev bash

# Batch processing
docker-compose --profile batch run batch-convert

# VS Code DevContainer (recommended for development)
# Open project and select "Reopen in Container"
```

### Docker Files Structure
- `Dockerfile` - Multi-stage unified Dockerfile
- `docker-compose.yml` - Service definitions with profiles
- `.devcontainer/` - VS Code DevContainer configuration
- `docker/entrypoint.sh` - Container initialization script
- `docker/test_container.sh` - Comprehensive container testing
- `.github/workflows/docker-publish.yml` - CI/CD pipeline

All Docker containers include pre-installed OpenStudio and dependencies, eliminating manual setup.

## Common Issues & Troubleshooting

### Installation Issues
- **OpenStudio not found**: Run `h2k-deps --auto-install` or use Docker containers
- **Missing dependencies**: Ensure you installed with `uv pip install -e ".[dev]"` for development (or `pip install -e ".[dev]"` if not using uv)
- **Config file issues**: Check `config/conversionconfig.ini` exists in project root

### Testing Issues
- **Golden file mismatches**: Expected when output format changes. Review changes carefully before running `--run-baseline`
- **Weather file errors**: Ensure weather data is downloaded via `h2k-deps` 
- **Path issues**: Use absolute paths in configuration files

### Docker Issues
- **Permission denied**: Run `chmod +x docker/*.sh` for script permissions
- **Volume mount errors**: Ensure local directories exist before mounting
- **DevContainer issues**: Update VS Code and Docker extensions

### Development Tips
- Always run tests before committing: `pytest`
- Format code with: `black src/ tests/`
- Check for issues with: `ruff check src/ tests/`
- Use DevContainer for consistent development environment
- Review `docker/README.md` for detailed Docker usage

## Project Documentation

### Key Documentation Files
- `README.md` - Project overview and quick start guide
- `docker/README.md` - Comprehensive Docker usage guide
- `docker/CONSOLIDATION.md` - Docker implementation history
- `docs/` - Additional documentation and examples
- `CLAUDE.md` - This file (AI assistant instructions)

### Configuration Files
- `config/conversionconfig.ini` - Main configuration file
- `config/templates/conversionconfig.template.ini` - Configuration template
- `pyproject.toml` - Python project configuration
- `docker-compose.yml` - Docker service definitions
- `.devcontainer/devcontainer.json` - VS Code DevContainer settings

### Resource Files
- `resources/hpxml_template.xml` - Base HPXML template
- `resources/weather/` - Weather data files
- `resources/mapping_jsons/` - H2K to HPXML mappings
- `tests/h2k_files/` - Test H2K input files
- `tests/expected_output/` - Baseline golden files