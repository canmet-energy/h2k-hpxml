# Quick Start with uv (Recommended) ⚡

The fastest way to get started with H2K-HPXML using `uv` - the modern Python package manager.

## Why Use uv?

- ⚡ **10-100x faster** than pip
- 🔒 **Better dependency isolation**
- 🎯 **More reliable** dependency resolution
- 💾 **Efficient caching** and disk usage
- 🚀 **Modern Python tooling**

## Installation & Test (2 minutes)

### 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell (run as user, no admin needed)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Windows Command Prompt (alternative)
pip install uv

# Verify installation
uv --version
```

### 2. Install H2K-HPXML

```bash
# Create new project (recommended)
uv init h2k-project
cd h2k-project
uv add h2k-hpxml

# OR add to existing project
uv add h2k-hpxml

# OR global installation
uv tool install h2k-hpxml
```

### 3. Setup Dependencies

```bash
uv run h2k-deps --setup
uv run h2k-deps --auto-install
```

### 4. Test Installation

```bash
# Quick test
uv run h2k-deps --check-only

# Full test (integrated command)
uv run h2k-deps --test-installation
```

## Basic Usage Examples

```bash
# Convert single H2K file  
uv run h2k2hpxml house.h2k

# Convert with custom output
uv run h2k2hpxml house.h2k --output results/house.xml

# Convert without simulation (fast)
uv run h2k2hpxml house.h2k --do-not-sim

# Process entire folder (Linux/macOS)
uv run h2k2hpxml /path/to/h2k/files/

# Process entire folder (Windows)
uv run h2k2hpxml "C:\path\to\h2k\files"

# Get help
uv run h2k2hpxml --help
uv run h2k-deps --help
```

### Windows PowerShell Examples

```powershell
# Basic conversion
uv run h2k2hpxml house.h2k

# With output to specific location
uv run h2k2hpxml house.h2k --output "C:\Results\house.xml"

# Process folder with spaces in path
uv run h2k2hpxml "C:\My Documents\H2K Files\"
```

## Expected Success Output

```
🔍 Dependency Check Report
==============================
✅ OpenStudio CLI: /path/to/openstudio
✅ OpenStudio-HPXML found at: /path/to/hpxml

🎉 All dependencies satisfied!

H2K-HPXML Smart Installation Test
========================================
📦 Detected installation method: uv
   Using 'uv run' commands

TEST SUMMARY
==================================================
Installation         ✅ PASS
CLI Tools            ✅ PASS
Dependencies         ✅ PASS
Basic Conversion     ✅ PASS
--------------------------------------------------
Passed: 4/4

🎉 All tests passed! H2K-HPXML is working correctly with uv.
```

## Python API Usage

```python
# In a uv project, create a script (e.g., convert.py)
from h2k_hpxml.api import convert_h2k_file, run_full_workflow

# Convert single file
output_path = convert_h2k_file('input.h2k', 'output.xml')
print(f"Converted: {output_path}")

# Run full workflow
results = run_full_workflow('input.h2k', simulate=True)
print(f"Successful: {results['successful_conversions']}")
```

```bash
# Run your script
uv run python convert.py
```

## Troubleshooting

### ❌ "uv: command not found"
Install uv first (see step 1 above)

### ❌ "h2k2hpxml: command not found"  
Use `uv run h2k2hpxml` instead of direct `h2k2hpxml`

### ❌ Dependencies missing
```bash
uv run h2k-deps --auto-install
```

### ❌ Permission issues
uv installs to user directories by default - no admin rights needed!

### ❌ Want global access to commands
```bash
# Install as a global tool  
uv tool install h2k-hpxml

# Now you can use directly
h2k2hpxml --help
h2k-deps --help
```

## Comparison: uv vs pip

| Feature | uv | pip |
|---------|----|----|
| Installation speed | ⚡ 10-100x faster | Standard |
| Dependency resolution | 🎯 Deterministic | Sometimes conflicts |
| Virtual environments | 🔒 Automatic | Manual setup needed |
| Disk usage | 💾 Efficient caching | Duplicates packages |
| Lockfile support | ✅ Built-in | ❌ Requires extra tools |
| Project isolation | ✅ Excellent | ⚠️ Manual |

## Advanced uv Features

```bash
# Lock dependencies for reproducible builds
uv lock

# Sync exact environment from lockfile
uv sync

# Run in isolated environment
uv run --isolated python script.py

# Add development dependencies
uv add --dev pytest black ruff

# Show project info
uv tree
uv show h2k-hpxml
```

## Docker Alternative (Zero Setup)

If you prefer not to install anything locally:

```bash
# Use pre-built Docker image
docker run -v $(pwd):/data canmet/h2k-hpxml:latest input.h2k

# Interactive shell
docker run -it -v $(pwd):/data canmet/h2k-hpxml:latest bash
```

## Next Steps

Once the test passes:

1. **Start converting**: `uv run h2k2hpxml your_file.h2k`
2. **Read the docs**: Check project README for advanced usage
3. **Join community**: Report issues or contribute on GitHub
4. **Scale up**: Use Docker containers for batch processing

Ready to convert your H2K files to HPXML! 🎉