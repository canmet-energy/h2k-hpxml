# Dependency Install/Uninstall Methods - Implementation Plan

## Overview
This document outlines a phased approach to fix issues identified in the h2k-hpxml dependency management system. The fixes are organized by priority and dependency relationships.

## Phase 1: Critical Fixes (High Priority) ✅ COMPLETED
**Timeline: Immediate**
**Goal: Fix breaking issues that affect core functionality**

### 1.1 Fix Orphan Detection for Editable Installs ✅ DONE
**Issue**: Dependencies not cleaned up for `pip install -e .` installations
**Location**: `installer.py:330-394` (`_check_and_cleanup_orphaned_deps`)
**Solution**:
- Use `importlib.metadata.distribution('h2k-hpxml')` to check if package is actually installed
- Fall back to directory check only if metadata check fails
- Add check for `.egg-link` files in site-packages for editable installs
**Implementation**: Added `_is_package_installed()` function using `importlib.metadata` with .egg-link fallback for editable installs. Enhanced `_check_and_cleanup_orphaned_deps()` to use proper package detection.

### 1.2 Fix Windows OpenStudio Installation ✅ DONE
**Issue**: Windows .exe installer downloaded but not extracted
**Location**: `installer.py:257-267` (`install_openstudio`)
**Solution**:
- Implement automatic extraction using `msiexec /a` command
- Fall back to 7-zip if available (`7z x` command)
- Provide clear instructions if automatic extraction fails
- Add Windows-specific extraction logic
**Implementation**: Added `_extract_windows_installer()` with multiple extraction methods: `msiexec /a`, `7z x`, and `expand` commands. Integrated into `install_openstudio()` with proper fallback logic.

### 1.3 Fix Marker File Location Consistency ✅ DONE
**Issue**: Marker file written to wrong directory during updates
**Location**: `installer.py:390` (`_check_and_cleanup_orphaned_deps`)
**Solution**:
- Ensure marker is always written to the actual deps directory being used
- Pass correct directory path to `_write_installation_marker()`
- Update marker when moving between directory locations
**Implementation**: Created `_write_installation_marker_to_dir()` function to ensure consistent marker placement. Updated all marker writing calls to use the correct directory path.

## Phase 2: Path and Structure Fixes (Medium Priority) ✅ COMPLETED
**Timeline: Week 1**
**Goal: Ensure correct handling of directory structures and paths**

### 2.1 Fix OpenStudio-HPXML Nested Directory Structure ✅ DONE
**Issue**: Incorrect handling of nested extraction path
**Location**: `installer.py:223-224` (`install_openstudio_hpxml`)
**Solution**:
- Check for nested `OpenStudio-HPXML/OpenStudio-HPXML` structure
- Move inner directory to expected location if nested
- Clean up empty parent directory after move
- Verify structure after extraction
**Implementation**: Added comprehensive nested directory detection and fixing logic with temporary directory moves. Added verification of final structure with workflow file check.

### 2.2 Normalize Cross-Platform Path Handling ✅ DONE
**Issue**: Mixed path separators on Windows
**Location**: `installer.py:26` (`_get_user_data_dir`)
**Solution**:
- Use `Path.joinpath()` consistently
- Ensure all paths use `pathlib.Path` objects
- Let pathlib handle OS-specific separators
- Test on both Windows and Linux
**Implementation**: Code review confirmed path handling already uses `pathlib.Path` consistently throughout. The few `str()` conversions are necessary for external tool compatibility.

### 2.3 Add Recursion Protection to Permission Checks ✅ DONE
**Issue**: Potential infinite recursion in permission checks
**Location**: `installer.py:39` (`_has_write_access`)
**Solution**:
- Add maximum recursion depth (e.g., 10 levels)
- Convert to iterative approach using loop
- Add safeguard against filesystem loops
- Return False if max depth reached
**Implementation**: Replaced recursive approach with iterative loop using `max_depth = 10`. Added `Path.resolve()` to handle symlinks and relative paths properly.

## Phase 3: Reliability Improvements (Medium Priority)
**Timeline: Week 2**
**Goal: Improve reliability and recoverability of operations**

### 3.1 Make Cleanup Operations Atomic
**Issue**: Partial cleanup leaves inconsistent state
**Location**: `installer.py:554-555` (`clean_user_dependencies`)
**Solution**:
- Rename directory to `.tmp_delete_[timestamp]` first
- Then delete the renamed directory
- If deletion fails, rename back to original
- Add rollback capability

