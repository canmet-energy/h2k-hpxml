# H2K-HPXML Documentation

Welcome to the complete documentation for H2K-HPXML, the Canadian tool for converting Hot2000 (H2K) building energy models to HPXML format for EnergyPlus simulation.

## 📜[Background](docs/BACKGROUND.md)

## 📊 Project Status

| Component | Status | Documentation |
|-----------|--------|---------------|
| **Phase 1: Loads** | ✅ Complete | [Status](docs/status/status.md) |
| **Phase 2: HVAC Systems** | ✅ Complete | [Report](docs/reports/H2k-HPXML-Systems-Report.pdf) |
| **Phase 3: Multi-Unit Buildings** | 🔄 Planned | TBD |

## Current Capabilities
- ✅ Single zone simulation to mimic Hot2000 approach for validation. 
- ✅ Building envelope (walls, windows, doors, foundations)
- ✅ All HVAC system types (heating, cooling, ventilation)
- ✅ Domestic hot water systems
- ✅ Lighting and plug loads
- ✅ Weather data mapping (Canadian → US weather files)
- ✅ Both translation modes (SOC and ASHRAE140)
- ✅ Parallel processing for batch operations
- ✅ Comprehensive error handling and validation


## 🚀 Getting Started

New to H2K-HPXML? Start here:

