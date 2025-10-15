# H2K-HPXML User Guide

Complete guide for using the H2K-HPXML command-line tools.

## Table of Contents

- [Installation](#installation)
- [Command Reference](#command-reference)
- [Common Workflows](#common-workflows)
- [Interactive Demo](#interactive-demo)
- [Performance & Parallel Processing](#performance--parallel-processing)
- [Configuration System](#configuration-system)
- [Troubleshooting](#troubleshooting)

## Installation

See the [Installation Guide](INSTALLATION.md) for detailed setup instructions.

> 🍎 **macOS Users**: Use [Docker](DOCKER.md) instead - automatic dependency installation is not supported on macOS.

Quick start (Windows/Linux):

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux
# OR
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install H2K-HPXML globally
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Setup dependencies automatically
os-setup --auto-install

# Test installation
os-setup --test-installation
```

## Command Reference

### h2k-hpxml - Main Conversion Tool

Convert H2K files to HPXML format with optional EnergyPlus simulation.

#### Basic Usage
```bash
# Convert single file (with simulation)
h2k-hpxml input.h2k

# Convert single file to specific output
h2k-hpxml input.h2k --output results/house.xml

# Convert without running simulation (faster)
h2k-hpxml input.h2k --do-not-sim

# Convert entire folder (parallel processing)
h2k-hpxml /path/to/h2k/files/
```

#### Advanced Options
```bash
# Debug mode with verbose output
h2k-hpxml input.h2k --debug

# Generate hourly outputs for all end uses
h2k-hpxml input.h2k --hourly ALL

# Specify output format (xml, json)
h2k-hpxml input.h2k --output-format json

# Custom simulation mode
h2k-hpxml input.h2k --mode ASHRAE140

# Combine options
h2k-hpxml input.h2k --debug --hourly ALL --do-not-sim --output results/
```

#### All Options
| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o` | Output path (file or directory) | Auto-generated |
| `--do-not-sim` | Skip EnergyPlus simulation | False |
| `--debug` | Enable debug logging | False |
| `--hourly` | Hourly output types (ALL, DHW, Heating, etc.) | None |
| `--output-format` | Output format (xml, json) | xml |
| `--mode` | Translation mode (SOC, ASHRAE140) | SOC |
| `--credits` | Show credits and exit | - |
| `--help` | Show help and exit | - |

### h2k-demo - Interactive Demo

Learn the conversion process with guided examples.

```bash
# English demo
h2k-demo

# French demo
h2k-demo --lang fr

# Specify demo file
h2k-demo --file WizardHouse.h2k

# Clean up demo files after running
h2k-demo --cleanup
```

The demo includes:
- File selection from built-in examples
- Step-by-step conversion process
- Explanation of all output files
- Sample EnergyPlus results analysis

### os-setup - Dependency Management

Manage OpenStudio, EnergyPlus, and configuration.

```bash
# Interactive dependency management
os-setup

# Check current dependency status
os-setup --check-only

# Setup initial configuration
os-setup --setup

# Auto-install missing dependencies
os-setup --auto-install

# Update configuration with new paths
os-setup --update-config

# Test installation (smart auto-detection)
os-setup --test-installation

# Quick installation test
os-setup --test-quick

# Comprehensive test with actual conversion
os-setup --test-comprehensive
```

### h2k-resilience - Resilience Analysis

Analyze building performance during power outages and extreme weather.

```bash
# Basic resilience analysis
h2k-resilience input.h2k

# Run with EnergyPlus simulation
h2k-resilience input.h2k --run-simulation

# Specify outage duration
h2k-resilience input.h2k --outage-days 3

# Custom clothing factors for comfort analysis
h2k-resilience input.h2k --clothing-factor-summer 0.5 --clothing-factor-winter 1.0

# Custom output location
h2k-resilience input.h2k --output-path /path/to/results/
```

## Common Workflows

### Single File Conversion

```bash
# Quick conversion for review
h2k-hpxml house.h2k --do-not-sim

# Full analysis with hourly data
h2k-hpxml house.h2k --hourly ALL

# Debug problematic file
h2k-hpxml problem_house.h2k --debug --do-not-sim
```

### Batch Processing

```bash
# Process all H2K files in a directory
h2k-hpxml /path/to/h2k/files/

# Process with custom output directory
h2k-hpxml /path/to/h2k/files/ --output /path/to/results/

# Batch processing without simulation (much faster)
h2k-hpxml /path/to/h2k/files/ --do-not-sim

# Debug batch processing
h2k-hpxml /path/to/h2k/files/ --debug --do-not-sim
```

### Research Workflows

```bash
# Generate HPXML files for external analysis
h2k-hpxml archetype_folder/ --do-not-sim --output hpxml_files/

# Full simulation with all hourly outputs
h2k-hpxml archetype_folder/ --hourly ALL --output simulation_results/

# JSON output for data analysis
h2k-hpxml archetype_folder/ --output-format json --output json_results/
```

### Quality Assurance

```bash
# Test specific translation mode
h2k-hpxml test_house.h2k --mode ASHRAE140 --debug

# Validate dependencies before processing
os-setup --check-only && h2k-hpxml large_batch/

# Test with demo files
h2k-demo --cleanup  # Clean previous runs
h2k-demo            # Run interactive demo
```

## Interactive Demo

The interactive demo (`h2k-demo`) is the best way to learn the tool:

### Demo Features
- **File Selection**: Choose from built-in example H2K files
- **Guided Process**: Step-by-step explanation of each conversion stage
- **Live Output**: See real conversion results with explanations
- **File Explorer**: Browse all generated output files with descriptions
- **Bilingual Support**: Available in English and French

### Demo Workflow
1. **Language Selection**: Choose English or French interface
2. **File Selection**: Pick from example H2K files (WizardHouse, TownHouse, etc.)
3. **Options Selection**: Choose simulation options (basic or advanced)
4. **Live Conversion**: Watch the conversion process with real-time feedback
5. **Results Review**: Explore all output files with detailed explanations

### Example Demo Session
```bash
$ h2k-demo

🏠 H2K-HPXML Interactive Demo

Select language / Sélectionnez la langue:
1. English
2. Français
Choice: 1

Available example files:
1. WizardHouse.h2k - Simple single-family home
2. TownHouse.h2k - Multi-story townhouse
3. Apartment.h2k - Apartment unit
Choice: 1

Conversion options:
1. Basic conversion (HPXML only, no simulation)
2. Full conversion with EnergyPlus simulation
3. Advanced with hourly outputs
Choice: 2

🔄 Converting WizardHouse.h2k...
✅ HPXML generated: WizardHouse.xml
✅ EnergyPlus simulation completed
✅ Results saved to: WizardHouse_results/

📊 Generated files:
📁 WizardHouse_results/
├── 📄 WizardHouse.xml          - HPXML building model
├── 📄 eplusout.sql            - EnergyPlus simulation database
├── 📄 eplusout.html           - Simulation summary report
├── 📄 annual_energy.json      - Annual energy summary
└── 📄 run.log                 - Detailed simulation log

Demo completed! Files saved in current directory.
```

## Performance & Parallel Processing

### Automatic Parallel Processing

H2K-HPXML automatically uses parallel processing for folder inputs:

```bash
# Automatically uses (CPU cores - 1) threads
h2k-hpxml /path/to/100_h2k_files/

# Monitor system resources during processing
htop  # Linux/Mac
# or Task Manager on Windows
```

### Performance Optimization

**For Large Batches:**
```bash
# Skip simulation for HPXML-only generation (10x faster)
h2k-hpxml large_batch/ --do-not-sim

# Use JSON output to reduce file I/O
h2k-hpxml large_batch/ --output-format json

# Combine for maximum speed
h2k-hpxml large_batch/ --do-not-sim --output-format json
```

**System Requirements:**
- **RAM**: 2GB minimum, 8GB+ recommended for large batches
- **Storage**: ~50MB per file with simulation, ~1MB without
- **CPU**: Multi-core systems benefit from parallel processing

**Performance Tips:**
- Use SSDs for better I/O performance
- Close other applications during large batch processing
- Use `--do-not-sim` for HPXML generation only
- Monitor system resources to avoid overwhelming the system

See the [Performance Guide](PERFORMANCE.md) for detailed optimization strategies.

## Configuration System

H2K-HPXML uses a single configuration file: `config/conversionconfig.ini`

### Configuration Sections

#### [paths] - File Locations
```ini
[paths]
openstudio_binary = /path/to/openstudio
energyplus_binary = /path/to/energyplus
hpxml_os_path = /path/to/openstudio-hpxml
```

#### [simulation] - Simulation Settings
```ini
[simulation]
default_mode = SOC
run_simulation = true
timesteps_per_hour = 4
```

#### [weather] - Weather Data
```ini
[weather]
vintage = CWEC2020
library_path = /path/to/weather/files
```

#### [logging] - Debug Settings
```ini
[logging]
level = INFO
debug_mode = false
```

### Configuration Commands

```bash
# View current configuration
os-setup --check-only

# Create initial configuration from template
os-setup --setup

# Update configuration with auto-detected paths
os-setup --update-config

# Reset to defaults
rm config/conversionconfig.ini
os-setup --setup
```

### Environment Variable Overrides

Configuration can be overridden with environment variables:

```bash
# Override OpenStudio path
export H2K_OPENSTUDIO_BINARY=/custom/path/to/openstudio
h2k-hpxml input.h2k

# Override simulation mode
export H2K_SIMULATION_MODE=ASHRAE140
h2k-hpxml input.h2k
```

## Troubleshooting

### Common Issues

#### "OpenStudio not found"
```bash
# Check current status
os-setup --check-only

# Auto-install OpenStudio
os-setup --auto-install

# Manual path configuration
os-setup --setup
```

#### "Command not found: h2k-hpxml"
```bash
# If using uv tool install
which h2k-hpxml  # Should show path

# If not found, reinstall
uv tool uninstall h2k-hpxml
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Alternative: use Python module syntax
python -m h2k_hpxml.cli.convert input.h2k
```

#### "Conversion failed"
```bash
# Run with debug mode
h2k-hpxml problematic_file.h2k --debug

# Check file format
file problematic_file.h2k  # Should show XML data

# Test with demo files first
h2k-demo
```

#### "No module named 'h2k_hpxml'"
```bash
# Check Python environment
python -c "import h2k_hpxml; print('OK')"

# Reinstall package
uv tool uninstall h2k-hpxml
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

### Getting Help

#### Built-in Help
```bash
# Command help
h2k-hpxml --help
os-setup --help
h2k-demo --help
h2k-resilience --help

# Show version and credits
h2k-hpxml --credits
```

#### Test Commands
```bash
# Quick installation test
os-setup --test-quick

# Comprehensive test including actual conversion
os-setup --test-comprehensive

# Smart test (auto-detects uv vs pip)
os-setup --test-installation
```

#### Debug Information
```bash
# System information
uv --version  # or python --version
which h2k-hpxml
os-setup --check-only

# Configuration file location
ls -la config/conversionconfig.ini

# Dependency paths
os-setup --check-only | grep "✅"
```

#### Log Files
When using `--debug`, detailed logs are written to:
- Console output (immediate feedback)
- Individual log files per conversion
- EnergyPlus simulation logs in output directories

### Performance Issues

#### Slow Conversion
```bash
# Skip simulation for faster processing
h2k-hpxml input.h2k --do-not-sim

# Check system resources
top  # Linux/Mac
# or Task Manager on Windows

# Process smaller batches
h2k-hpxml batch_part1/ && h2k-hpxml batch_part2/
```

#### Memory Issues
```bash
# Process files individually instead of batch
for file in *.h2k; do h2k-hpxml "$file"; done

# Close other applications
# Restart computer if necessary
```

### Getting Support

If you continue to experience issues:

1. **Check Documentation**: [docs/](../)
2. **Run Diagnostics**: `os-setup --test-comprehensive`
3. **Report Issues**: [GitHub Issues](https://github.com/canmet-energy/h2k-hpxml/issues)

When reporting issues, include:
- Operating system and version
- Python version (`python --version`)
- H2K-HPXML version (`h2k-hpxml --credits`)
- Complete error output
- Example H2K file (if possible)

## Next Steps

Once you're comfortable with the CLI tools:

- **Advanced Usage**: See [LIBRARY.md](LIBRARY.md) for Python API
- **Docker Usage**: See [DOCKER.md](DOCKER.md) for containerized processing
- **Development**: See [DEVELOPMENT.md](DEVELOPMENT.md) to contribute
- **Performance**: See [PERFORMANCE.md](PERFORMANCE.md) for optimization