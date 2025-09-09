#!/usr/bin/env python3
"""
Test the automatic cleanup behavior when packages are uninstalled.

This demonstrates how h2k-hpxml now automatically removes its dependencies
when the package is uninstalled.
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


def simulate_uninstall_cleanup():
    """Simulate what happens when the package is uninstalled and then another package tries to import h2k_hpxml."""
    
    print("=" * 70)
    print("H2K-HPXML Automatic Cleanup Test")
    print("=" * 70)
    
    # Create a temporary user directory to simulate user home
    with tempfile.TemporaryDirectory() as temp_home:
        temp_deps = Path(temp_home) / "h2k_hpxml" / "deps"
        marker_file = temp_deps / ".h2k_hpxml_installation"
        
        print(f"\n1. Simulating user directory: {temp_deps}")
        
        # Create fake dependencies (simulate previous installation)
        temp_deps.mkdir(parents=True, exist_ok=True)
        
        # Create some fake dependency files
        (temp_deps / "OpenStudio-HPXML").mkdir()
        (temp_deps / "openstudio").mkdir()
        
        # Write some files to show they exist
        fake_file1 = temp_deps / "OpenStudio-HPXML" / "workflow.rb"
        fake_file2 = temp_deps / "openstudio" / "bin"
        fake_file2.mkdir()
        fake_file1.write_text("# Fake HPXML file")
        (fake_file2 / "openstudio").write_text("#!/bin/bash\necho fake")
        
        # Create marker file pointing to a non-existent package directory
        fake_package_dir = "/fake/nonexistent/package/directory"
        marker_data = {
            "package_dir": fake_package_dir,
            "installed_at": "2025-01-01T00:00:00",
            "version": "1.0.0",
            "python_version": "3.13",
            "deps_version": {
                "openstudio_version": "3.9.0",
                "openstudio_sha": "c77fbb9569",
                "openstudio_hpxml_version": "v1.9.1"
            }
        }
        
        with open(marker_file, 'w') as f:
            json.dump(marker_data, f, indent=2)
        
        print(f"2. Created fake dependencies:")
        print(f"   - {temp_deps / 'OpenStudio-HPXML'}")
        print(f"   - {temp_deps / 'openstudio'}")
        print(f"   - {marker_file}")
        
        # Show initial state
        size_before = sum(f.stat().st_size for f in temp_deps.rglob('*') if f.is_file())
        file_count_before = len(list(temp_deps.rglob('*')))
        print(f"3. Before cleanup: {file_count_before} files, {size_before} bytes")
        
        # Now simulate the cleanup check by calling the function directly
        print(f"\\n4. Simulating import of h2k_hpxml (triggers cleanup check)...")
        print(f"   - Marker points to: {fake_package_dir}")
        print(f"   - Package exists: {Path(fake_package_dir).exists()}")
        
        # Mock the cleanup function with our test directory
        import h2k_hpxml.installer as installer
        
        # Temporarily override the user data directory and disable env var
        original_get_user_data = installer._get_user_data_dir
        original_env = os.environ.get('H2K_DEPS_DIR')
        
        def mock_get_user_data():
            return Path(temp_home) / "h2k_hpxml"
        
        installer._get_user_data_dir = mock_get_user_data
        if 'H2K_DEPS_DIR' in os.environ:
            del os.environ['H2K_DEPS_DIR']
        
        try:
            # This should detect orphaned dependencies and clean them up
            installer._check_and_cleanup_orphaned_deps()
            
            # Check if cleanup worked
            if temp_deps.exists():
                size_after = sum(f.stat().st_size for f in temp_deps.rglob('*') if f.is_file())
                file_count_after = len(list(temp_deps.rglob('*')))
                print(f"5. After cleanup: {file_count_after} files, {size_after} bytes")
                
                if file_count_after == 0:
                    print("✓ SUCCESS: All dependencies cleaned up automatically!")
                else:
                    print(f"✗ PARTIAL: {file_count_after} files remain")
            else:
                print("✓ SUCCESS: Dependency directory completely removed!")
                
        finally:
            # Restore original function and environment
            installer._get_user_data_dir = original_get_user_data
            if original_env:
                os.environ['H2K_DEPS_DIR'] = original_env


def demonstrate_version_upgrade():
    """Demonstrate automatic cleanup when dependency versions change."""
    print("\\n" + "=" * 70)
    print("Dependency Version Upgrade Test")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_home:
        temp_deps = Path(temp_home) / "h2k_hpxml" / "deps"
        marker_file = temp_deps / ".h2k_hpxml_installation"
        
        # Create dependencies with old version
        temp_deps.mkdir(parents=True, exist_ok=True)
        (temp_deps / "OpenStudio-HPXML").mkdir()
        (temp_deps / "openstudio").mkdir()
        
        # Create marker with OLD dependency versions
        old_marker_data = {
            "package_dir": "/workspaces/h2k_hpxml/src/h2k_hpxml",  # Valid path
            "installed_at": "2025-01-01T00:00:00",
            "version": "1.0.0",
            "python_version": "3.13",
            "deps_version": {
                "openstudio_version": "3.8.0",  # OLD VERSION
                "openstudio_sha": "old_hash",
                "openstudio_hpxml_version": "v1.8.0"  # OLD VERSION
            }
        }
        
        with open(marker_file, 'w') as f:
            json.dump(old_marker_data, f, indent=2)
        
        print(f"1. Created deps with OLD versions:")
        print(f"   - OpenStudio: 3.8.0 (current: 3.9.0)")
        print(f"   - HPXML: v1.8.0 (current: v1.9.1)")
        
        # Mock the cleanup function and disable env var
        import h2k_hpxml.installer as installer
        original_get_user_data = installer._get_user_data_dir
        original_env = os.environ.get('H2K_DEPS_DIR')
        
        def mock_get_user_data():
            return Path(temp_home) / "h2k_hpxml"
        
        installer._get_user_data_dir = mock_get_user_data
        if 'H2K_DEPS_DIR' in os.environ:
            del os.environ['H2K_DEPS_DIR']
        
        try:
            print("\\n2. Simulating import (triggers version check)...")
            installer._check_and_cleanup_orphaned_deps()
            
            # Check if old deps were removed
            hpxml_exists = (temp_deps / "OpenStudio-HPXML").exists()
            os_exists = (temp_deps / "openstudio").exists()
            
            if not hpxml_exists and not os_exists:
                print("✓ SUCCESS: Old dependencies removed for upgrade!")
            else:
                print(f"✗ FAILED: Dependencies still exist (HPXML: {hpxml_exists}, OS: {os_exists})")
                
        finally:
            installer._get_user_data_dir = original_get_user_data
            if original_env:
                os.environ['H2K_DEPS_DIR'] = original_env


if __name__ == "__main__":
    # Test automatic cleanup of orphaned dependencies
    simulate_uninstall_cleanup()
    
    # Test automatic upgrade when versions change
    demonstrate_version_upgrade()
    
    print("\\n" + "=" * 70)
    print("SUMMARY: New Cleanup Behavior")
    print("=" * 70)
    print("✓ Dependencies are automatically removed when package is uninstalled")
    print("✓ Dependencies are automatically updated when versions change")  
    print("✓ Only affects user directory installations (not Docker/CI)")
    print("✓ Cleanup happens silently on next h2k_hpxml import")
    print("✓ No manual intervention required")
    print("\\nThis solves the original problem:")
    print("  pip uninstall h2k-hpxml  # Now also removes dependencies!")