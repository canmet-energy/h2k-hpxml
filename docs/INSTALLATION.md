# H2K-HPXML Installation Guide

Complete installation instructions for Windows and Linux.

## Requirements
**Windows**: Windows 10/11 (64-bit), PowerShell 5.1+
**Linux**: Ubuntu 20.04+ or equivalent, Python 3.12+


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
### 2. Install Python (3.12)
```bash
uv --native-tls python install 3.12
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


## Verification

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
