# H2K-HPXML Converter

Convert Canadian H2K building energy models to HPXML format for sub-hourly EnergyPlus simulation.

## What It Does

This tool translates Hot2000 (H2K) building energy models to HPXML format, enabling sub-hourly energy analysis of Canada's 6,000+ housing archetypes. H2K provides only annual energy estimates, while HPXML/EnergyPlus delivers detailed hourly and sub-hourly data for advanced analysis of time-of-use rates, thermal storage, and electrification technologies.

👉 **[Learn more about the project background](docs/BACKGROUND.md)**

## Quick Installation (Recommended)

### 1. Install uv (fast Python package manager)

**Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
> ⚠️ **macOS Users**: Automatic dependency installation is not currently supported. Use [Docker instead](docs/DOCKER.md) for zero-setup usage.

**Windows PowerShell:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install H2K-HPXML

```bash
# Global installation (commands available everywhere)
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Setup dependencies automatically (OpenStudio, EnergyPlus)
h2k-deps --auto-install
```

### 3. Try the Interactive Demo

```bash
# Run guided demo with example files
h2k-demo

# French version
h2k-demo --lang fr
```

The demo walks you through the complete conversion process using sample H2K files.

## Basic Usage

```bash
# Convert a single H2K file
h2k-hpxml input.h2k

# Convert all H2K files in a folder (parallel processing)
h2k-hpxml /path/to/h2k/files/

# Convert without running EnergyPlus simulation
h2k-hpxml input.h2k --do-not-sim

# Get help
h2k-hpxml --help
```

## Alternative Installation Methods

### 🐳 Docker (Zero Setup)
Perfect if you don't want to install anything locally, or **required for macOS users**:
```bash
# Convert a file using Docker
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/input.h2k
```
👉 **[Complete Docker guide](docs/DOCKER.md)**

### 🐍 Python Library
For energy modellers and data scientists who want to integrate with their workflows:
```python
from h2k_hpxml import convert_h2k_file, run_full_workflow

# Simple conversion
convert_h2k_file('input.h2k', 'output.xml')

# Full workflow with simulation
results = run_full_workflow('input.h2k', simulate=True)
```
👉 **[Python library usage guide](docs/LIBRARY.md)**

## Documentation

- 📋 **[User Guide](docs/USER_GUIDE.md)** - Complete CLI usage and workflows
- 🔧 **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- 🐳 **[Docker Guide](docs/DOCKER.md)** - Docker usage and deployment
- 🐍 **[Library Guide](docs/LIBRARY.md)** - Python API for researchers
- 💻 **[Development Guide](docs/DEVELOPMENT.md)** - Contributing with VSCode
- 📚 **[All Documentation](docs/)** - Complete documentation index

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Loads, schedules, envelope | ✅ **Complete** |
| 2 | HVAC systems, all fuel types | ✅ **Complete** |
| 3 | Multi-unit residential buildings | 🔄 **Planned** |

👉 **[Current implementation status](docs/status/status.md)**

## Getting Help

- 🐛 **Issues**: [GitHub Issues](https://github.com/canmet-energy/h2k-hpxml/issues)
- 📖 **Documentation**: [docs/](docs/)
- 🚀 **Quick Test**: Run `h2k-deps --test-installation` to verify setup

## Credits & License

Developed by NRCan/CMHC for advancing Canadian building energy analysis.

```bash
# Show full credits
h2k-hpxml --credits
```