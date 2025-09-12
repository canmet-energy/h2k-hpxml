# H2K-HPXML Scripts

This directory contains various scripts for testing and development of the H2K-HPXML package.

## Installation Scripts (`installation/`)

User-facing scripts for testing package installation and functionality:

### `smart_test.py`
- **Purpose**: Intelligent test that automatically detects whether you're using pip or uv installation
- **Target**: End users who have installed h2k-hpxml with either `pip install h2k-hpxml` or `uv add h2k-hpxml`
- **Features**: 
  - Auto-detects installation method (pip vs uv)
  - Runs comprehensive installation tests
  - Tests dependencies, CLI tools, and basic conversion
  - Works on Windows, macOS, and Linux

### `quick_test.py`
- **Purpose**: Quick verification of basic package functionality
- **Target**: Users who want a fast installation check
- **Features**:
  - Package import test
  - CLI tools availability
  - Basic dependency check
  - Configuration validation

### `test_installation.py`
- **Purpose**: Comprehensive installation testing suite
- **Target**: Users who want thorough verification
- **Features**:
  - Complete dependency validation
  - Full conversion test with example files
  - Python API testing
  - Detailed error reporting

## Development Scripts (`development/`)

Development and demonstration scripts for maintainers and contributors:

### `demo_windows_paths.py`
- **Purpose**: Demonstrates how example file discovery works on Windows
- **Target**: Developers understanding cross-platform path handling
- **Features**:
  - Simulates Windows installation paths
  - Shows pathlib.Path behavior on different platforms
  - Demonstrates example file discovery mechanism

### `install_and_test.py`
- **Purpose**: Installation helper with guided setup
- **Target**: Developers and advanced users
- **Features**:
  - Interactive installation guidance
  - Multiple installation method support
  - Guided dependency setup

### `test_windows.py`
- **Purpose**: Windows-specific functionality testing
- **Target**: Developers testing Windows compatibility
- **Features**:
  - Windows path handling tests
  - Platform-specific functionality validation
  - Windows-specific configuration testing

## Usage

### For End Users (Installation Testing)

Download and run the appropriate test script:

```bash
# Smart test (recommended) - auto-detects your installation
curl -O https://raw.githubusercontent.com/canmet-energy/h2k-hpxml/main/scripts/installation/smart_test.py
python smart_test.py

# Quick test - fast verification
curl -O https://raw.githubusercontent.com/canmet-energy/h2k-hpxml/main/scripts/installation/quick_test.py  
python quick_test.py

# Comprehensive test - thorough verification
curl -O https://raw.githubusercontent.com/canmet-energy/h2k-hpxml/main/scripts/installation/test_installation.py
python test_installation.py
```

### For Developers

Clone the repository and run development scripts directly:

```bash
# Example file path discovery demo
python scripts/development/demo_windows_paths.py

# Installation helper
python scripts/development/install_and_test.py

# Windows-specific testing
python scripts/development/test_windows.py
```

## Notes

- All installation scripts are designed to work independently and can be downloaded from GitHub
- Development scripts assume you have the full repository cloned
- Scripts are tested on Windows 10+, macOS, and Linux
- curl is available by default on Windows 10+ (build 17063+)