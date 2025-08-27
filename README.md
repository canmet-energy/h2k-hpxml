# H2K -> HPXML -> EnergyPlus Initiative

## Background

NRCan/CMHC is investigating energy use in Canada’s existing housing stock and exploring policy measures to enhance energy efficiency and affordability for Canadians. The primary tool used to evaluate building energy performance in Canada is NRCan’s Hot2000 (H2K) software. H2K is a building energy simulator that estimates the annual energy consumption of homes across Canada. NRCan has also developed a comprehensive database of archetypes representing housing across the country, using over 30 years of data from the EnerGuide for housing program. This location-specific database includes more than 6,000 archetypes, each reflecting regional housing characteristics.

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

### Docker Usage (Recommended for Easy Setup)

The easiest way to use h2k-hpxml without installing Python, OpenStudio, or other dependencies is through Docker:

#### Quick Start with Docker

1. **Install Docker** on your machine ([Docker Desktop](https://www.docker.com/products/docker-desktop/))

2. **Run h2k-hpxml directly**:
   ```bash
   # Convert H2K file in your current directory
   docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/your_file.h2k
   
   # Resilience analysis
   docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-resilience /data/your_file.h2k
   ```

#### Docker Usage Examples

```bash
# Basic conversion - process file in current directory
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# Specify output location
docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
  h2k2hpxml /data/input.h2k --output /data/output.xml

# Use separate input/output directories (Windows example)
docker run --rm \
  -v "C:\path\to\input":/input:ro \
  -v "C:\path\to\output":/output \
  canmet/h2k-hpxml h2k2hpxml /input/house.h2k --output /output/house.xml

# Resilience analysis with specific scenarios
docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
  h2k-resilience /data/house.h2k --scenarios "outage_typical_year,thermal_autonomy_extreme_year"

# Get help
docker run --rm canmet/h2k-hpxml help
```

#### Docker Configuration

The Docker container automatically:
- Sets up all required dependencies (OpenStudio, OpenStudio-HPXML, Python packages)
- Creates configuration files in `/data/.h2k-config/` (preserved between runs)
- Creates output directories as needed

#### Advantages of Docker Approach
- ✅ No local Python/OpenStudio installation required
- ✅ Consistent environment across Windows, Mac, and Linux
- ✅ Automatic dependency management
- ✅ Version-pinned for reproducibility
- ✅ Easy to integrate into CI/CD pipelines

### Docker CLI Reference

#### All Available Commands
```bash
# Help and version information
docker run --rm canmet/h2k-hpxml help                    # Docker usage help
docker run --rm canmet/h2k-hpxml h2k2hpxml --help       # H2K conversion help
docker run --rm canmet/h2k-hpxml h2k-resilience --help  # Resilience analysis help
docker run --rm canmet/h2k-hpxml h2k2hpxml --version    # Show version

# Basic file conversion
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# Conversion with custom output path
docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
  h2k2hpxml /data/input.h2k --output /data/custom_output.xml

# Resilience analysis (default: 7-day outage)
docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
  h2k-resilience /data/input.h2k

# Resilience analysis with custom parameters
docker run --rm -v $(pwd):/data canmet/h2k-hpxml \
  h2k-resilience /data/input.h2k \
  --outage-days 10 \
  --clothing-factor-summer 0.6 \
  --clothing-factor-winter 1.2 \
  --run-simulation

# Interactive shell (for debugging)
docker run --rm -it -v $(pwd):/data canmet/h2k-hpxml bash
```

#### Volume Mounting Options
```bash
# Single directory (read/write)
-v $(pwd):/data                              # Current directory
-v /absolute/path:/data                      # Absolute path
-v "C:\Windows\Path":/data                   # Windows path

# Separate input/output directories
-v /path/to/h2k/files:/input:ro              # Read-only input
-v /path/to/output:/output                   # Write-only output

# Multiple mount points
docker run --rm \
  -v /home/user/h2k_files:/input:ro \
  -v /home/user/results:/output \
  -v /home/user/configs:/config \
  canmet/h2k-hpxml h2k2hpxml /input/house.h2k --output /output/house.xml
```

#### Environment Variables
```bash
# Enable debug logging
docker run --rm -e H2K_LOG_LEVEL=DEBUG -v $(pwd):/data \
  canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# Custom configuration path
docker run --rm -e H2K_CONFIG_PATH=/data/custom_config.ini -v $(pwd):/data \
  canmet/h2k-hpxml h2k2hpxml /data/input.h2k
```

#### Building the Docker Image Locally
```bash
# Build from source (for development)
git clone https://github.com/canmet-energy/h2k-hpxml.git
cd h2k-hpxml
docker build -t canmet/h2k-hpxml .

# Test the locally built image
docker run --rm canmet/h2k-hpxml help
```

#### Docker Compose (Batch Processing)
```yaml
# docker-compose.yml example for batch processing
version: '3.8'
services:
  h2k-converter:
    image: canmet/h2k-hpxml
    volumes:
      - ./input:/input:ro
      - ./output:/output
    command: h2k2hpxml /input/house.h2k --output /output/house.xml
```

### Alternative Docker Environment (Development)

For development work, we also provide a comprehensive development container. Installation and usage documentation is available [here](https://github.com/canmet-energy/model-dev-container)

## Development Environment

### Quick Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/canmet-energy/h2k-hpxml.git
   cd h2k-hpxml
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
