# H2K -> HPXML -> EnergyPlus Initiative

## Table of Contents
- [Background](#background)
- [Why use HPXML?](#why-use-hpxml)
- [Roadmap](#roadmap)
- [Installation & Setup](#installation--setup)
  - [Quick Start](#quick-start-uv-install)
  - [Configuration System](#configuration-system)
- [Usage](#usage)
  - [Command Line Tools](#command-line-tools)
  - [Performance & Parallel Processing](#performance-and-parallel-processing)
  - [Docker Usage](#docker-usage-recommended-for-easy-setup)
- [Development Environment](#development-environment)
- [Contributing](#contributing)
- [Full Documentation](#full-documentation)

## Background

NRCan/CMHC is investigating energy use in Canada's existing housing stock and exploring policy measures to enhance energy efficiency and affordability for Canadians. The primary tool used to evaluate building energy performance in Canada is NRCan's Hot2000 (H2K) software. H2K is a building energy simulator that estimates the annual energy consumption of homes across Canada. NRCan has also developed a comprehensive database of archetypes representing housing across the country, using over 30 years of data from the EnerGuide for housing program. This location-specific database includes more than 6,000 archetypes, each reflecting regional housing characteristics.

However, H2K has some limitations, including the inability to provide hourly energy data.  H2K only produces annual energy estimates. This lack of hourly resolution restricts its capacity to support analyses of modern energy conservation measures, such as thermal and electrical storage technologies, renewable energy, advanced building automation, and other innovative solutions. Furthermore, H2K cannot assess the effects of time-of-use (TOU) electricity rates or peak demand on housing affordability.

In contrast, the software created by the U.S. Department of Energy (U.S. DOE), EnergyPlus/HPXML, provides high resolution sub-hourly outputs.  EnergyPlus/HPXML was developed in 2001 to be the standard simulation tool used by the U.S. DOE to support housing and building energy analysis.  Over $3M is annually invested in EnergyPlus/HPXML to support R&D, as well as national programs.  It provides detailed simulation information at a sub-hourly resolution that can examine time-of-use (TOU) technologies and help examine evaluate several advanced energy conservation measures.

The goal of this work is to leverage the 6000 H2K archetype model data, by translating them to EnergyPlus/HPXML. These new models will then produce sub-hourly natural gas and electricity usage profiles to better analyze the Canadian housing stock. This will create an unprecedented level of information on how these homes consume electricity and natural gas on a sub hourly basis.  It can also provide estimates on the hourly temperatures these homes experience in extreme weather events.

This data could be used to better understand thermal safety measures (overheating) that could be applied to existing and new homes.  The affordability of different HVAC systems combined with TOU electricity rates could show what are the most cost-effective systems based on TOU electric utility rates.  It could also be used to explore new technologies such as energy storage to support electrification. This and other analyses are possible and open up a door to a wealth of analysis for housing down the road.

## Why use HPXML?
HPXML, or Home Performance eXtensible Markup Language, is a standardized data format designed for the residential energy efficiency industry. It enables consistent data collection, sharing, and analysis across different software systems, tools, and stakeholders involved in home energy performance. Developed by the Building Performance Institute (BPI) and managed by the National Renewable Energy Laboratory (NREL), HPXML provides a common structure for information about home energy audits, improvements, and performance metrics. By using HPXML, organizations can streamline processes, improve data accuracy, and easily integrate with energy efficiency programs, certifications, and incentives. More information on the HPXML standard can be found [here](https://hpxml-guide.readthedocs.io/en/latest/overview.html)

## Roadmap
The overall goal of this project is to have full support of all H2K features translated to OS/EnergyPlus via HPXML format. We have taken an incremental approach to release the translator as we add functionality. This allows researchers and stakeholders to use, and evaluate the translation capabilities as we develop them.

The timeline is as follows:

| Phase | Description | Target Completion Date | Status |  |
|---|---|---|---|---|
| 1 | Loads Translations. This includes schedules, occupancy, plug loads, envelope characteristics & climate file mapping. Default fixed HVAC  |Summer 2024| Completed & available for use. Presentation comparing results available [here](docs/presentations/H2k-HPXML-20240214-V2.pdf)|
| 2 | HVAC Systems. This includes all systems and fuel types.|Spring 2025| Completed - Beta Testing. Report and presentation comparing results available [here](docs/reports/H2k-HPXML-Systems-Report.pdf) and [here](docs/presentations/H2k-HPXML-EPlus-Systems-Update-20250326.pdf)|
| 3 | Multi-Urban Residential Buildings | TBD | Not Started |

**Note**: Versioning of components targeted for each OS SDK is kept [here](https://github.com/canmet-energy/model-dev-container/blob/main/versioning.md). This will keep the development and results consistent across development as we upgrade components.

Here is a [list](docs/status/status.md) of the current completed sections related to the HPXML standard. This is a list of the assumptions and issues that were found in the translation work.

## Installation & Setup

### Quick Start: uv Install

**uv** is a fast Python package installer and resolver (10-100x faster than pip). It also manages Python versions automatically.

#### Windows 11 Installation

1. **Install uv** (Python package manager):
   ```powershell
   # Open PowerShell as Administrator and run:
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Create and activate a virtual environment** (uv automatically installs Python 3.12+ if needed):
   ```powershell
   # Create environment with correct Python version
   uv venv h2k-env --python 3.12
   
   # Activate it (commands will be added to PATH)
   h2k-env\Scripts\activate
   ```

3. **Install the package**:
   ```powershell
   uv pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
   ```

4. **Setup dependencies and PATH** (automatic):
   ```powershell
   # This will check/install dependencies and automatically set up PATH
   h2k-deps
   ```

   The setup will:
   - ✅ Install missing OpenStudio/OpenStudio-HPXML dependencies
   - ✅ Automatically add h2k2hpxml to your Windows PATH
   - 🧹 Remove any old h2k2hpxml PATH entries (from previous installations)
   - 📢 Inform you when PATH has been updated

   **Manual PATH setup (if needed):**
   ```powershell
   h2k-deps --add-to-path  # Manually clean up and add to PATH
   ```

   **⚠️ IMPORTANT**: After setup, **start a new terminal session** for PATH changes to take effect.

   **Complete workflow example:**
   ```powershell
   # 1. Install and setup
   uv pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
   h2k-deps

   # 2. CLOSE this terminal and open a NEW one

   # 3. Test that it works
   h2k2hpxml --help        # Should work from any directory
   h2k2hpxml --demo        # Run the interactive demo
   ```

#### Linux/Mac Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create and activate a virtual environment** (uv automatically installs Python 3.12+ if needed):
   ```bash
   # Create environment with correct Python version
   uv venv h2k-env --python 3.12
   
   # Activate it (commands will be added to PATH)
   source h2k-env/bin/activate
   ```

3. **Install the package**:
   ```bash
   uv pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
   ```

#### Alternative: Global Installation (Advanced Users)

For system-wide installation where commands are available everywhere:

```bash
# Install globally (use with caution - may conflict with other packages)
uv pip install --system git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

#### Alternative: Traditional pip Installation

If you prefer using pip instead of uv:

**Windows:**
```powershell
python -m venv h2k-env
h2k-env\Scripts\activate
pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

**Linux/Mac:**
```bash
python -m venv h2k-env
source h2k-env/bin/activate
pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

#### Common Setup Steps (All Platforms)

1. **Initial setup** (creates user configuration with auto-detected dependencies):
   ```bash
   h2k-deps --setup
   ```

2. **Verify installation**:
   ```bash
   h2k-deps --check-only
   ```

3. **Convert your first H2K file**:
   
   **Windows:**
   ```powershell
   # Single file
   h2k2hpxml C:\path\to\your\file.h2k
   
   # Or entire folder (processes all .h2k files in parallel)
   h2k2hpxml C:\path\to\h2k\folder\
   ```
   
   **Linux/Mac:**
   ```bash
   # Single file
   h2k2hpxml path/to/your/file.h2k
   
   # Or entire folder (processes all .h2k files in parallel)
   h2k2hpxml path/to/h2k/folder/
   ```

**Note:** After installation and activation, all commands (`h2k2hpxml`, `h2k-resilience`, `h2k-deps`) are directly available without needing `uv run` or other prefixes. To use them in future sessions, just activate the environment again.

### Interactive Demo

New users can learn the conversion process with the interactive demo:

**Windows:**
```powershell
# English demo
h2k-demo

# French demo  
h2k-demo --lang fr
```

**Linux/Mac:**
```bash
# English demo
h2k-demo

# French demo
h2k-demo --lang fr
```

The demo will:
- Guide you through selecting an example H2K file
- Show the exact command that will be run with all flags
- Run a real conversion with hourly outputs
- Display all generated output files in tree format with descriptions
- Demonstrate the full workflow from H2K to EnergyPlus simulation results

### Configuration System

The package uses a simple single-file configuration approach:

- **Main Config**: `config/conversionconfig.ini` - Single configuration file for all settings
- **Template**: `config/defaults/conversionconfig.template.ini` - Template used to create initial configuration

#### Configuration Management Commands

```bash
# Setup configuration from template
h2k-deps --setup

# Update dependency paths in configuration
h2k-deps --update-config

# Check dependency status
h2k-deps --check-only

# Auto-install missing dependencies
h2k-deps --auto-install

# Interactive dependency management
h2k-deps
```

## Usage

### Command Line Tools

The package provides several command-line tools:

```bash
# H2K to HPXML conversion (single file)
h2k2hpxml input.h2k [--output output.xml]

# H2K to HPXML conversion (entire folder)
h2k2hpxml /path/to/h2k/files/ [--output output_folder]

# Advanced options
h2k2hpxml input.h2k --debug --hourly ALL --output-format json

# Convert only (no simulation)
h2k2hpxml input.h2k --do-not-sim

# Show credits
h2k2hpxml --credits

# Resilience analysis
h2k-resilience input.h2k [--run-simulation] [--outage-days N] [--output-path PATH] \
  [--clothing-factor-summer F] [--clothing-factor-winter F]

# Dependency management
h2k-deps [--setup] [--check-only] [--auto-install]
```

### Performance and Parallel Processing

h2k2hpxml automatically uses parallel processing for folder inputs, utilizing `CPU cores - 1` threads for optimal performance.

See the [Performance Guide](docs/PERFORMANCE.md) for detailed optimization strategies.

### Docker Usage (Recommended for Easy Setup)

Docker provides the easiest way to use h2k-hpxml without installing dependencies:

```bash
# Quick start - convert a single file
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# Process entire folder (parallel processing)
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/
```

✅ No Python/OpenStudio installation required  
✅ Works on Windows, Mac, and Linux  
✅ All dependencies included

See the [Docker Guide](docs/DOCKER.md) for complete documentation, including Docker Compose examples and CI/CD integration.

### Alternative Docker Environment (Development)

For development work, we also provide a comprehensive development container. Installation and usage documentation is available [here](https://github.com/canmet-energy/model-dev-container)

## Development Environment

### Quick Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/canmet-energy/h2k-hpxml.git
   cd h2k-hpxml
   ```

2. **Create development environment with uv**:
   ```bash
   # Create virtual environment with correct Python version
   uv venv h2k-dev --python 3.12
   
   # Activate environment
   source h2k-dev/bin/activate  # Linux/Mac
   # or
   h2k-dev\Scripts\activate     # Windows
   ```

3. **Install in development mode**:
   ```bash
   uv pip install -e '.[dev]'
   ```

4. **Setup development configuration**:
   ```bash
   h2k-deps --setup
   ```

5. **Install dependencies automatically**:
   ```bash
   h2k-deps --auto-install
   ```

6. **Run tests to verify setup**:
   ```bash
   pytest tests/unit/
   ```

### Development Dependencies

The project integrates several key components:

* **EnergyPlus** - Building energy simulation engine
* **OpenStudio SDK** - Building modeling and simulation tools
* **OpenStudio-HPXML** - NREL's HPXML-OpenStudio Python source code
* **Python 3.12+** and necessary libraries

### Development Tools

The project includes several quality assurance tools:

```bash
# Manual formatting and linting
black src/ tests/                    # Code formatting
ruff check src/ tests/               # Linting
ruff check --fix src/ tests/         # Auto-fix linting issues

# Type checking (Note: Most type hints have been removed from the codebase)
mypy src/h2k_hpxml/core/            # Will show remaining type issues
```

### Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with baseline generation (WARNING: overwrites golden files)
pytest --run-baseline
```

### Docker Development Environment (Alternative)

To streamline development, we've also created a [Visual Studio Code](https://code.visualstudio.com/) [devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) environment that automatically installs all required libraries with their correct versions, ensuring a smooth setup and consistent configuration.

Full instructions on how to set up the Docker development environment are [here](docs/development/vscode.md)

### AI Assistant Development

For AI assistants (like Claude Code) working with this repository, see [CLAUDE.md](CLAUDE.md) for detailed architecture overview, essential commands, and development guidance.

## Contributing

Contributions are encouraged! If you find a bug, submit an "Issue" on the tab above.  **Please understand that this is still under heavy development and should not be used for any production level of work.**

## Full Documentation

For more detailed documentation, please see:

### Installation & Testing
- 📦 **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup, configuration, and dependency management
- ⚡ **[Quick Start with uv](docs/installation/quick_start_uv.md)** - Fast installation using the modern uv package manager (10-100x faster than pip)
- 🧪 **[Installation Testing Guide](docs/installation/installation_test.md)** - Complete guide to verify your installation is working correctly
- ✅ **[Post-Installation Testing](docs/installation/test_after_install.md)** - Step-by-step verification after package installation

### Usage & Performance
- 🐳 **[Docker Guide](docs/DOCKER.md)** - Complete Docker usage, deployment, and Docker Compose examples
- ⚡ **[Performance Guide](docs/PERFORMANCE.md)** - Parallel processing, optimization, and batch processing

### Development
- 💻 **[Development Guide](docs/DEVELOPMENT.md)** - Development environment setup, testing, and contribution guidelines
- 🔧 **[Configuration Guide](docs/development/configuration_system.md)** - Configuration system details
- 📊 **[Status & Features](docs/status/status.md)** - Current implementation status and supported features
