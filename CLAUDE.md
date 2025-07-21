# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the H2K to HPXML to EnergyPlus initiative project, which translates Canadian Hot2000 (H2K) building energy models to the standardized HPXML format for simulation in EnergyPlus. The project aims to leverage Canada's 6,000+ H2K archetype database to produce sub-hourly energy usage profiles for better housing stock analysis.

## Key Development Commands

### Testing
- `pytest` - Run all tests
- `pytest tests/unit/` - Run unit tests only
- `pytest tests/integration/` - Run integration tests only
- `pytest --run-baseline` - Run baseline generation tests (WARNING: overwrites golden files)

### Translation and Simulation
- `python -m h2k_hpxml.workflows.main` - Run H2K to HPXML translation using conversionconfig.ini
- `python -m h2k_hpxml.workflows.run` - Run OpenStudio-HPXML simulation workflow
- `python -m h2k_hpxml.cli.convert <h2k_file>` - CLI tool for H2K to HPXML conversion
- `python -m h2k_hpxml.cli.resilience <h2k_file> [options]` - Resilience analysis tool

### Environment Setup
- `pip install -r requirements.txt` - Install Python dependencies
- Requires OpenStudio Python bindings and OpenStudio-HPXML at `/OpenStudio-HPXML/`

## Code Architecture

### Core Translation Module (`src/h2k_hpxml/core/`)
- **`translator.py`** - Main translation engine that converts H2K XML strings to HPXML
- **`model.py`** - Model handling and data structures

### Translation Components (`src/h2k_hpxml/components/`)
- **`enclosure/`** - Building envelope elements (walls, floors, ceilings, windows, doors, foundations)
- **`systems/`** - HVAC and building systems (heating, cooling, heat pumps, ventilation, hot water)
- **`baseloads/`** - Plug loads, lighting, and appliances
- **`program_mode/`** - Special program modes like ASHRAE 140

### Configuration
- **`conversionconfig.ini`** - Main configuration file with paths and simulation settings
- **`src/h2k_hpxml/resources/config/`** - JSON configuration files for various components
- **`src/h2k_hpxml/resources/templates/`** - Base HPXML templates (base.xml)
- **`src/h2k_hpxml/resources/weather/`** - Weather data and mappings

### Analysis Tools
- **`src/h2k_hpxml/analysis/`** - Annual energy analysis and comparison utilities
- **`src/h2k_hpxml/cli/resilience.py`** - Specialized CLI tool for building resilience analysis with 4 scenarios:
  - Power outage + normal weather
  - Power outage + extreme weather  
  - Thermal autonomy + normal weather
  - Thermal autonomy + extreme weather

### Testing Framework
- **`tests/`** - Comprehensive test suite with fixtures and golden files
- **`tests/fixtures/expected_outputs/golden_files/`** - Golden file regression testing
- **`conftest.py`** - pytest configuration with custom baseline generation options

## Important Development Notes

### Dependencies
- Project requires OpenStudio Python bindings
- OpenStudio-HPXML must be installed at `/OpenStudio-HPXML/`
- Weather files are automatically downloaded to `src/h2k_hpxml/utils/` when needed

### Translation Process
1. H2K XML files are parsed using xmltodict
2. Base HPXML template is loaded and populated
3. Building components are translated through specialized modules
4. Weather files are mapped using `h2k_weather_names.csv`
5. Output HPXML is generated for OpenStudio-HPXML workflow

### Testing Strategy
- Unit tests for individual components
- Integration tests for full translation workflow
- Golden file regression testing for energy comparison
- Baseline generation tests (protected by `--run-baseline` flag)

### Key Configuration Files
- `conversionconfig.ini` - Main configuration (paths, simulation flags, weather settings)
- `src/h2k_hpxml/resources/config/foundationconfig.json` - Foundation type mappings
- `src/h2k_hpxml/resources/config/hpxmllocations.json` - Location and weather mappings
- `src/h2k_hpxml/resources/config/selection.json` - Component selection logic

### Weather Data
- Supports both CWEC (typical) and EWY (extreme) weather files
- Historic weather library with automatic downloads
- Weather files stored in `src/h2k_hpxml/utils/` with file locking

### CLI Tools
- `python -m h2k_hpxml.cli.convert` - Basic conversion tool
- `python -m h2k_hpxml.cli.resilience` - Advanced resilience analysis with clothing factors and HVAC scenarios