- **[Installation Guide](docs/INSTALLATION.md)** - Complete setup instructions for all platforms
- **[User Guide](docs/USER_GUIDE.md)** - Command-line usage and workflows
- **[Interactive Demo](#try-the-demo)** - Learn with built-in examples

### Try the Demo

The quickest way to learn H2K-HPXML:

```bash
# Install and run demo
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
h2k-demo
```

The interactive demo guides you through the complete conversion process with real examples.

## 🎯 Basic Usage

### Convert and Simulate (Default Behavior)

By default, h2k-hpxml converts H2K files to HPXML and **automatically runs EnergyPlus simulations**:

```bash
# Convert single file and run simulation
h2k-hpxml input.h2k
# Creates: output/input.xml (HPXML file)
#          output/results_annual.csv (annual results)
#          output/results_*.csv (detailed outputs)

# Convert entire folder (parallel processing)
h2k-hpxml /path/to/h2k/files/
# Automatically uses (CPU cores - 1) threads for faster processing
```

### Simulation with Detailed Outputs

Generate hourly, daily, or monthly timeseries data:

```bash
# Generate all hourly outputs
h2k-hpxml input.h2k --hourly ALL

# Generate specific hourly outputs (total energy, fuels breakdown)
h2k-hpxml input.h2k --hourly total --hourly fuels

# Generate monthly outputs with debug information
h2k-hpxml input.h2k --monthly ALL --debug

# Custom output format (JSON instead of CSV)
h2k-hpxml input.h2k --output-format json
```

### Conversion Only (No Simulation)

If you only need the HPXML file without running simulations:

```bash
# Convert without simulation
h2k-hpxml input.h2k --do-not-sim

# Useful for validation or when you'll run simulations separately
```

### Output Files

After running with simulation, you'll find these files in the `output/` folder:

```
output/
├── input.xml                    # Generated HPXML file
├── results_annual.csv           # Annual energy summary
├── results_timeseries_*.csv     # Hourly/monthly data (if requested)
└── run.log                      # Detailed simulation log
```

## 📚 Documentation by Audience

### 🔧 **End Users** (Building Analysts, Energy Modellers)
- **[Installation Guide](docs/INSTALLATION.md)** - Setup for Windows, Linux 
- **[User Guide](docs/USER_GUIDE.md)** - Complete CLI usage guide
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

### 🐍 **Python Developers** (Data Scientists, Researchers)
- **[API Reference](docs/API.md)** - Complete Python API documentation
- **[Examples](docs/API.md#examples)** - Usage examples and patterns

### 💻 **Contributors** (Software Developers)
- **[Development Guide](docs/DEVELOPMENT.md)** - VSCode-centered development
- **[Contributing](#contributing)** - How to contribute code

### 🐳 **DevOps/IT** (System Administrators)
- **[Docker Guide](docs/DOCKER.md)** - Containerized deployment
- **[CI/CD Integration](docs/DOCKER.md#cicd-integration)** - Automated workflows

## 📖 Core Documentation

### Installation & Setup
- **[Installation Guide](docs/INSTALLATION.md)** - Comprehensive setup guide
  - Quick start with uv (Windows, Linux)
  - Platform-specific instructions
  - Dependency management with os-setup
  - Installation verification and testing
  - Troubleshooting common issues

### Usage Guides
- **[User Guide](docs/USER_GUIDE.md)** - Complete CLI reference
  - Command reference (h2k-hpxml, h2k-demo, os-setup, h2k-resilience)
  - Common workflows and examples
  - Configuration system
  - Interactive demo walkthrough

- **[Docker Guide](docs/DOCKER.md)** - Containerized usage
  - Quick start with Docker
  - Platform-specific Docker setup
  - Docker Compose for batch processing
  - CI/CD integration examples

### Technical References
- **[API Reference](docs/API.md)** - Complete Python API documentation
  - Function signatures and parameters
  - Return types and error handling
  - Type definitions
  - Usage examples for every function

- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing with VSCode
  - DevContainer setup (recommended)
  - Project architecture overview
  - Testing strategy and tools
  - Code quality standards
  - Debugging and troubleshooting

## 🔧 Quick Reference

### Essential Commands

```bash
# Installation (recommended method)
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
os-setup --auto-install

# Help information
h2k-hpxml --help
# Basic usage (runs simulations by default)
h2k-hpxml input.h2k                    # Convert and simulate single file
h2k-hpxml folder/                      # Convert and simulate all files in folder
h2k-demo                               # Interactive learning demo

# Testing and verification
os-setup --test-installation           # Verify setup
os-setup --check-only                  # Check dependencies

# Advanced usage
h2k-hpxml input.h2k --hourly ALL       # Simulate with hourly outputs
h2k-hpxml input.h2k --do-not-sim       # Convert only (skip simulation)
h2k-resilience input.h2k               # Resilience analysis
```

### Docker Quick Start

```bash
# Zero installation - convert and simulate using Docker
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/input.h2k

# Batch processing with Docker (parallel simulation of all files)
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/

# Generate hourly outputs with Docker
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/input.h2k --hourly ALL
```

### Python API Quick Start

```python
from h2k_hpxml.api import convert_h2k_file, run_full_workflow

# Simple conversion (HPXML file only, no simulation)
hpxml_path = convert_h2k_file('input.h2k', 'output.xml')
print(f"HPXML file created: {hpxml_path}")

# Full workflow with simulation (conversion + EnergyPlus simulation)
results = run_full_workflow('input.h2k', simulate=True)
print(f"Successfully converted {results['successful_conversions']} file(s)")
print(f"Output files: {', '.join(results['converted_files'])}")
```

## 🔍 Detailed Status & Features

### Implementation Status
- **[Current Status](docs/status/status.md)** - Detailed feature completion matrix
- **[Assumptions](docs/status/assumptions.md)** - Translation assumptions and limitations
- **[Known Issues](docs/status/issues.md)** - Current limitations and workarounds

### Technical Reports
- **[Systems Report](docs/reports/H2k-HPXML-Systems-Report.pdf)** - HVAC systems validation
- **[Presentations](docs/presentations/)** - Research presentations and results

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution | Documentation |
|-------|----------|---------------|
| "Command not found" | Check installation method | [Installation](docs/INSTALLATION.md#troubleshooting) |
| "OpenStudio not found" | Run `os-setup --auto-install` | [User Guide](docs/USER_GUIDE.md#troubleshooting) |
| Conversion failures | Use `--debug` flag | [User Guide](docs/USER_GUIDE.md#debugging) |

### Getting Help

1. **Check Documentation**: Use the guides above for your use case
2. **Run Diagnostics**: `os-setup --test-comprehensive`
3. **Search Issues**: [GitHub Issues](https://github.com/canmet-energy/h2k-hpxml/issues)
4. **Report Problems**: Include OS, Python version, error output

### Debug Commands

```bash
# Test complete installation
os-setup --test-comprehensive

# Debug conversion issues
h2k-hpxml problematic.h2k --debug --do-not-sim

# Check system status
os-setup --check-only
python -c "import h2k_hpxml; print('Package OK')"
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### For Users
- **Report Issues**: [GitHub Issues](https://github.com/canmet-energy/h2k-hpxml/issues)
- **Request Features**: Describe your use case and requirements
- **Share Examples**: Help improve documentation with real-world examples

### For Developers
- **Read**: [Development Guide](docs/DEVELOPMENT.md) for complete setup
- **Quick Start**: Use VSCode DevContainer for instant development environment
- **Follow Standards**: Code style, testing, and documentation requirements
- **Submit PRs**: Follow the contribution workflow



## 📞 Support & Community

### Official Resources
- **GitHub Repository**: [canmet-energy/h2k-hpxml](https://github.com/canmet-energy/h2k-hpxml)
- **Issue Tracker**: [GitHub Issues](https://github.com/canmet-energy/h2k-hpxml/issues)
- **Releases**: [GitHub Releases](https://github.com/canmet-energy/h2k-hpxml/releases)

### Related Projects
- **OpenStudio**: [OpenStudio Documentation](https://openstudio.net/)
- **OpenStudio-HPXML**: [NREL/OpenStudio-HPXML](https://github.com/NREL/OpenStudio-HPXML)
- **HPXML Standard**: [HPXML Guide](https://hpxml-guide.readthedocs.io/)

### Citing This Work

If you use H2K-HPXML in your research, please cite:

```
NRCan/CMHC H2K-HPXML Translation Tool
Canada Mortgage and Housing Corporation and Natural Resources Canada
https://github.com/canmet-energy/h2k-hpxml
```

## 📄 License & Credits

This project is developed by Natural Resources Canada (NRCan) and Canada Mortgage and Housing Corporation (CMHC) to advance Canadian building energy analysis capabilities.

```bash
# Show detailed credits
h2k-hpxml --credits
```

---

**Ready to get started?** Choose your path:
- 🏃‍♂️ **Quick Start**: [Installation Guide](docs/INSTALLATION.md)
- 🎓 **Learn**: Run `h2k-demo` for interactive tutorial
- 🐍 **Python API**: [API Reference](docs/API.md)
- 🐳 **Deploy**: [Docker Guide](docs/DOCKER.md)
- 💻 **Contribute**: [Development Guide](docs/DEVELOPMENT.md)