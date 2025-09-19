# Testing H2K-HPXML After Installation

After installing h2k-hpxml with either:
- `pip install h2k-hpxml` (traditional method)
- `uv add h2k-hpxml` (faster, modern method - **recommended**)

**Why uv?** 
- ⚡ **10-100x faster** than pip for installation and dependency resolution
- 🔒 **Better isolation** - creates project-specific virtual environments
- 🎯 **More reliable** - deterministic dependency resolution
- 💾 **Smaller disk usage** - smart caching and linking

Follow these steps to verify everything is working correctly.

## Method 1: Smart Auto-Detection Test 🤖 (Recommended)

```bash
# For uv installations
uv run h2k-deps --test-installation

# For pip installations
h2k-deps --test-installation
```

This command automatically detects whether you're using uv or pip and runs appropriate tests.
```

## Method 2: Step-by-Step Manual Test 📋

### Step 1: Check Package Installation
```bash
python -c "import h2k_hpxml; print('✅ Package installed')"
```

### Step 2: Verify CLI Tools
```bash
# For pip installations
h2k2hpxml --help     # Should show help text
h2k-deps --help      # Should show help text

# For uv installations
uv run h2k2hpxml --help     # Should show help text
uv run h2k-deps --help      # Should show help text
```

### Step 3: Check Dependencies
```bash
# For pip installations
h2k-deps --check-only

# For uv installations  
uv run h2k-deps --check-only
```
**Expected**: ✅ messages for OpenStudio CLI and OpenStudio-HPXML

### Step 4: Test Basic Conversion
```bash
# For pip installations
h2k2hpxml your_file.h2k --output test.xml --do-not-sim

# For uv installations
uv run h2k2hpxml your_file.h2k --output test.xml --do-not-sim
```

## Method 3: Alternative Test Commands 🧪

### Quick Test (30 seconds)
```bash
# For uv installations
uv run h2k-deps --test-quick

# For pip installations
h2k-deps --test-quick
```

### Comprehensive Test (5-10 minutes)
```bash
# For uv installations
uv run h2k-deps --test-comprehensive

# For pip installations
h2k-deps --test-comprehensive
```

## Expected Success Output

You should see something like:
```
🔍 Dependency Check Report
==============================
✅ OpenStudio CLI: /path/to/openstudio
✅ OpenStudio-HPXML found at: /path/to/hpxml

🎉 All dependencies satisfied!
```

## Common Issues & Solutions

### ❌ "h2k2hpxml: command not found"

**Solution 1**: Use Python module syntax
```bash
python -m h2k_hpxml.cli.convert --help
```

**Solution 2**: Check if CLI scripts are in PATH
```bash
pip show -f h2k-hpxml | grep console_scripts
```

### ❌ "OpenStudio CLI not found"

**Windows users**:
```bash
h2k-deps --auto-install  # Installs OpenStudio automatically
```

**Linux users**:
```bash
sudo h2k-deps --auto-install  # May need sudo for system install
```

**Docker alternative** (no installation needed):
```bash
docker run -v $(pwd):/data canmet/h2k-hpxml:latest your_file.h2k
```

### ❌ "OpenStudio-HPXML not found"

```bash
h2k-deps --auto-install  # Downloads and installs OpenStudio-HPXML
```

### ❌ Permission errors

**Windows**: OpenStudio installs to user directory (no admin rights needed)
**Linux**: Use `sudo h2k-deps --auto-install` or Docker containers

## Platform-Specific Quick Tests

### Windows PowerShell
```powershell
python -c "import h2k_hpxml; print('Package OK')" ; h2k-deps --check-only
```

### Linux/macOS
```bash
python3 -c "import h2k_hpxml; print('Package OK')" && h2k-deps --check-only
```

### Docker (Zero Setup)
```bash
# Test without any installation
docker run canmet/h2k-hpxml:latest --help
```

## Troubleshooting

If any test fails:

1. **Reinstall dependencies**:
   ```bash
   h2k-deps --setup       # Interactive setup
   h2k-deps --auto-install # Automatic installation
   ```

2. **Check Python environment**:
   ```bash
   python -c "import sys; print(sys.executable)"
   pip list | grep h2k
   ```

3. **Use Docker** (guaranteed to work):
   ```bash
   docker run -v $(pwd):/data canmet/h2k-hpxml:latest input.h2k
   ```

4. **Report issues**: If problems persist, create an issue with:
   - Operating system and version
   - Python version (`python --version`)
   - Complete error output
   - Installation method used

## Advanced Verification

For developers or thorough testing:

```bash
# Run the project's full test suite (requires source code)
git clone https://github.com/canmet-energy/h2k-hpxml.git
cd h2k-hpxml
pip install -e ".[dev]"
pytest tests/ -v
```

## Success Indicators

✅ All CLI commands work (`h2k2hpxml`, `h2k-deps`)  
✅ Dependencies are found (OpenStudio, OpenStudio-HPXML)  
✅ Basic conversion completes without errors  
✅ Configuration files are properly set up  
✅ Python API imports work correctly  

Once these are working, you're ready to use H2K-HPXML for converting your H2K files to HPXML format!