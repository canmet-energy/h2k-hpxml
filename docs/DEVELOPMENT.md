# H2K-HPXML Development Guide

Guide for contributing to the H2K-HPXML project.

## Table of Contents

- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [Project Architecture](#project-architecture)
- [Development Commands](#development-commands)
- [Testing](#testing)
- [Contributing](#contributing)
- [External Resources](#external-resources)

## Quick Start

**Recommended**: Use the pre-configured DevContainer for instant setup with all dependencies.

### Prerequisites

- [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) or Docker Engine (Linux)

### Windows — WSL bootstrap (one-time)

Corporate Windows machines need WSL + Docker Desktop before they can run
DevContainers. Use the
[canmet-energy/development_config](https://github.com/canmet-energy/development_config/tree/main/wsl)
bootstrap scripts:

**1. Admin phase** — run once from an **elevated** PowerShell as your admin account:

```powershell
& "<path-to-repo>\wsl\Install-WslDevEnvironment-Admin.ps1"
```

This installs Docker Desktop and adds your daily-use account to the local
`docker-users` group. Launch Docker Desktop once to accept the license, then
**log out and back in**.

**2. User phase** — run as your **daily-use** account from a **normal** (non-elevated) PowerShell:

```powershell
& "<path-to-repo>\wsl\Install-WslDevEnvironment.ps1" -ResetDistro -DebugLog
```

> **Important:** Run unelevated so the WSL distro registers under *your*
> profile. If you run elevated, the distro lands under the admin account.

This installs Ubuntu 24.04 LTS (registered as `nrcan_ubuntu`), creates your
Linux user, installs corporate root CAs, configures Kerberos, and sets up
Docker Desktop WSL integration.

| Flag | Meaning |
|------|---------|
| `-ResetDistro` | Unregister and reinstall the distro from scratch |
| `-DebugLog` | Capture run to `%USERPROFILE%\Install-WslDevEnvironment.log` |
| `-SkipKerberos` | Skip Kerberos/SQL setup (non-domain machines) |

### Setup — Clone Repository into Container Volume

Once Docker Desktop is running (Windows/WSL) or Docker Engine is installed (Linux):

1. Open VS Code
2. `Ctrl+Shift+P` → **Dev Containers: Clone Repository in Container Volume**
3. Enter the repo URL: `https://github.com/canmet-energy/h2k-hpxml.git`
4. Wait for the container to build
5. *(Optional — corporate networks)* Add your certs to `.devcontainer/certs/`
   and rebuild (`Ctrl+Shift+P` → **Dev Containers: Rebuild Container**). See [Corporate Networks](../.devcontainer/certs/README.md)
6. Verify the environment:
   ```bash
   os-setup --check-only        # Verify OpenStudio + HPXML dependencies
   pytest -v                    # Run the full test suite
   ```
7. If contributing, configure your git identity:
   ```bash
   git config --global user.email '<your email>'
   git config --global user.name '<Your First and Last Name>'
   ```

The DevContainer automatically configures Python, OpenStudio, EnergyPlus, and all development tools.

**Learn more**: [VS Code DevContainers Guide](https://code.visualstudio.com/docs/devcontainers/containers)

**VS Code Extensions**: See `.vscode/extensions.json` for recommended extensions. [VS Code Python Setup](https://code.visualstudio.com/docs/python/python-tutorial)

## Project Architecture

### Repository Structure

```
h2k-hpxml/
├── src/h2k_hpxml/              # Main package
│   ├── api.py                  # Public API (convert_h2k_file, run_full_workflow)
│   ├── cli/                    # CLI tools (h2k-hpxml, h2k-demo, os-setup)
│   ├── core/                   # Core translation engine
│   │   ├── translator.py       # Main h2ktohpxml() function
│   │   ├── model.py            # ModelData state tracking
│   │   ├── template_loader.py  # HPXML template & H2K parsing
│   │   └── processors/         # Building/Weather/Enclosure/Systems
│   ├── components/             # Component translators (walls, HVAC, etc.)
│   ├── config/                 # Configuration management
│   ├── resources/              # Templates, weather data, mappings
│   ├── utils/                  # Utilities and helpers
│   └── analysis/               # Post-simulation analysis
├── tests/                      # Test suite
│   ├── unit/                   # Fast, isolated tests
│   ├── integration/            # End-to-end workflow tests
│   └── fixtures/               # Test data and golden files
├── config/                     # Configuration files
└── .devcontainer/             # DevContainer configuration
```

### Translation Pipeline

```
H2K File → XML Parser → Component Processors → HPXML Assembly → EnergyPlus Simulation
    ↓           ↓              ↓                    ↓                ↓
Validation  ModelData    Building/Systems      XML Generation     Results
```

### Key Design Principles

- **Modular Architecture** - Each component has its own translator
- **Configuration-Driven** - Single config file (`config/conversionconfig.ini`)
- **Error Resilience** - Comprehensive validation with detailed error messages
- **Performance Optimized** - Parallel processing using `(CPU cores - 1)` threads
- **Extensible** - Easy to add new components without modifying core logic
- **Test-Driven** - Extensive unit, integration, and regression test coverage

### Data Flow

```python
# Typical translation flow
h2k_dict = parse_h2k_xml(h2k_file_path)      # Parse input
model_data = ModelData()                      # State tracking
config = ConfigManager()                      # Load configuration

# Process components
building_info = process_building_details(h2k_dict, model_data)
weather_data = process_weather_mapping(h2k_dict, config)
enclosure = process_enclosure_components(h2k_dict, model_data)
systems = process_hvac_systems(h2k_dict, model_data)

# Assemble output
hpxml_dict = assemble_hpxml(building_info, weather_data, enclosure, systems)
xml_output = dict_to_xml(hpxml_dict)
```

## Development Commands

### Essential Commands

```bash
# Run tests
pytest tests/unit/ -v                           # Unit tests
pytest tests/integration/ -v                    # Integration tests
pytest -n auto                                  # Parallel execution
pytest --cov=src/h2k_hpxml --cov-report=html    # With coverage

# Code quality
black src/ tests/                               # Format code
ruff check src/ tests/ --fix                    # Lint and auto-fix
mypy src/h2k_hpxml/core/                       # Type checking

# Test with real files
h2k-hpxml src/h2k_hpxml/examples/WizardHouse.h2k --debug --do-not-sim
h2k-demo                                        # Interactive demo

# Regenerate test baselines (use with caution)
pytest --run-baseline
```

### Branch Strategy

```bash
git checkout -b feature/new-component-translator
git checkout -b fix/issue-123
git checkout -b docs/update-guide
```

**Learn more**: [Git Branching](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell), [Conventional Commits](https://www.conventionalcommits.org/)

## Testing

### Test Organization

```
tests/
├── unit/                           # Fast, isolated tests (flat structure)
│   ├── test_cli_convert.py         # CLI conversion tests
│   ├── test_config_manager.py      # Configuration tests
│   ├── test_core_model.py          # ModelData tests
│   ├── test_core_translator.py     # Core translation logic
│   ├── test_dependencies.py        # Dependency management
│   ├── test_essential_utilities.py # Utility functions
│   └── ... (other unit tests)
├── integration/                    # End-to-end tests
│   ├── test_demo.py                # Interactive demo tests
│   ├── test_regression.py          # Golden file comparisons
│   ├── test_resilience.py          # Resilience CLI tests
│   └── test_windows_installation.py # Windows-specific tests
└── fixtures/                       # Test data
    └── expected_outputs/           # Golden files for regression tests
```

### Running Tests

```bash
# By test folder
pytest tests/unit/ -v                    # Fast unit tests
pytest tests/integration/ -v             # Slow regression tests.
pytest -v                                # All tests. 

# Specific test files
pytest tests/unit/test_core_translator.py -v
pytest tests/unit/test_config_manager.py -v

# Specific test in a file
pytest tests/unit/test_core_translator.py::TestH2KToHPXML::test_valid_translation_modes -v

# With options
pytest -n auto                           # Parallel to test faster. 
pytest -x                                # Stop on first failure
pytest -v -s                             # Verbose with stdout

# Coverage to determin how much of the code is covered by tests. 
pytest --cov=src/h2k_hpxml --cov-report=html tests/
open htmlcov/index.html                  # View coverage report
```

**Learn more**: [Pytest Documentation](https://docs.pytest.org/), [Pytest-cov](https://pytest-cov.readthedocs.io/)

## Contributing

### Code Style

- **Python**: PEP 8 (enforced by black and ruff)
- **Line Length**: 100 characters max
- **Docstrings**: Required for all public functions
- **Type Hints**: Optional but encouraged

### Pull Request Process

1. Create feature branch from `main`
2. Make changes and add tests
3. Run full test suite: `pytest -n auto`
4. Test python targets using tox on supported python versions. (Install other versions using "uv python install 3.xx" )
4. Format code: `black src/ tests/ tools/`
5. Lint code: `ruff check src/ tests/ tools/ --fix`
6. Commit with [conventional commits](https://www.conventionalcommits.org/) format
7. Push and create pull request on GitHub
8. Request review from maintainers

### Testing Requirements

- Add unit tests for new components
- Add integration/regression tests for significant features
- Ensure all tests pass before submitting PR
- Update golden files if output format changes (document why)

## External Resources

### Project-Specific
- **HPXML Standard**: [HPXML Guide](https://hpxml-guide.readthedocs.io/)
- **OpenStudio**: [Documentation](https://openstudio.net/)
- **EnergyPlus**: [Documentation](https://energyplus.net/)

### Development Tools
- **VSCode Python**: [Tutorial](https://code.visualstudio.com/docs/python/python-tutorial)
- **VSCode DevContainers**: [Guide](https://code.visualstudio.com/docs/devcontainers/containers)
- **Git**: [Pro Git Book](https://git-scm.com/book/en/v2)
- **Pytest**: [Documentation](https://docs.pytest.org/)
- **Black**: [Documentation](https://black.readthedocs.io/)
- **Ruff**: [Documentation](https://docs.astral.sh/ruff/)
- **MyPy**: [Documentation](https://mypy.readthedocs.io/)

---

**Ready to contribute?** Start with `src/h2k_hpxml/core/translator.py` to understand the translation pipeline, then pick an issue from [GitHub Issues](https://github.com/canmet-energy/h2k-hpxml/issues).

Welcome to the H2K-HPXML development community! 🎉
