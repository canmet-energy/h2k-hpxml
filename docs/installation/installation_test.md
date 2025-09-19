# H2K-HPXML Installation Test Guide

This guide helps you verify that H2K-HPXML is properly installed and working after installation via pip or uv.

## Quick Test Steps

### 1. Basic Installation Check

```bash
# Check that the package is installed
python -c "import h2k_hpxml; print('✅ Package imported successfully')"

# Check CLI tools are available (use uv run if installed with uv)
h2k2hpxml --help              # If installed with pip
# OR
uv run h2k2hpxml --help       # If installed with uv

h2k-deps --help               # If installed with pip  
# OR
uv run h2k-deps --help        # If installed with uv
```

### 2. Dependencies Check

```bash
# Check if dependencies are properly configured
h2k-deps --check-only
```

**Expected output**: Should show ✅ for OpenStudio CLI and OpenStudio-HPXML

**If dependencies are missing:**
```bash
# Set up configuration and auto-install dependencies
h2k-deps --setup
h2k-deps --auto-install
```

### 3. Simple Conversion Test

Create a test script or download a sample H2K file:

```bash
# If you have the source code, use a sample file
h2k2hpxml examples/WizardHouse.h2k --output test_output.xml --do-not-sim

# This should create test_output.xml (HPXML format)
ls -la test_output.xml
```

### 4. Python API Test

```python
# Test the Python API
from h2k_hpxml.api import validate_dependencies, convert_h2k_string
from h2k_hpxml.config.manager import ConfigManager

# Check dependencies
deps = validate_dependencies()
print("Dependencies valid:", deps['valid'])

# Check configuration
config = ConfigManager()
print("OpenStudio path:", config.openstudio_binary)
print("EnergyPlus path:", config.energyplus_binary)
```

## Automated Test Script

For convenience, you can run our automated test script:

```bash
# For uv installations
uv run h2k-deps --test-comprehensive

# For pip installations
h2k-deps --test-comprehensive
```

This script will automatically test:
- ✅ Package import and version
- ✅ Dependencies availability  
- ✅ Basic H2K to HPXML conversion
- ✅ Python API functionality
- 🔄 Optional: Full simulation test (slow)

## Expected Results

### Successful Installation
```
🎉 All tests passed! H2K-HPXML is working correctly.

TEST SUMMARY
==================================================
Dependencies         ✅ PASS
Basic Conversion     ✅ PASS  
Python API           ✅ PASS
--------------------------------------------------
Passed: 3/3
```

### Common Issues and Solutions

#### ❌ Dependencies Check Failed
```bash
# Solution: Install dependencies automatically
h2k-deps --auto-install

# Or set up manually
h2k-deps --setup
```

#### ❌ Command Not Found (`h2k2hpxml: command not found`)
The CLI tools may not be in your PATH. Try:
```bash
# Use python -m instead
python -m h2k_hpxml.cli.convert --help

# Or install in development mode if you have the source
pip install -e .
```

#### ❌ OpenStudio Not Found
- **Windows**: The installer will download OpenStudio portable (no admin rights needed)
- **Linux**: May require `sudo` for system installation, or use Docker containers
- **Alternative**: Use the provided Docker containers which have everything pre-installed

#### ❌ Conversion Failed
- Check that your H2K file is valid
- Try with `--debug` flag for more information
- Verify dependencies with `h2k-deps --check-only`

## Platform-Specific Notes

### Windows
- OpenStudio installs to `%LOCALAPPDATA%\OpenStudio-3.9.0`
- No administrator privileges required
- PowerShell commands may be needed for PATH setup

### Linux  
- OpenStudio installs to `/usr/local/openstudio-3.9.0` (system) or user directory
- May require `sudo` for system-wide installation
- Docker containers are recommended for easy setup

### Docker (Recommended)
```bash
# Use pre-built container with all dependencies
docker run -v $(pwd):/data canmet/h2k-hpxml:latest input.h2k
```

## Getting Help

If tests fail:

1. **Check the logs**: Look for specific error messages
2. **Verify sample files**: Ensure you have valid H2K input files  
3. **Try Docker**: Use containers for guaranteed working environment
4. **Report issues**: Create an issue at the project repository with:
   - Test output
   - Operating system
   - Python version
   - Installation method used

## Advanced Testing

For complete verification, you can also run the project's test suite:

```bash
# Run all tests (requires development setup)
pytest tests/

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests  
```

This requires the full development environment and may take several minutes to complete.