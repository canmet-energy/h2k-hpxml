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

- [VSCode](https://code.visualstudio.com/) with Microsoft Dev Container Extension Installed.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Setup

### Clone Repository into Container Volume.
 1. Open vscode. 
 2. Ctrl + Shift + P and Type "Dev Containers: Clone Repository in container volume" and select from list.
 3. Enter the github repo url.  
 4. Let it build.
 5. Optionally if you are on a secured network like NRCan, add your certs file to the .devcontainer/certs/ folder and rebuild (Ctrl+Shift+P and Type "Dev Containers: Rebuild.) See [Corporate Networks](../.devcontainer/certs/README.md)
 6. Check if eveything works with these commands
    * os-setup --check-only
    * pytest -v


The DevContainer automatically configures Python, OpenStudio, EnergyPlus, and all development tools. They should all be available on in the terminal when typed. 

**Learn more**: [VSCode DevContainers Guide](https://code.visualstudio.com/docs/devcontainers/containers)


**VSCode Extensions**: See `.vscode/extensions.json` for recommended extensions. [VSCode Python Setup](https://code.visualstudio.com/docs/python/python-tutorial)

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
