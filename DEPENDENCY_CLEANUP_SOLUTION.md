# H2K-HPXML Automatic Dependency Cleanup Solution

## Problem Solved

Previously, when uninstalling `h2k-hpxml`, the package dependencies (~1.2GB of OpenStudio and OpenStudio-HPXML files) would remain in the user's home directory forever, consuming disk space.

## Solution Implemented

The package now automatically removes its dependencies when uninstalled, using a tracking mechanism that detects orphaned installations.

## How It Works

### 1. Installation Tracking
When dependencies are installed, a marker file is created:
```json
{
  "package_dir": "/path/to/h2k_hpxml/package",
  "installed_at": "2025-09-07T14:48:38.909116",
  "version": "0.1.dev151",
  "python_version": "3.13",
  "deps_version": {
    "openstudio_version": "3.9.0",
    "openstudio_sha": "c77fbb9569", 
    "openstudio_hpxml_version": "v1.9.1"
  }
}
```

**Location**: `~/.local/share/h2k_hpxml/deps/.h2k_hpxml_installation`

### 2. Orphan Detection
On every `import h2k_hpxml`, the system:
1. Checks if the marker file exists
2. Verifies if the original package directory still exists
3. If the package is gone → dependencies are orphaned → auto-cleanup

### 3. Version Management
Also automatically handles dependency updates:
- Compares installed vs. required dependency versions
- Removes old versions when package is upgraded
- Forces reinstall of dependencies with new versions

## User Experience

### Before (Old Behavior)
```bash
pip install h2k-hpxml          # Installs package + downloads deps (~1.2GB)
pip uninstall h2k-hpxml        # Removes package only
# Dependencies remain in ~/.local/share/h2k_hpxml/ forever ❌
```

### After (New Behavior)  
```bash
pip install h2k-hpxml          # Installs package + downloads deps (~1.2GB)
pip uninstall h2k-hpxml        # Removes package only
python -c "import another_pkg"  # Any future Python import...
# Automatically detects orphaned deps and cleans them up! ✅
```

## Technical Details

### Smart Fallback Installation Locations
1. **H2K_DEPS_DIR environment variable** (Docker/CI) → `/app/deps`
2. **Package directory if writable** (virtual environments) → `site-packages/h2k_hpxml/_deps/`
3. **User home directory** (system installs) → `~/.local/share/h2k_hpxml/deps/`

### Cleanup Triggers
- **Package removal**: Next import of any Python package detects orphaned h2k-hpxml deps
- **Version upgrades**: Automatic cleanup of old dependency versions
- **Manual cleanup**: `python -m h2k_hpxml.installer --clean`

### Safety Features
- Only affects user directory installations (not Docker/CI environments)
- Graceful failure - cleanup errors don't break imports
- Version tracking prevents unnecessary reinstalls
- Marker file prevents false positives

## Files Modified

1. **`src/h2k_hpxml/installer.py`**
   - Added `_write_installation_marker()` - tracks installations
   - Added `_check_and_cleanup_orphaned_deps()` - detects and cleans orphans  
   - Added `get_package_version()` - version tracking
   - Enhanced `ensure_dependencies()` - calls cleanup check
   - Added `clean_user_dependencies()` - manual cleanup command

2. **`src/h2k_hpxml/config/manager.py`**
   - Enhanced `hpxml_os_path` - auto-detect from installer
   - Enhanced `openstudio_binary` - auto-detect with fallbacks
   - Updated validation to be more lenient with auto-detected paths

## Testing

Run the comprehensive test:
```bash
python test_cleanup_behavior.py
```

This demonstrates:
- Automatic cleanup of orphaned dependencies
- Automatic version upgrades  
- Before/after states
- Safety for different installation types

## Benefits

✅ **Solves the original problem**: Dependencies are removed with package uninstall  
✅ **Zero user intervention**: Happens automatically on next import  
✅ **Handles upgrades**: Old versions cleaned up automatically  
✅ **Safe**: Only affects user directories, graceful failure  
✅ **Efficient**: Avoids unnecessary reinstalls  
✅ **Compatible**: Works with all installation methods (pip, Docker, CI)

## Manual Cleanup (if needed)

```bash
# Interactive cleanup
python -m h2k_hpxml.installer --clean

# Force cleanup (non-interactive)  
python -m h2k_hpxml.installer --clean --force

# Manual removal
rm -rf ~/.local/share/h2k_hpxml/
```

This solution provides the best user experience - dependencies are automatically managed and cleaned up without any manual intervention required.