# Tools Directory

This directory contains various utilities and scripts for the h2k-hpxml project.

## Scripts

### `generate_baseline_data.py` (moved to tests/utils/)
**Purpose**: Generate baseline "golden files" for regression testing
**Usage**: `uv run python tests/utils/generate_baseline_data.py`
**Warning**: Overwrites existing baseline files - use with caution
**Alternative**: `pytest --run-baseline`
**Note**: Moved to tests/utils/ since it's a test utility

### Test Scripts (`test_scripts/`)
Development and debugging scripts created during implementation:

- **`test_cleanup_behavior.py`** - Tests automatic cleanup behavior when packages are uninstalled
- **`test_dependency_installation.py`** - Demonstrates the dependency installation system  
- **`test_windows_cleanup.py`** - Tests Windows-specific cleanup behavior

These are standalone scripts used for development/debugging and are not part of the main test suite.

### Utility Scripts

- **`cleanup.py`** - Cross-platform cleanup script that removes Python cache files, tool caches, and temporary files while preserving directory structure (works on Windows, Linux, macOS)
- **`compare.py`** - Analysis comparison utility that compares H2K vs HPXML/EnergyPlus simulation results, supporting both SOC and ASHRAE140 translation modes

## Usage

All Python scripts should be run from the project root using:
```bash
uv run python tools/script_name.py
```

This ensures proper path resolution and virtual environment usage.

### Parallel Testing

The regression tests can be run in parallel for significantly improved performance:

```bash
# Run regression tests in parallel (recommended)
pytest tests/integration/test_regression.py -n auto

# Run all tests with parallel execution
pytest -n auto

# Expected performance improvement:
# - Sequential: ~7 tests × 30-60 seconds each = 3.5-7 minutes
# - Parallel (4 cores): ~60-120 seconds total (3-6x faster)
```

**Benefits:**
- **3-7x faster execution** depending on CPU cores
- **Better test isolation** (each test in separate process)
- **Clearer failure reporting** (individual test results per H2K file)
- **Same simplicity** for adding new tests (just add H2K file to examples/)