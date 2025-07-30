# Cross-Platform Dependency Checking & Auto-Installation Strategy

## Overview
Create a robust dependency validation and automated installation system for OpenStudio and OpenStudio-HPXML that works on both Windows and Linux systems.

## Requirements
- **OpenStudio**: Version 3.9.0 (with Python bindings)
- **OpenStudio-HPXML**: Version v1.9.1
- **Cross-platform support**: Windows and Linux
- **Default paths**: `/OpenStudio-HPXML/` for OpenStudio-HPXML

## Implementation Plan

### 1. Core Dependency Manager Module
**File**: `src/h2k_hpxml/utils/dependencies.py`

**Features**:
- Cross-platform detection (Windows/Linux)
- Version validation for OpenStudio (3.9.0) and OpenStudio-HPXML (v1.9.1)
- Automated download and installation
- User prompts for consent
- Configuration management

### 2. Integration Points
**Files to modify**:
- `src/h2k_hpxml/cli/resilience.py` - Add dependency check at startup
- `src/h2k_hpxml/cli/convert.py` - Add dependency check at startup

### 3. Detection Strategy

**OpenStudio Detection**:
- Check Python bindings: `import openstudio; openstudio.openStudioVersion()`
- Check CLI binary: `openstudio --version`
- Platform-specific paths:
  - Windows: `C:\openstudioXX\bin\openstudio.exe`, `C:\Program Files\OpenStudio X.X.X\bin\`
  - Linux: `/usr/local/bin/openstudio`, `/usr/bin/openstudio`

**OpenStudio-HPXML Detection**:
- Check default path: `/OpenStudio-HPXML/`
- Validate workflow script: `workflow/run_simulation.rb`
- Check version in documentation or README files

### 4. Auto-Installation Strategy

**OpenStudio**:
- Windows:
  - Download .exe installer from GitHub releases
  - Run silent installation: `/S` flag
  - Update system PATH
- Linux:
  - Download .deb package for Ubuntu/Debian
  - Download .tar.gz for other distributions
  - Install via package manager or extract to `/usr/local/`
- URLs: `https://github.com/NREL/OpenStudio/releases/download/v3.9.0/`

**OpenStudio-HPXML**:
- Download from: `https://github.com/NREL/OpenStudio-HPXML/releases/download/v1.9.1/`
- Extract to `/OpenStudio-HPXML/`
- Set proper permissions (Linux)
- Validate workflow script exists

### 5. User Experience Features
- Interactive prompts with clear explanations
- Progress indicators for downloads
- Automatic PATH updates where possible
- Backup/rollback for failed installations
- Skip options for advanced users (`--skip-deps` flag)
- Configuration persistence
- Clear error messages with manual installation instructions

### 6. CLI Integration
- Run dependency check before any major operations
- Add `--skip-deps` flag for advanced users
- Add `--check-deps` command for standalone validation
- Graceful error messages with installation guidance
- Support for custom installation paths via environment variables

### 7. Configuration Updates
- Update `conversionconfig.ini` with detected paths
- Support environment variables:
  - `OPENSTUDIO_PATH`
  - `OPENSTUDIO_HPXML_PATH`
- User preference storage for installation choices

## Implementation Details

### Dependency Manager Class Structure
```python
class DependencyManager:
    def check_openstudio()
    def check_openstudio_hpxml()
    def install_openstudio()
    def install_openstudio_hpxml()
    def validate_versions()
    def update_configuration()
```

### CLI Integration Pattern
```python
def main():
    # Check dependencies before main operations
    if not skip_deps:
        dependency_manager = DependencyManager()
        dependency_manager.validate_all()

    # Continue with normal CLI operations
    ...
```

## Error Handling
- Network connectivity issues
- Permission errors during installation
- Version conflicts
- Path resolution failures
- User cancellation scenarios

## Testing Strategy
- Unit tests for each detection method
- Integration tests on both Windows and Linux
- Mock tests for network operations
- CI/CD pipeline validation

## Benefits
- Seamless user onboarding experience
- Reduced support burden for installation issues
- Cross-platform compatibility
- Version consistency across installations
- Automated CI/CD compatibility
- Professional user experience

## Files to Create/Modify
1. **NEW**: `src/h2k_hpxml/utils/dependencies.py` (main dependency manager)
2. **MODIFY**: `src/h2k_hpxml/cli/resilience.py` (add startup check)
3. **MODIFY**: `src/h2k_hpxml/cli/convert.py` (add startup check)
4. **UPDATE**: `pyproject.toml` (add dependencies: requests, packaging)

## Usage Examples

### Automatic Installation
```bash
python -m h2k_hpxml.cli.resilience input.h2k
# Automatically detects missing dependencies and prompts for installation
```

### Skip Dependency Check
```bash
python -m h2k_hpxml.cli.resilience input.h2k --skip-deps
# Skips dependency validation for advanced users
```

### Standalone Dependency Check
```bash
python -m h2k_hpxml.cli.resilience --check-deps
# Only validates dependencies without running main functionality
```

This comprehensive approach ensures reliable, user-friendly dependency management across platforms while maintaining flexibility for advanced users and automated environments.
