# H2K -> HPXML -> EnergyPlus Initiative

## Background

CMHC is investigating energy use in Canada’s existing housing stock and exploring policy measures to enhance energy efficiency and affordability for Canadians. The primary tool used to evaluate building energy performance in Canada is NRCan’s Hot2000 (H2K) software. H2K is a building energy simulator that estimates the annual energy consumption of homes across Canada. NRCan has also developed a comprehensive database of archetypes representing housing across the country, using over 30 years of data from the EnerGuide for housing program. This location-specific database includes more than 6,000 archetypes, each reflecting regional housing characteristics.

However, H2K has some limitations, including the inability to provide hourly energy data.  H2K only produces annual energy estimates. This lack of hourly resolution restricts its capacity to support analyses of modern energy conservation measures, such as thermal and electrical storage technologies, renewable energy, advanced building automation, and other innovative solutions. Furthermore, H2K cannot assess the effects of time-of-use (TOU) electricity rates or peak demand on housing affordability.

In contrast, the software created by the U.S. Department of Energy (U.S. DOE), EnergyPlus/HPXML, provides high resolution sub-hourly outputs.  EnergyPlus/HPXML was developed in 2001 to be the standard simulation tool used by the U.S. DOE to support housing and building energy analysis.  Over $3M is annually invested in EnergyPlus/HPXML to support R&D, as well as national programs.  It provides detailed simulation information at a sub-hourly resolution that can examine time-of-use (TOU) technologies and help examine evaluate several advanced energy conservation measures.

The goal of this work is to leverage the 6000 H2K archetype model data, by translating them to EnergyPlus/HPXML. These new models will then produce sub-hourly natural gas and electricity usage profiles to better analyze the Canadian housing stock. This will create an unprecedented level of information on how these homes consume electricity and natural gas on a sub hourly basis.  It can also provide estimates on the hourly temperatures these homes experience in extreme weather events.

This data could be used to better understand thermal safety measures (overheating) that could be applied to existing and new homes.  The affordability of different HVAC systems combined with TOU electricity rates could show what are the most cost-effective systems based on TOU electric utility rates.  It could also be used to explore new technologies such as energy storage to support electrification. This and other analyses are possible and open up a door to a wealth of analysis for housing down the road.

## Why use HPXML?
HPXML, or Home Performance eXtensible Markup Language, is a standardized data format designed for the residential energy efficiency industry. It enables consistent data collection, sharing, and analysis across different software systems, tools, and stakeholders involved in home energy performance. Developed by the Building Performance Institute (BPI) and managed by the National Renewable Energy Laboratory (NREL), HPXML provides a common structure for information about home energy audits, improvements, and performance metrics. By using HPXML, organizations can streamline processes, improve data accuracy, and easily integrate with energy efficiency programs, certifications, and incentives. More information on the HPXML standard can be found [here](https://hpxml-guide.readthedocs.io/en/latest/overview.html)

## Roadmap
The overall goal of this project is to have full support of all H2K features translated to OS/EnergyPlus via HPXML format. We have taken an incremental approach to release the translator as we add funtionality. This allows researchers and stakeholders to use, and evaluate the translation capabilities as we develop them.

The timeline is as follows:

| Phase | Description | Target Completion Date | Status |  |
|---|---|---|---|---|
| 1 | Loads Translations. This includes schedules, occupancy, plug loads, envelope charecteristics & climate file mapping. Default fixed HVAC  |Summer 2024| Completed & available for use. Presentation comparing results available [here](docs/presentations/H2k-HPXML-20240214-V2.pdf)|
| 2 | HVAC Systems. This includes all systems and fuel types.|Spring 2025| Completed - Beta Testing. Report and presentation comparing results available [here](docs/reports/H2k-HPXML-Systems-Report.pdf) and [here](docs/presentations/H2k-HPXML-EPlus-Systems-Update-20250326.pdf)|
| 3 | Multi-Urban Residential Buildings | TBD | Not Started |

**Note**: Versioning of components targeted for each OS SDK is kept [here](https://github.com/canmet-energy/model-dev-container/blob/main/versioning.md). This will keep the development and results consistent across development as we upgrade components.

Here is a [list](docs/status/status.md) of the current completed sections related to the HPXML standard. This is a list of the assumptions and issues that were found in the translation work.

## Installation & Setup

### Quick Start (pip install)

1. **Install the package**:
   ```bash
   pip install h2k-hpxml
   ```

2. **Initial setup** (creates user configuration with auto-detected dependencies):
   ```bash
   h2k-deps --setup
   ```

3. **Verify installation**:
   ```bash
   h2k-deps --check-only
   ```

4. **Convert your first H2K file**:
   ```bash
   h2k2hpxml path/to/your/file.h2k
   ```

### Configuration System

The package uses a simple single-file configuration approach:

- **Main Config**: `config/conversionconfig.ini` - Single configuration file for all settings
- **Template**: `config/templates/conversionconfig.template.ini` - Template used to create initial configuration

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
# H2K to HPXML conversion
h2k2hpxml input.h2k [--output output.xml]

# Resilience analysis
h2k-resilience input.h2k [--scenarios SCENARIOS]

# Dependency management
h2k-deps [--setup] [--check-only] [--auto-install]
```

### Docker Environment (Alternative)

During development, we've also created a separate Docker command-line interface (CLI) application that translates and runs H2K data files in EnergyPlus. To use it, simply install Docker Desktop on your machine. Comprehensive installation and usage documentation is available [here](https://github.com/canmet-energy/model-dev-container)

## Development Environment

### Quick Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/canmet-energy/h2k_hpxml.git
   cd h2k_hpxml
   ```

2. **Install in development mode**:
   ```bash
   pip install -e .
   ```

3. **Setup development configuration**:
   ```bash
   h2k-deps --setup
   ```

4. **Install dependencies automatically**:
   ```bash
   h2k-deps --auto-install
   ```

5. **Run tests to verify setup**:
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
# Run all quality checks (formatting, linting, type checking, tests)
./scripts/quality_check.sh

# Auto-fix formatting and linting issues
./scripts/quality_fix.sh

# Manual formatting and linting
black src/ tests/                    # Code formatting
ruff check src/ tests/               # Linting
mypy src/h2k_hpxml/core/            # Type checking
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


Contributions are encouraged! If you find a bug, submit an "Issue" on the tab above.  Please understand that this is still under heavy development and should not be used for any production level of work.
