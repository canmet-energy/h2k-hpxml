# H2K-HPXML User Guide

Complete guide for using the H2K-HPXML command-line tools.

## Table of Contents

- [Installation](#installation)
- [Command Reference](#command-reference)
- [Common Workflows](#common-workflows)
- [Interactive Demo](#interactive-demo)
- [Configuration System](#configuration-system)
- [Troubleshooting](#troubleshooting)

## Installation

See the [Installation Guide](INSTALLATION.md) for detailed setup instructions.

**Supported Platforms**: Windows and Linux

## Command Reference

### h2k-hpxml - Main Conversion Tool

Convert H2K files to HPXML format with optional EnergyPlus simulation.

#### Basic Usage
```bash
# Get list of all commands. 
h2k-hpxml --help

# Convert single file (with simulation)
h2k-hpxml input.h2k

# Convert single file to specific output
h2k-hpxml input.h2k --output results/house.xml

# Convert without running simulation (faster)
h2k-hpxml input.h2k --do-not-sim

# Convert entire folder (parallel processing)
h2k-hpxml /path/to/h2k/files/
```

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


### HPXML Validation

Validate generated HPXML files against the H2K-HPXML subset schema to ensure they conform to the expected structure.

```bash
# Validate a single HPXML file
python -m h2k_hpxml.utils.hpxml_validator output.xml

# Batch validate all XML files in a directory
python -m h2k_hpxml.utils.hpxml_validator --batch output_folder/

# Recursive validation with verbose output
python -m h2k_hpxml.utils.hpxml_validator --batch output/ --recursive --verbose

# Quiet mode (only show summary)
python -m h2k_hpxml.utils.hpxml_validator --batch output/ --quiet
```

The validator checks:
- XML structure and syntax
- Required elements presence
- Data types and value ranges
- Referential integrity (e.g., windows attached to valid walls)
- HPXML v4.0 compliance

For more information about the HPXML subset schema and validation, see [docs/HPXML_SUBSET.md](HPXML_SUBSET.md).


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

# If not found, reinstall/update
uv tool uninstall h2k-hpxml
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git

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
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git
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



#### Log Files
When using `--debug`, detailed logs are written to:
- Console output (immediate feedback)
- Individual log files per conversion
- EnergyPlus simulation logs in output directories


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

- **Python API**: See [API.md](API.md) for Python library usage
- **Docker Usage**: See [DOCKER.md](DOCKER.md) for containerized processing (Unavailable until Nov 2025)
- **Development**: See [DEVELOPMENT.md](DEVELOPMENT.md) to contribute