# H2K-HPXML Installation Guide

Complete installation guide for all platforms and installation methods.

## Table of Contents

- [Quick Start (Recommended)](#quick-start-recommended)
- [Installation Methods](#installation-methods)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Dependency Management](#dependency-management)
- [Verification and Testing](#verification-and-testing)
- [Troubleshooting](#troubleshooting)
- [Alternative Installation Methods](#alternative-installation-methods)

## Quick Start (Recommended)

### 1. Install uv (Modern Python Package Manager)

**Why uv?** 10-100x faster than pip, better dependency resolution, automatic virtual environments.

**Linux/Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows PowerShell:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (any platform):**
```bash
pip install uv
```

### 2. Install H2K-HPXML

**Global Installation (commands available everywhere):**
```bash
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

**Project Installation:**
```bash
# Create new project
uv init my-h2k-project
cd my-h2k-project
uv add git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Or add to existing project
uv add git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

### 3. Setup Dependencies

```bash
# Setup configuration and auto-install dependencies
h2k-deps --auto-install

# Verify installation
h2k-deps --test-installation
```

### 4. Test with Demo

```bash
# Run interactive demo
h2k-demo

# Or convert a file directly
h2k2hpxml your_file.h2k
```

## Installation Methods

### Method 1: uv Tool (Recommended)

**Best for**: General users who want commands available globally.

```bash
# Install globally
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Update
uv tool upgrade git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Uninstall
uv tool uninstall h2k-hpxml
```

### Method 2: uv Project

**Best for**: Developers or users who want project isolation.

```bash
# Create new environment
uv venv h2k-env --python 3.12
source h2k-env/bin/activate  # Linux/Mac
# or
h2k-env\Scripts\activate     # Windows

# Install package
uv pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Use commands (only when environment is active)
h2k2hpxml --help
```

### Method 3: Traditional pip

**Best for**: Users who prefer traditional Python package management.

```bash
# Create virtual environment
python -m venv h2k-env
source h2k-env/bin/activate  # Linux/Mac
# or
h2k-env\Scripts\activate     # Windows

# Install package
pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

### Method 4: Docker (Zero Setup)

**Best for**: Users who don't want to install anything locally.

```bash
# Convert files using Docker
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k

# See Docker Guide for complete instructions
```

## Platform-Specific Instructions

### Windows Installation

#### Prerequisites
- **Windows 10/11** (64-bit)
- **PowerShell 5.1+** (pre-installed on Windows 10/11)
- **Admin rights** (for initial uv installation only)

#### Step-by-Step

1. **Install uv**:
   ```powershell
   # Open PowerShell as Administrator
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Restart PowerShell** (as regular user) and verify:
   ```powershell
   uv --version
   ```

3. **Install H2K-HPXML**:
   ```powershell
   uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
   ```

4. **Setup dependencies** (automatic OpenStudio installation):
   ```powershell
   h2k-deps --auto-install
   ```

   This automatically:
   - Downloads OpenStudio 3.9.0 portable (no admin rights required)
   - Installs to `%LOCALAPPDATA%\OpenStudio-3.9.0`
   - Downloads OpenStudio-HPXML
   - Configures all paths

5. **Test installation**:
   ```powershell
   h2k-deps --test-installation
   h2k-demo
   ```

#### Windows Troubleshooting

**"Execution policy" errors:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**"Command not found" after installation:**
```powershell
# Restart PowerShell/Command Prompt
# Or manually add to PATH (h2k-deps will help with this)
h2k-deps --add-to-path
```

**OpenStudio installation location:**
- Primary: `%LOCALAPPDATA%\OpenStudio-3.9.0`
- Fallback: `%USERPROFILE%\OpenStudio-3.9.0`

### Linux Installation

#### Prerequisites
- **Ubuntu 20.04+** or **CentOS 8+** (or equivalent)
- **Python 3.12+** (uv can install this automatically)
- **curl** (usually pre-installed)

#### Step-by-Step

1. **Install uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.bashrc  # or restart terminal
   ```

2. **Install H2K-HPXML**:
   ```bash
   uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
   ```

3. **Setup dependencies**:
   ```bash
   # May require sudo for system-wide OpenStudio installation
   sudo h2k-deps --auto-install

   # Alternative: Use Docker for no system modifications
   docker run --rm canmet/h2k-hpxml h2k2hpxml --help
   ```

4. **Test installation**:
   ```bash
   h2k-deps --test-installation
   h2k-demo
   ```

#### Linux Troubleshooting

**Permission errors:**
```bash
# Use sudo for system dependencies
sudo h2k-deps --auto-install

# Or use Docker for no system changes
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k
```

**Python version issues:**
```bash
# uv can install specific Python versions
uv python install 3.12
uv venv --python 3.12
```

### macOS Installation

> ⚠️ **Important**: Automatic dependency installation is **not currently supported** on macOS. OpenStudio and EnergyPlus must be installed manually, or use Docker for zero-setup usage.

#### Recommended: Use Docker (Zero Setup)

```bash
# Install Docker Desktop for Mac
# Then use H2K-HPXML via Docker
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k
```

See the complete [Docker Guide](DOCKER.md) for full instructions.

#### Manual Installation (Advanced Users)

1. **Install uv**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.zshrc  # or restart terminal
   ```

2. **Install H2K-HPXML**:
   ```bash
   uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
   ```

3. **Manual dependency setup** (required):
   - Download and install [OpenStudio 3.9.0](https://github.com/NREL/OpenStudio/releases/tag/v3.9.0) for macOS
   - Download [OpenStudio-HPXML v1.9.1](https://github.com/NREL/OpenStudio-HPXML/releases/tag/v1.9.1)
   - Configure paths manually:
     ```bash
     h2k-deps --setup
     # Follow prompts to specify custom paths
     ```

4. **Test installation**:
   ```bash
   h2k-deps --check-only  # Verify dependencies
   h2k-demo              # If dependencies are configured
   ```

#### macOS Troubleshooting

**Automatic installation not supported:**
```bash
# h2k-deps --auto-install will show unsupported platform error
# Use Docker instead for easiest setup
docker run --rm canmet/h2k-hpxml h2k2hpxml --help
```

**Manual OpenStudio setup:**
```bash
# After manual OpenStudio installation, check if detected
h2k-deps --check-only

# If not detected, use interactive setup
h2k-deps --setup
```

**Gatekeeper issues with manual installation:**
```bash
# Allow OpenStudio to run if blocked
sudo xattr -rd com.apple.quarantine /path/to/openstudio-3.9.0/
```

## Dependency Management

H2K-HPXML requires several external dependencies that are managed by the `h2k-deps` command.

### Required Dependencies

1. **OpenStudio 3.9.0** - Building modeling and simulation platform
2. **OpenStudio-HPXML 1.9.1** - NREL's HPXML implementation
3. **EnergyPlus** - Simulation engine (included with OpenStudio)
4. **Weather data files** - Canadian CWEC2020 weather files

### Dependency Commands

```bash
# Check current status
h2k-deps --check-only

# Interactive setup (first time)
h2k-deps --setup

# Automatic installation
h2k-deps --auto-install

# Update existing installation
h2k-deps --update-config

# Test comprehensive installation
h2k-deps --test-comprehensive
```

### Manual Dependency Installation

If automatic installation fails, you can install dependencies manually:

#### OpenStudio 3.9.0

**Windows:**
1. Download from [OpenStudio Releases](https://github.com/NREL/OpenStudio/releases/tag/v3.9.0)
2. Use portable `.tar.gz` version (no admin required)
3. Extract to `%LOCALAPPDATA%\OpenStudio-3.9.0`

**Linux:**
```bash
# Ubuntu/Debian
wget https://github.com/NREL/OpenStudio/releases/download/v3.9.0/OpenStudio-3.9.0+bb9481519e-Ubuntu-20.04-x86_64.deb
sudo dpkg -i OpenStudio-3.9.0+bb9481519e-Ubuntu-20.04-x86_64.deb
```

**macOS:**
```bash
# Download .dmg from GitHub releases (manual installation required)
# Visit: https://github.com/NREL/OpenStudio/releases/tag/v3.9.0
# Look for macOS .dmg file in Assets section
# Install via GUI, then configure with h2k-deps --setup
```

#### OpenStudio-HPXML

```bash
# Download and extract
wget https://github.com/NREL/OpenStudio-HPXML/archive/refs/tags/v1.9.1.zip
unzip v1.9.1.zip -d /path/to/openstudio-hpxml/
```

#### Configuration

After manual installation, update configuration:

```bash
h2k-deps --setup
# Follow prompts to specify custom paths
```

## Verification and Testing

### Basic Verification

```bash
# 1. Check package installation
python -c "import h2k_hpxml; print('✅ Package imported successfully')"

# 2. Check CLI commands
h2k2hpxml --help
h2k-deps --help
h2k-demo --help

# 3. Check dependencies
h2k-deps --check-only
```

Expected output:
```
🔍 Dependency Check Report
==============================
✅ OpenStudio CLI: /path/to/openstudio
✅ OpenStudio-HPXML found at: /path/to/hpxml
✅ Weather files configured

🎉 All dependencies satisfied!
```

### Installation Testing

```bash
# Quick test (30 seconds)
h2k-deps --test-quick

# Smart test (auto-detects installation method)
h2k-deps --test-installation

# Comprehensive test (5-10 minutes)
h2k-deps --test-comprehensive
```

Expected output:
```
H2K-HPXML Installation Test
========================================
📦 Detected installation method: uv tool
   Commands available globally

TEST SUMMARY
==================================================
Installation         ✅ PASS
CLI Tools            ✅ PASS
Dependencies         ✅ PASS
Basic Conversion     ✅ PASS
--------------------------------------------------
Passed: 4/4

🎉 All tests passed! H2K-HPXML is working correctly.
```

### Interactive Demo

```bash
# English demo
h2k-demo

# French demo
h2k-demo --lang fr
```

The demo provides:
- Guided file selection
- Step-by-step conversion process
- Explanation of output files
- Real conversion results

### Manual Testing

```bash
# Test with example file (if you have access to source)
h2k2hpxml examples/WizardHouse.h2k --do-not-sim

# Test with your own file
h2k2hpxml /path/to/your/file.h2k --output results.xml

# Test batch processing
h2k2hpxml /path/to/folder/ --output results/
```

## Troubleshooting

### Common Issues

#### 1. "Command not found: h2k2hpxml"

**uv tool installation:**
```bash
# Check if tool is installed
uv tool list

# Reinstall if needed
uv tool uninstall h2k-hpxml
uv tool install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Check PATH
echo $PATH | grep -i uv
```

**Traditional installation:**
```bash
# Use Python module syntax
python -m h2k_hpxml.cli.convert --help

# Check if in PATH
which h2k2hpxml
pip show h2k-hpxml
```

#### 2. "OpenStudio not found"

```bash
# Check current status
h2k-deps --check-only

# Auto-install
h2k-deps --auto-install

# Manual configuration
h2k-deps --setup
```

#### 3. "Permission denied" (Linux/Mac)

```bash
# Use sudo for system installation
sudo h2k-deps --auto-install

# Or use user-only installation
h2k-deps --setup  # Choose user directory

# Alternative: Use Docker
docker run --rm canmet/h2k-hpxml h2k2hpxml --help
```

#### 4. Python version incompatibility

```bash
# Check Python version
python --version

# Use uv to manage Python versions
uv python install 3.12
uv venv --python 3.12
```

#### 5. Network/Download issues

```bash
# Install from GitHub repository
pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Or download manually and install offline
pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor --no-index --find-links /path/to/wheels/
```

### Platform-Specific Issues

#### Windows

**PowerShell execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**PATH issues:**
```powershell
# Let h2k-deps fix PATH
h2k-deps --add-to-path

# Or manually add uv tools directory to PATH
$env:PATH += ";$env:USERPROFILE\.local\bin"
```

**WSL interference:**
```powershell
# Use native Windows Python, not WSL
where python
# Should show Windows path, not /usr/bin/python
```

#### Linux

**Missing system dependencies:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

**OpenStudio installation fails:**
```bash
# Try manual download
wget https://github.com/NREL/OpenStudio/releases/download/v3.9.0/OpenStudio-3.9.0+bb9481519e-Ubuntu-20.04-x86_64.deb
sudo dpkg -i OpenStudio-3.9.0+bb9481519e-Ubuntu-20.04-x86_64.deb

# Fix dependencies if needed
sudo apt --fix-broken install
```

#### macOS

**No automatic dependency installation:**
```bash
# This will fail on macOS
h2k-deps --auto-install
# Error: ❌ Unsupported platform: Darwin

# Recommended solution: Use Docker
docker run --rm canmet/h2k-hpxml h2k2hpxml --help
```

**Manual installation challenges:**
- OpenStudio 3.9.0 may not have macOS releases
- EnergyPlus compatibility issues
- Complex manual configuration required

**Best solution for macOS:**
```bash
# Use Docker for guaranteed compatibility
docker run --rm -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/input.h2k
```

### Getting Help

If issues persist:

1. **Run diagnostics**:
   ```bash
   h2k-deps --test-comprehensive 2>&1 | tee diagnosis.log
   ```

2. **Check system info**:
   ```bash
   uv --version
   python --version
   which h2k2hpxml
   ```

3. **Report issue** with:
   - Operating system and version
   - Python version
   - Installation method used
   - Complete error output
   - Diagnosis log

## Alternative Installation Methods

### Development Installation

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/canmet-energy/h2k-hpxml.git
cd h2k-hpxml

# Install in development mode
uv pip install -e '.[dev]'

# Setup dependencies
h2k-deps --setup
h2k-deps --auto-install

# Run tests
pytest tests/unit/
```

### Docker Development

```bash
# Clone repository
git clone https://github.com/canmet-energy/h2k-hpxml.git
cd h2k-hpxml

# Open in VSCode with DevContainer
code .
# Select "Reopen in Container" when prompted
```

### Offline Installation

For environments without internet access:

1. **Download packages** on connected machine:
   ```bash
   pip download git+https://github.com/canmet-energy/h2k-hpxml.git@refactor -d packages/
   ```

2. **Transfer to offline machine** and install:
   ```bash
   pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor --no-index --find-links packages/
   ```

3. **Manual dependency setup**:
   - Download OpenStudio and OpenStudio-HPXML manually
   - Use `h2k-deps --setup` to configure paths

### Virtual Environment with specific Python version

```bash
# Using uv
uv venv h2k-env --python 3.12
source h2k-env/bin/activate
uv pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor

# Using pyenv + virtualenv
pyenv install 3.12.0
pyenv virtualenv 3.12.0 h2k-env
pyenv activate h2k-env
pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
```

## Next Steps

After successful installation:

1. **Try the demo**: `h2k-demo`
2. **Read the user guide**: [USER_GUIDE.md](USER_GUIDE.md)
3. **Convert your files**: `h2k2hpxml your_file.h2k`
4. **Explore other tools**: `h2k-resilience`, `h2k-deps`
5. **Use as library**: See [LIBRARY.md](LIBRARY.md)
6. **Docker usage**: See [DOCKER.md](DOCKER.md)

Welcome to H2K-HPXML! 🎉