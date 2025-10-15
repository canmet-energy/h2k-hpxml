# H2K-HPXML Documentation

Welcome to the complete documentation for H2K-HPXML, the Canadian tool for converting Hot2000 (H2K) building energy models to HPXML format for EnergyPlus simulation.

## 🚀 Getting Started

New to H2K-HPXML? Start here:

- **[Installation Guide](INSTALLATION.md)** - Complete setup instructions for all platforms
- **[User Guide](USER_GUIDE.md)** - Command-line usage and workflows
- **[Interactive Demo](#try-the-demo)** - Learn with built-in examples

### Try the Demo

The quickest way to learn H2K-HPXML:

```bash
# Install and run demo
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
h2k-demo
```

The interactive demo guides you through the complete conversion process with real examples.

## 📚 Documentation by Audience

### 🔧 **End Users** (Building Analysts, Energy Modellers)
- **[Installation Guide](INSTALLATION.md)** - Setup for Windows, Linux (macOS: use Docker)
- **[User Guide](USER_GUIDE.md)** - Complete CLI usage guide
- **[Docker Guide](DOCKER.md)** - Zero-installation usage (required for macOS)
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

### 🐍 **Python Developers** (Data Scientists, Researchers)
- **[Library Guide](LIBRARY.md)** - Python API for research workflows
- **[API Reference](API.md)** - Complete function documentation
- **[Examples](LIBRARY.md#examples-and-use-cases)** - Research workflow examples

### 💻 **Contributors** (Software Developers)
- **[Development Guide](DEVELOPMENT.md)** - VSCode-centered development
- **[Architecture](#project-architecture)** - System design overview
- **[Contributing](#contributing)** - How to contribute code

### 🐳 **DevOps/IT** (System Administrators)
- **[Docker Guide](DOCKER.md)** - Containerized deployment
- **[CI/CD Integration](DOCKER.md#cicd-integration)** - Automated workflows
- **[Performance Guide](PERFORMANCE.md)** - Optimization strategies

## 📖 Core Documentation

### Installation & Setup
- **[Installation Guide](INSTALLATION.md)** - Comprehensive setup guide
  - Quick start with uv (Windows, Linux)
  - Platform-specific instructions
  - macOS: Docker required (no automatic dependency support)
  - Dependency management with os-setup
  - Installation verification and testing
  - Troubleshooting common issues

### Usage Guides
- **[User Guide](USER_GUIDE.md)** - Complete CLI reference
  - Command reference (h2k-hpxml, h2k-demo, os-setup, h2k-resilience)
  - Common workflows and examples
  - Performance optimization with parallel processing
  - Configuration system
  - Interactive demo walkthrough

- **[Library Guide](LIBRARY.md)** - Python API for researchers
  - Installation for data analysis projects
  - Core API functions
  - Batch processing workflows
  - Integration with pandas, numpy, matplotlib
  - Research examples and use cases

- **[Docker Guide](DOCKER.md)** - Containerized usage
  - Quick start with Docker
  - Platform-specific Docker setup
  - Docker Compose for batch processing
  - CI/CD integration examples
  - Performance optimization

### Technical References
- **[API Reference](API.md)** - Complete Python API documentation
  - Function signatures and parameters
  - Return types and error handling
  - Type definitions
  - Usage examples for every function

- **[Development Guide](DEVELOPMENT.md)** - Contributing with VSCode
  - DevContainer setup (recommended)
  - Project architecture overview
  - Testing strategy and tools
  - Code quality standards
  - Debugging and troubleshooting

### Project Information
- **[Background](BACKGROUND.md)** - Project history and goals
  - Project overview and motivation
  - Technical approach and benefits
  - Development roadmap and status
  - Research applications and impact

- **[Performance Guide](PERFORMANCE.md)** - Optimization strategies
  - Parallel processing configuration
  - Memory management
  - Batch processing best practices
  - System requirements and tuning

## 📊 Project Status

| Component | Status | Documentation |
|-----------|--------|---------------|
| **Phase 1: Loads** | ✅ Complete | [Status](status/status.md) |
| **Phase 2: HVAC Systems** | ✅ Complete | [Report](reports/H2k-HPXML-Systems-Report.pdf) |
| **Phase 3: Multi-Unit Buildings** | 🔄 Planned | TBD |

### Current Capabilities
- ✅ Building envelope (walls, windows, doors, foundations)
- ✅ All HVAC system types (heating, cooling, ventilation)
- ✅ Domestic hot water systems
- ✅ Lighting and plug loads
- ✅ Weather data mapping (Canadian → US weather files)
- ✅ Both translation modes (SOC and ASHRAE140)
- ✅ Parallel processing for batch operations
- ✅ Comprehensive error handling and validation

## 🔧 Quick Reference

### Essential Commands

```bash
# Installation (recommended method)
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
os-setup --auto-install

# Basic usage
h2k-hpxml input.h2k                    # Convert single file
h2k-hpxml folder/                      # Convert all files in folder
h2k-demo                              # Interactive learning demo

# Testing and verification
os-setup --test-installation          # Verify setup
os-setup --check-only                 # Check dependencies

# Advanced usage
h2k-hpxml input.h2k --hourly ALL      # Generate hourly outputs
h2k-resilience input.h2k              # Resilience analysis
```

### Docker Quick Start

```bash
# Zero installation - use Docker
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/input.h2k

# Batch processing with Docker
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/
```

### Python API Quick Start

```python
from h2k_hpxml.api import convert_h2k_file, run_full_workflow

# Simple conversion
output = convert_h2k_file('input.h2k')

# Full workflow with simulation
results = run_full_workflow('input.h2k', simulate=True)
```

## 🔍 Detailed Status & Features

### Implementation Status
- **[Current Status](status/status.md)** - Detailed feature completion matrix
- **[Assumptions](status/assumptions.md)** - Translation assumptions and limitations
- **[Known Issues](status/issues.md)** - Current limitations and workarounds

### Technical Reports
- **[Systems Report](reports/H2k-HPXML-Systems-Report.pdf)** - HVAC systems validation
- **[Presentations](presentations/)** - Research presentations and results

## 🏗️ Project Architecture

### High-Level Architecture

```
H2K File → XML Parser → Translation Engine → HPXML Assembly → EnergyPlus Simulation
    ↓           ↓              ↓                ↓                ↓
Input         H2K Dict    Component         HPXML Dict      Energy Results
Validation    Parsing     Processors        Generation      & Reports
```

### Core Components

- **Translation Engine** (`core/translator.py`) - Main orchestration
- **Component Processors** (`components/`) - Individual building system translators
- **Configuration System** (`config/manager.py`) - Settings management
- **CLI Tools** (`cli/`) - Command-line interfaces
- **API Layer** (`api/`) - Python library interface

### Key Design Principles

- **Modular Architecture** - Each building component has its own translator
- **Configuration-Driven** - Single configuration file for all settings
- **Error Resilience** - Comprehensive validation and error handling
- **Performance Optimized** - Parallel processing for batch operations
- **Extensible** - Easy to add new component types and features

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution | Documentation |
|-------|----------|---------------|
| "Command not found" | Check installation method | [Installation](INSTALLATION.md#troubleshooting) |
| "OpenStudio not found" | Run `os-setup --auto-install` | [User Guide](USER_GUIDE.md#troubleshooting) |
| Conversion failures | Use `--debug` flag | [User Guide](USER_GUIDE.md#debugging) |
| Performance issues | Enable parallel processing | [Performance](PERFORMANCE.md) |
| Memory errors | Process smaller batches | [Library Guide](LIBRARY.md#performance-optimization) |

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
- **Read**: [Development Guide](DEVELOPMENT.md) for complete setup
- **Quick Start**: Use VSCode DevContainer for instant development environment
- **Follow Standards**: Code style, testing, and documentation requirements
- **Submit PRs**: Follow the contribution workflow

### Development Quick Start

```bash
# 1. Clone repository
git clone https://github.com/canmet-energy/h2k-hpxml.git
cd h2k-hpxml

# 2. Open in VSCode
code .

# 3. Reopen in DevContainer (when prompted)
# Everything is now configured!

# 4. Run tests
pytest tests/unit/
```

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
- 🏃‍♂️ **Quick Start**: [Installation Guide](INSTALLATION.md)
- 🎓 **Learn**: Run `h2k-demo` for interactive tutorial
- 🐍 **Develop**: [Python Library Guide](LIBRARY.md)
- 🐳 **Deploy**: [Docker Guide](DOCKER.md)
- 💻 **Contribute**: [Development Guide](DEVELOPMENT.md)