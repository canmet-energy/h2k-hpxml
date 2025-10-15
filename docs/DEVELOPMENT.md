# H2K-HPXML Development Guide

Complete guide for contributing to the H2K-HPXML project using VSCode and modern development tools.

## Table of Contents

- [Quick Start with VSCode](#quick-start-with-vscode)
- [Development Environment Setup](#development-environment-setup)
- [Project Architecture](#project-architecture)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [Code Quality Tools](#code-quality-tools)
- [Contributing Guidelines](#contributing-guidelines)
- [Debugging and Troubleshooting](#debugging-and-troubleshooting)

## Quick Start with VSCode

**Recommended Approach**: Use the pre-configured DevContainer for instant development setup.

### 1. Prerequisites

- **VSCode**: [Download Visual Studio Code](https://code.visualstudio.com/)
- **Docker Desktop**: [Install Docker](https://www.docker.com/products/docker-desktop/)
- **VSCode Extensions** (auto-installed with DevContainer):
  - Dev Containers
  - Python
  - Python Debugger
  - Pylance

### 2. DevContainer Setup (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/canmet-energy/h2k-hpxml.git
cd h2k-hpxml

# 2. Open in VSCode
code .

# 3. When prompted, click "Reopen in Container"
# OR: Press F1 → "Dev Containers: Reopen in Container"
```

**That's it!** The DevContainer automatically:
- ✅ Sets up Python 3.12
- ✅ Installs all dependencies (OpenStudio, EnergyPlus, Python packages)
- ✅ Configures development tools (pytest, black, ruff, mypy)
- ✅ Sets up debugging configuration
- ✅ Mounts your code for live editing

### 3. Verify Setup

```bash
# Run in VSCode terminal (should work immediately)
os-setup --check-only
pytest tests/unit/ -v
h2k-hpxml --help
```

### 4. Start Developing

- **Run Tests**: `Ctrl+Shift+P` → "Python: Run All Tests"
- **Debug**: Set breakpoints and press `F5`
- **Format Code**: `Shift+Alt+F` (auto-formats with black)
- **Lint**: Problems panel shows ruff/mypy issues automatically

## Development Environment Setup

### Option 1: DevContainer (Recommended)

The `.devcontainer/` folder contains a complete development environment:

```
.devcontainer/
├── devcontainer.json    # VSCode configuration
├── Dockerfile          # Development container definition
└── docker-compose.yml  # Multi-service setup
```

**Benefits**:
- 🚀 **Zero setup time** - everything pre-configured
- 🔒 **Isolated environment** - no conflicts with your system
- 🔄 **Consistent across team** - everyone uses identical environment
- 🛠️ **All tools included** - OpenStudio, EnergyPlus, Python tools

### Option 2: Manual Setup (Alternative)

If you prefer not to use Docker:

#### Prerequisites
```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
```

#### Setup Steps
```bash
# 1. Clone repository
git clone https://github.com/canmet-energy/h2k-hpxml.git
cd h2k-hpxml

# 2. Create development environment
uv venv h2k-dev --python 3.12
source h2k-dev/bin/activate  # Linux/Mac
# or
h2k-dev\Scripts\activate     # Windows

# 3. Install development dependencies
uv pip install -e '.[dev]'

# 4. Setup dependencies and configuration
os-setup --setup
os-setup --auto-install

# 5. Verify setup
pytest tests/unit/
h2k-hpxml --help
```

#### VSCode Configuration (Manual Setup)

Install recommended extensions:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.debugpy",
    "ms-python.pylance",
    "charliermarsh.ruff",
    "ms-python.black-formatter",
    "ms-vscode.test-adapter-converter"
  ]
}
```

## Project Architecture

### Repository Structure

```
h2k-hpxml/
├── src/h2k_hpxml/              # Main package source
│   ├── api/                    # Public API (convert_h2k_file, etc.)
│   ├── cli/                    # Command-line interfaces
│   ├── components/             # H2K component translators
│   ├── config/                 # Configuration management
│   ├── core/                   # Core translation engine
│   ├── resources/              # Data files, templates, mappings
│   ├── utils/                  # Utility functions
│   └── analysis/               # Energy analysis tools
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── fixtures/               # Test data and baselines
│   └── utils/                  # Test utilities
├── docs/                       # Documentation
├── tools/                      # Development tools
├── config/                     # Configuration files
├── examples/                   # Sample H2K files
└── .devcontainer/             # VSCode DevContainer setup
```

### Core Architecture

#### Translation Pipeline
```python
# Main translation flow
H2K File → XML Parser → Component Processors → HPXML Assembly → EnergyPlus Simulation
    ↓           ↓              ↓                    ↓                ↓
  Validation  ModelData   Building/Systems     XML Generation    Results
```

#### Key Components

**Core Translation Engine** (`src/h2k_hpxml/core/`):
- `translator.py` - Main orchestration function `h2ktohpxml()`
- `model.py` - `ModelData` class for tracking building info
- `template_loader.py` - HPXML template and H2K XML parsing
- `hpxml_assembly.py` - Final XML generation

**Component Translators** (`src/h2k_hpxml/components/`):
- Individual translators for walls, windows, HVAC systems, etc.
- Pattern: `extract_from_h2k() → validate() → create_hpxml_structure() → return_components`

**Configuration** (`src/h2k_hpxml/config/`):
- `manager.py` - `ConfigManager` class
- Single config file: `config/conversionconfig.ini`

### Data Flow

```python
# Typical data flow through the system
h2k_dict = parse_h2k_xml(h2k_file_path)
model_data = ModelData()
config = ConfigManager()

# Process each building system
building_info = process_building_details(h2k_dict, model_data)
weather_data = process_weather_mapping(h2k_dict, config)
enclosure = process_enclosure_components(h2k_dict, model_data)
systems = process_hvac_systems(h2k_dict, model_data)

# Assemble final HPXML
hpxml_dict = assemble_hpxml(building_info, weather_data, enclosure, systems)
xml_output = dict_to_xml(hpxml_dict)
```

## Development Workflow

### 1. Branch Strategy

```bash
# Create feature branch
git checkout -b feature/new-component-translator
git checkout -b fix/issue-123
git checkout -b docs/update-installation-guide
```

### 2. Development Process

#### VSCode Workflow
1. **Open VSCode** with DevContainer
2. **Create/Switch Branch**: `Ctrl+Shift+P` → "Git: Create Branch"
3. **Make Changes**: Edit files with IntelliSense and auto-completion
4. **Run Tests Continuously**:
   - `Ctrl+Shift+P` → "Python: Configure Tests" (choose pytest)
   - Test Explorer panel shows all tests
   - Click ▶️ to run individual tests
5. **Debug Code**:
   - Set breakpoints with `F9`
   - Start debugging with `F5`
   - Step through code with `F10`/`F11`
6. **Format on Save**: Files auto-format with black/ruff
7. **Commit Changes**: Source Control panel (`Ctrl+Shift+G`)

#### Command Line Workflow
```bash
# Run tests during development
pytest tests/unit/test_translator.py -v
pytest tests/unit/test_translator.py::TestTranslator::test_basic_conversion -v

# Run tests with coverage
pytest tests/ --cov=h2k_hpxml --cov-report=html

# Format code
black src/ tests/
ruff check src/ tests/ --fix

# Type checking
mypy src/h2k_hpxml/core/

# Run all quality checks
pytest && black --check src/ tests/ && ruff check src/ tests/
```

### 3. Testing Your Changes

```bash
# Unit tests (fast)
pytest tests/unit/ -v

# Integration tests (slower, tests full pipeline)
pytest tests/integration/ -v

# Specific test for your component
pytest tests/unit/test_components/test_walls.py -v

# Test with real H2K files
h2k-hpxml examples/WizardHouse.h2k --debug --do-not-sim
```

### 4. Commit and Push

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add support for advanced window types

- Implement new window component translator
- Add support for dynamic glazing
- Update HPXML mapping for window properties
- Add unit tests for window translations"

# Push to GitHub
git push -u origin feature/advanced-windows
```

### 5. Create Pull Request

1. Go to GitHub repository
2. Click "Compare & pull request"
3. Fill out PR template:
   - Description of changes
   - Testing performed
   - Breaking changes (if any)
4. Request review from maintainers

## Testing Strategy

### Test Organization

```
tests/
├── unit/                       # Fast, isolated tests
│   ├── test_core/             # Core translation logic
│   ├── test_components/       # Individual component tests
│   ├── test_config/           # Configuration tests
│   └── test_utils/            # Utility function tests
├── integration/               # End-to-end tests
│   ├── test_regression.py     # Golden file comparisons
│   ├── test_full_workflow.py  # Complete H2K→HPXML→EnergyPlus
│   └── test_cli.py           # Command-line interface tests
└── fixtures/                  # Test data
    ├── h2k_files/            # Sample H2K files
    ├── expected_outputs/     # Golden master files
    └── mock_data/            # Mock objects for unit tests
```

### Running Tests in VSCode

#### Test Explorer
1. **Open Test Explorer**: `Ctrl+Shift+T`
2. **Run All Tests**: Click ▶️ at top level
3. **Run Specific Test**: Click ▶️ next to test name
4. **Debug Test**: Click 🐛 next to test name
5. **View Results**: Green ✅/Red ❌ indicators with detailed output

#### Test Discovery
```json
// .vscode/settings.json (auto-configured in DevContainer)
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

### Test Types

#### 1. Unit Tests
```python
# Example: tests/unit/test_components/test_walls.py
import pytest
from h2k_hpxml.components.walls import translate_wall_components
from h2k_hpxml.core.model import ModelData

def test_basic_wall_translation():
    """Test basic wall component translation."""
    # Arrange
    h2k_wall_data = {
        'wall_id': 'W1',
        'construction': 'Wood Frame',
        'area': 100.0
    }
    model_data = ModelData()

    # Act
    hpxml_walls = translate_wall_components(h2k_wall_data, model_data)

    # Assert
    assert len(hpxml_walls) == 1
    assert hpxml_walls[0]['id'] == 'Wall_W1'
    assert hpxml_walls[0]['area'] == 100.0
```

#### 2. Integration Tests
```python
# Example: tests/integration/test_full_workflow.py
def test_wizardhouse_full_conversion():
    """Test complete WizardHouse.h2k conversion."""
    result = convert_h2k_file(
        'examples/WizardHouse.h2k',
        simulate=True
    )

    # Verify HPXML was created
    assert Path(result).exists()

    # Verify simulation completed
    sim_dir = Path(result).parent / 'run'
    assert (sim_dir / 'eplusout.sql').exists()
```

#### 3. Regression Tests
```python
# Automatically compare against golden master files
pytest tests/integration/test_regression.py -v

# Update golden files (use with caution!)
pytest --run-baseline
```

### Test Configuration

#### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    baseline_generation: marks tests that generate baseline data
```

#### Running Specific Test Types
```bash
# Fast tests only
pytest tests/unit/ -v

# Skip slow tests
pytest -m "not slow" -v

# Integration tests only
pytest tests/integration/ -v

# Parallel execution (faster)
pytest -n auto tests/

# With coverage
pytest --cov=h2k_hpxml --cov-report=html tests/
```

## Code Quality Tools

All tools are pre-configured in the DevContainer and integrated with VSCode.

### 1. Code Formatting (Black)

**VSCode Integration**:
- Auto-formats on save
- Manual format: `Shift+Alt+F`

**Command Line**:
```bash
# Format all code
black src/ tests/

# Check formatting without changes
black --check src/ tests/

# Format specific file
black src/h2k_hpxml/core/translator.py
```

### 2. Linting (Ruff)

**VSCode Integration**:
- Real-time linting in editor
- Problems panel shows issues
- Auto-fix on save for some issues

**Command Line**:
```bash
# Check all files
ruff check src/ tests/

# Auto-fix issues
ruff check src/ tests/ --fix

# Check specific file
ruff check src/h2k_hpxml/core/translator.py
```

**Configuration** (pyproject.toml):
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]
```

### 3. Type Checking (MyPy)

**Note**: The project uses selective type hints. MyPy is configured with relaxed settings.

```bash
# Check core modules (where type hints exist)
mypy src/h2k_hpxml/core/

# Check specific file
mypy src/h2k_hpxml/core/translator.py

# Skip type checking for rapid development
# (Type hints are optional in this project)
```

### 4. Pre-commit Hooks (Optional)

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

Configuration (.pre-commit-config.yaml):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

## Contributing Guidelines

### 1. Code Style

- **Python**: Follow PEP 8 (enforced by black and ruff)
- **Line Length**: 100 characters max
- **Imports**: Use isort/ruff for import organization
- **Comments**: Clear, concise docstrings for public functions
- **Type Hints**: Optional but encouraged for new code

### 2. Component Development Pattern

When adding new component translators:

```python
# src/h2k_hpxml/components/new_component.py
def translate_new_components(h2k_data: dict, model_data: ModelData) -> list:
    """
    Translate H2K new components to HPXML format.

    Args:
        h2k_data: Dictionary containing H2K XML data
        model_data: ModelData instance for tracking counters/warnings

    Returns:
        List of HPXML component dictionaries
    """
    components = []

    # 1. Extract data from H2K
    new_items = extract_new_items(h2k_data)

    # 2. Process each item
    for item in new_items:
        # Validate and transform
        if validate_item(item):
            hpxml_item = create_hpxml_item(item, model_data)
            components.append(hpxml_item)
        else:
            model_data.add_warning_message(f"Invalid item: {item}")

    return components

def extract_new_items(h2k_data):
    """Extract new component data from H2K dictionary."""
    # Use h2k_parser utilities
    from h2k_hpxml.core.h2k_parser import safe_get, safe_float

    items = safe_get(h2k_data, ['Building', 'NewComponents'], [])
    return [item for item in items if item.get('enabled', True)]

def create_hpxml_item(h2k_item, model_data):
    """Create HPXML structure for a new component."""
    # Increment counter
    counter = model_data.increment_counter('new_component')

    return {
        'id': f'NewComponent_{counter}',
        'type': h2k_item.get('type'),
        'properties': transform_properties(h2k_item)
    }
```

### 3. Testing New Components

```python
# tests/unit/test_components/test_new_component.py
import pytest
from h2k_hpxml.components.new_component import translate_new_components
from h2k_hpxml.core.model import ModelData

class TestNewComponentTranslation:
    def test_basic_translation(self):
        """Test basic new component translation."""
        h2k_data = {
            'Building': {
                'NewComponents': [
                    {'type': 'TypeA', 'property1': 'value1'},
                    {'type': 'TypeB', 'property2': 'value2'}
                ]
            }
        }
        model_data = ModelData()

        result = translate_new_components(h2k_data, model_data)

        assert len(result) == 2
        assert result[0]['id'] == 'NewComponent_1'
        assert result[1]['id'] == 'NewComponent_2'

    def test_invalid_component_handling(self):
        """Test handling of invalid components."""
        h2k_data = {
            'Building': {
                'NewComponents': [
                    {'type': None},  # Invalid
                    {'type': 'Valid', 'property': 'value'}  # Valid
                ]
            }
        }
        model_data = ModelData()

        result = translate_new_components(h2k_data, model_data)

        assert len(result) == 1  # Only valid component
        assert len(model_data.warnings) == 1  # Warning for invalid
```

### 4. Documentation

- **API Documentation**: Docstrings for all public functions
- **Component Documentation**: README in component directories
- **User Documentation**: Update relevant guides when adding features
- **Examples**: Provide usage examples for new features

## Debugging and Troubleshooting

### VSCode Debugging

#### 1. Debug Configuration (.vscode/launch.json)
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug H2K Conversion",
            "type": "python",
            "request": "launch",
            "module": "h2k_hpxml.cli.convert",
            "args": [
                "examples/WizardHouse.h2k",
                "--debug",
                "--do-not-sim"
            ],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "tests/unit/test_translator.py::test_basic_conversion",
                "-v",
                "-s"
            ],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

#### 2. Debugging Workflow
1. **Set Breakpoints**: Click in gutter next to line numbers
2. **Start Debugging**: Press `F5` or click ▶️ in Debug panel
3. **Step Through Code**:
   - `F10` - Step over
   - `F11` - Step into
   - `Shift+F11` - Step out
   - `F5` - Continue
4. **Inspect Variables**: Hover or use Variables panel
5. **Debug Console**: Evaluate expressions at runtime

### Common Development Issues

#### 1. Import Errors
```bash
# Ensure you're in the right environment
which python
pip list | grep h2k-hpxml

# Install in development mode
uv pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH
```

#### 2. Configuration Issues
```bash
# Check configuration
os-setup --check-only

# Reset configuration
rm config/conversionconfig.ini
os-setup --setup
```

#### 3. Test Failures
```bash
# Run with verbose output
pytest tests/unit/test_failing.py -v -s

# Run with debugging
pytest tests/unit/test_failing.py --pdb

# Run in VSCode with debugger
# Set breakpoint in test and use "Debug Test" button
```

#### 4. Memory Issues During Development
```bash
# Monitor memory usage
htop  # Linux/Mac
# or Task Manager on Windows

# Use smaller test files
cp examples/simple.h2k test_input.h2k
h2k-hpxml test_input.h2k --debug

# Profile memory usage
pip install memory-profiler
python -m memory_profiler your_script.py
```

### Logging and Debug Output

```python
# Add debug logging to your code
import logging
logger = logging.getLogger(__name__)

def your_function():
    logger.debug("Processing component X")
    logger.info(f"Found {count} items")
    logger.warning("Using default value for missing property")
    logger.error("Failed to process component")
```

```bash
# Run with debug logging
h2k-hpxml input.h2k --debug

# Or set environment variable
export H2K_LOG_LEVEL=DEBUG
h2k-hpxml input.h2k
```

### Performance Profiling

```python
# Add timing to your functions
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end-start:.2f} seconds")
        return result
    return wrapper

@timing_decorator
def slow_function():
    # Your code here
    pass
```

```bash
# Profile entire conversion
python -m cProfile -o profile.stats -m h2k_hpxml.cli.convert input.h2k

# Analyze profile
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('time').print_stats(20)
"
```

## Next Steps

After setting up your development environment:

1. **Explore the Codebase**: Start with `src/h2k_hpxml/core/translator.py`
2. **Run Tests**: Ensure everything works with `pytest tests/unit/`
3. **Try a Small Change**: Fix a typo or add a comment
4. **Add a Feature**: Implement a new component translator
5. **Write Tests**: Add tests for your new code
6. **Submit PR**: Follow the contribution process

### Learning Resources

- **HPXML Standard**: [HPXML Guide](https://hpxml-guide.readthedocs.io/)
- **OpenStudio**: [OpenStudio Documentation](https://openstudio.net/)
- **EnergyPlus**: [EnergyPlus Documentation](https://energyplus.net/)
- **Python Testing**: [Pytest Documentation](https://docs.pytest.org/)
- **VSCode Python**: [Python in VSCode](https://code.visualstudio.com/docs/python/python-tutorial)

Welcome to the H2K-HPXML development community! 🎉