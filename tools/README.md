# Tools Directory

This directory contains various utilities and scripts for the h2k-hpxml project.

## Scripts

### `generate_baseline_data.py`
**Purpose**: Generate baseline "golden files" for regression testing
**Usage**: `uv run python tools/generate_baseline_data.py`
**Warning**: Overwrites existing baseline files - use with caution
**Alternative**: `pytest --run-baseline`

### Test Scripts (`test_scripts/`)
Development and debugging scripts created during implementation:

- **`test_cleanup_behavior.py`** - Tests automatic cleanup behavior when packages are uninstalled
- **`test_dependency_installation.py`** - Demonstrates the dependency installation system  
- **`test_windows_cleanup.py`** - Tests Windows-specific cleanup behavior

These are standalone scripts used for development/debugging and are not part of the main test suite.

### Utility Scripts

- **`cleanup.py`** - Cross-platform cleanup script that removes Python cache files, tool caches, and temporary files while preserving directory structure (works on Windows, Linux, macOS)
- **`quality.py`** - Cross-platform code quality tool that runs black, ruff, mypy, and pytest. Use `--fix` flag to auto-fix issues (works on Windows, Linux, macOS)  
- **`compare.py`** - Analysis comparison utility (legacy script for H2K vs HPXML comparison)

## Usage

All Python scripts should be run from the project root using:
```bash
uv run python tools/script_name.py
```

This ensures proper path resolution and virtual environment usage.