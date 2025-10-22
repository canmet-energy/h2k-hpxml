# H2K-HPXML Installation Guide

Complete installation instructions for Windows and Linux.

## Quick Start (5 Minutes)

### 1. Install uv Package Manager

**Windows PowerShell:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install H2K-HPXML Globally

```bash
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

### 3. Setup Dependencies

```bash
# Automatic installation (no admin rights needed on Windows)
os-setup --auto-install

# Verify installation
os-setup --test-installation
```

### 4. Try the Demo

```bash
h2k-demo                    # Interactive demo
h2k-hpxml your_file.h2k     # Convert a file
```

**That's it!** You're ready to use H2K-HPXML.

---

## Platform-Specific Instructions

### Windows

**Prerequisites**: Windows 10/11 (64-bit), PowerShell 5.1+

**Complete Installation:**
```powershell
# 1. Install uv (one-time setup)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Restart PowerShell, then install H2K-HPXML
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# 3. Auto-install dependencies (portable, no admin required)
os-setup --auto-install

# 4. Test
h2k-demo
```

**Dependencies are installed to**: `%LOCALAPPDATA%\OpenStudio-3.9.0` (~500MB)

**Troubleshooting:**
- **"Command not found"**: Restart PowerShell or run `os-setup --add-to-path`
- **Execution policy errors**: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Linux

**Prerequisites**: Ubuntu 20.04+ or equivalent, Python 3.12+

**Complete Installation:**
```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.bashrc

# 2. Install H2K-HPXML
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# 3. Auto-install dependencies (may require sudo)
sudo os-setup --auto-install

# 4. Test
h2k-demo
```

**Troubleshooting:**
- **Permission errors**: Use `sudo os-setup --auto-install` or [Docker](#docker-installation)
- **Missing dependencies**: `sudo apt install build-essential python3-dev`

---

## Alternative Installation Methods

### Docker (Zero Setup)

Works on Windows and Linux:

```bash
# Convert single file
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/input.h2k

# Batch process folder
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/

# With hourly outputs
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k-hpxml /data/input.h2k --hourly ALL
```

See [DOCKER.md](DOCKER.md) for complete guide.

### Python Project/Virtual Environment

For isolated installations:

```bash
# Create virtual environment
uv venv h2k-env --python 3.12
source h2k-env/bin/activate     # Linux
h2k-env\Scripts\activate        # Windows

# Install
uv pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Setup dependencies
os-setup --auto-install
```

### Traditional pip

```bash
# In a virtual environment
pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
os-setup --auto-install
```

### Development Installation

For contributors:

```bash
git clone https://github.com/canmet-energy/h2k-hpxml.git
cd h2k-hpxml
uv pip install -e '.[dev]'
os-setup --auto-install
pytest tests/unit/
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for complete development setup.

---

## Dependency Management

H2K-HPXML requires:
- **OpenStudio 3.9.0** - Building simulation platform
- **OpenStudio-HPXML 1.9.1** - NREL's HPXML implementation
- **EnergyPlus** - Simulation engine (included with OpenStudio)
- **Weather data** - Canadian CWEC2020 files

### Dependency Commands

```bash
os-setup --check-only           # Check installation status
os-setup --auto-install         # Auto-install all dependencies
os-setup --setup                # Interactive setup
os-setup --test-installation    # Quick test (30 sec)
os-setup --test-comprehensive   # Full test (5-10 min)
```

### Manual Dependency Installation

If auto-install fails:

**Windows:**
1. Download [OpenStudio 3.9.0 portable](https://github.com/NREL/OpenStudio/releases/tag/v3.9.0) (.tar.gz)
2. Extract to `%LOCALAPPDATA%\OpenStudio-3.9.0`
3. Download [OpenStudio-HPXML v1.9.1](https://github.com/NREL/OpenStudio-HPXML/releases/tag/v1.9.1)
4. Run `os-setup --setup` to configure paths

**Linux:**
```bash
# Ubuntu/Debian
wget https://github.com/NREL/OpenStudio/releases/download/v3.9.0/OpenStudio-3.9.0+bb9481519e-Ubuntu-20.04-x86_64.deb
sudo dpkg -i OpenStudio-3.9.0+bb9481519e-Ubuntu-20.04-x86_64.deb
os-setup --setup
```

---

## Verification

### Quick Test

```bash
# Verify package
python -c "import h2k_hpxml; print('✅ Package OK')"

# Check CLI commands
h2k-hpxml --help
h2k-demo --help

# Check dependencies
os-setup --check-only
```

**Expected output:**
```
🔍 Dependency Check Report
==============================
✅ OpenStudio CLI: /path/to/openstudio
✅ OpenStudio-HPXML found
✅ Weather files configured

🎉 All dependencies satisfied!
```

### Full Test

```bash
# Quick test (30 seconds)
os-setup --test-installation

# Comprehensive test (5-10 minutes)
os-setup --test-comprehensive

# Interactive demo
h2k-demo
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Command not found: h2k-hpxml" | Restart terminal or run `os-setup --add-to-path` (Windows) |
| "OpenStudio not found" | Run `os-setup --auto-install` or `os-setup --check-only` |
| Permission errors (Linux) | Use `sudo os-setup --auto-install` or Docker |
| Python version issues | `uv python install 3.12` then `uv venv --python 3.12` |

### Platform-Specific Issues

**Windows:**
```powershell
# Execution policy
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Fix PATH
os-setup --add-to-path
```

**Linux:**
```bash
# Install system dependencies
sudo apt update && sudo apt install build-essential python3-dev

# Fix broken dependencies
sudo apt --fix-broken install
```

### Getting Help

If issues persist:

1. Run diagnostics:
   ```bash
   os-setup --test-comprehensive 2>&1 | tee diagnosis.log
   ```

2. Report issue with:
   - OS and version
   - Python version (`python --version`)
   - Installation method
   - Error output and diagnosis log

---

## Next Steps

After installation:

1. **Try the demo**: `h2k-demo`
2. **Convert files**: `h2k-hpxml your_file.h2k`
3. **Read guides**:
   - [User Guide](USER_GUIDE.md) - CLI usage and workflows
   - [API Reference](API.md) - Python API documentation
   - [Docker Guide](DOCKER.md) - Container usage
   - [Development Guide](DEVELOPMENT.md) - Contributing

Welcome to H2K-HPXML! 🎉