### 3.2 Trigger Reinstall After Version Cleanup
**Issue**: Dependencies removed but not reinstalled after version change
**Location**: `installer.py:374-391` (`_check_and_cleanup_orphaned_deps`)
**Solution**:
- After removing old versions, set flag to trigger reinstall
- Call `ensure_dependencies()` with reinstall flag
- Ensure new versions are downloaded immediately
- Update marker file with new versions

## Phase 4: Debugging and Monitoring (Low Priority)
**Timeline: Week 3**
**Goal: Improve troubleshooting and monitoring capabilities**

### 4.1 Add Debug Logging Capability
**Issue**: Silent exceptions make debugging difficult
**Location**: Multiple locations with `except: pass`
**Solution**:
- Add environment variable `H2K_DEBUG` to enable debug output
- Log exceptions to stderr when debug mode enabled
- Add timestamp and context to debug messages
- Keep silent behavior by default for production

### 4.2 Improve Error Messages
**Issue**: Generic error messages don't help users
**Location**: Throughout installer.py
**Solution**:
- Add specific error messages for common failures
- Include suggested fixes in error messages
- Differentiate between recoverable and fatal errors
- Add progress indicators for long operations

## Implementation Order

### Week 1 - Critical Path
1. **Day 1-2**: Fix orphan detection (1.1)
   - Most critical issue affecting uninstall cleanup
   - Test with both regular and editable installs

2. **Day 3-4**: Fix Windows installation (1.2)
   - Affects all Windows users
   - Test on Windows 10/11

3. **Day 5**: Fix marker file consistency (1.3)
   - Quick fix but important for tracking

### Week 2 - Structure and Paths
1. **Day 1-2**: Fix nested directory handling (2.1)
   - Test with actual HPXML downloads

2. **Day 3**: Normalize paths (2.2)
   - Test on Windows, Linux, macOS if possible

3. **Day 4**: Add recursion protection (2.3)
   - Add unit tests for edge cases

4. **Day 5**: Testing and integration

### Week 3 - Reliability and Debugging
1. **Day 1-2**: Atomic operations (3.1)
   - Test failure scenarios

2. **Day 3**: Auto-reinstall (3.2)
   - Test version upgrade scenarios

3. **Day 4-5**: Debug logging and error messages (4.1, 4.2)
   - Document debug environment variables

## Testing Requirements

### Unit Tests
- Test orphan detection with various installation types
- Test path handling on different platforms
- Test atomic cleanup with simulated failures
- Test version comparison logic

### Integration Tests
- Full install/uninstall cycle on Windows
- Full install/uninstall cycle on Linux
- Editable install cleanup
- Version upgrade scenarios
- Corrupted installation recovery

### Manual Testing Checklist
- [ ] Regular pip install → uninstall → cleanup
- [ ] Editable install → uninstall → cleanup
- [ ] Windows .exe extraction
- [ ] Linux tarball extraction
- [ ] Version upgrade triggers reinstall
- [ ] Cleanup with no write permissions
- [ ] Cleanup with partial installation
- [ ] Multiple Python versions

## Success Criteria

1. **Orphan Detection**: Works for all installation types (regular, editable, user, system)
2. **Windows Support**: Fully automatic installation without manual steps
3. **Atomic Operations**: No partial states that break future operations
4. **Version Management**: Automatic upgrade when versions change
5. **Debugging**: Clear error messages and optional debug output
6. **Cross-Platform**: Works identically on Windows, Linux, macOS

## Risk Mitigation

### Backward Compatibility
- Maintain compatibility with existing installations
- Don't break existing marker files
- Support migration from old structure

### Rollback Plan
- Keep backup of original installer.py
- Version control all changes
- Test in isolated environment first
- Gradual rollout with beta testing

### Known Limitations
- Windows may still require admin rights for some operations
- Network issues during download can't be fully mitigated
- Some antivirus software may flag downloads

## Documentation Updates

After implementation, update:
1. README.md - Installation troubleshooting section
2. CLAUDE.md - Document new environment variables
3. Inline code comments for complex logic
4. Error messages with helpful context

## Future Enhancements (Not in Current Scope)

- Progress bars for downloads
- Parallel download of dependencies
- Checksum verification of downloads
- Local cache of dependencies
- GUI installer for Windows
- Homebrew formula for macOS
- Debian/RPM packages for Linux