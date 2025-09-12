#!/usr/bin/env python3
"""
Windows-specific test for H2K-HPXML installation and functionality.

This script tests Windows-specific paths, commands, and functionality.
"""

import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path


def is_windows():
    """Check if running on Windows."""
    return platform.system() == "Windows"


def test_windows_paths():
    """Test Windows path handling."""
    print("\n1. Testing Windows Path Handling")
    print("=" * 40)
    
    if not is_windows():
        print("⚠️  Not running on Windows - skipping Windows path tests")
        return True
    
    try:
        # Test Windows-specific path patterns
        from h2k_hpxml.examples import get_examples_directory, get_wizard_house
        from h2k_hpxml.config.manager import ConfigManager
        
        # Test example paths
        examples_dir = get_examples_directory()
        print(f"✅ Examples directory: {examples_dir}")
        
        wizard_house = get_wizard_house()
        print(f"✅ WizardHouse path: {wizard_house}")
        
        # Test config paths
        config = ConfigManager()
        print(f"✅ OpenStudio path: {config.openstudio_binary}")
        print(f"✅ EnergyPlus path: {config.energyplus_binary}")
        
        # Test that paths work with Windows path separators
        if wizard_house:
            # Convert to Windows path format and verify it still works
            windows_path = str(wizard_house).replace('/', '\\')
            if Path(windows_path).exists():
                print(f"✅ Windows path format works: {windows_path}")
            else:
                print(f"⚠️  Windows path format issue: {windows_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Windows path test failed: {e}")
        return False


def test_windows_commands():
    """Test Windows command execution."""
    print("\n2. Testing Windows Commands")
    print("=" * 40)
    
    if not is_windows():
        print("⚠️  Not running on Windows - skipping Windows command tests")
        return True
    
    try:
        # Test basic Python command
        result = subprocess.run(["python", "--version"], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ Python command works: {result.stdout.strip()}")
        else:
            # Try py launcher (Windows-specific)
            result = subprocess.run(["py", "--version"], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"✅ Python (py launcher) works: {result.stdout.strip()}")
            else:
                print("❌ Python command failed")
                return False
        
        # Test uv if available
        result = subprocess.run(["uv", "--version"], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ uv command works: {result.stdout.strip()}")
        else:
            print("⚠️  uv not available (can be installed)")
        
        return True
        
    except Exception as e:
        print(f"❌ Windows command test failed: {e}")
        return False


def test_windows_dependencies():
    """Test Windows dependency installation."""
    print("\n3. Testing Windows Dependencies")
    print("=" * 40)
    
    if not is_windows():
        print("⚠️  Not running on Windows - skipping Windows dependency tests")
        return True
    
    try:
        # Test dependency manager
        from h2k_hpxml.utils.dependencies import DependencyManager
        
        dep_manager = DependencyManager(interactive=False, skip_deps=False, auto_install=False)
        
        # Check Windows-specific paths
        print(f"✅ Windows detected: {dep_manager.is_windows}")
        
        # Test default paths
        hpxml_path = dep_manager.default_hpxml_path()
        openstudio_path = dep_manager.default_openstudio_path()
        
        print(f"✅ Default HPXML path: {hpxml_path}")
        print(f"✅ Default OpenStudio path: {openstudio_path}")
        
        # Test Windows path patterns
        if dep_manager.is_windows:
            windows_paths = dep_manager._get_windows_paths()
            print(f"✅ Windows OpenStudio search paths: {len(windows_paths)} locations")
            for path in windows_paths[:3]:  # Show first 3
                print(f"   • {path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Windows dependency test failed: {e}")
        return False


def test_windows_file_operations():
    """Test Windows file operations."""
    print("\n4. Testing Windows File Operations")
    print("=" * 40)
    
    try:
        # Test temp directory operations
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            print(f"✅ Temp directory created: {temp_path}")
            
            # Test file creation with Windows-safe names
            test_file = temp_path / "test_file.xml"
            test_file.write_text("<?xml version='1.0'?><test/>")
            
            if test_file.exists():
                print(f"✅ File creation works: {test_file}")
            else:
                print("❌ File creation failed")
                return False
            
            # Test reading file back
            content = test_file.read_text()
            if "test" in content:
                print("✅ File reading works")
            else:
                print("❌ File reading failed")
                return False
        
        print("✅ Temp directory cleanup successful")
        return True
        
    except Exception as e:
        print(f"❌ Windows file operations test failed: {e}")
        return False


def main():
    """Run Windows-specific tests."""
    print("H2K-HPXML Windows Compatibility Test")
    print("=" * 50)
    
    if not is_windows():
        print("⚠️  Not running on Windows")
        print("This test is designed for Windows systems but will run basic cross-platform tests")
    else:
        print("✅ Running on Windows")
        print(f"   OS: {platform.platform()}")
        print(f"   Python: {sys.version}")
    
    # Run tests
    tests = [
        ("Windows Paths", test_windows_paths),
        ("Windows Commands", test_windows_commands),
        ("Windows Dependencies", test_windows_dependencies),
        ("Windows File Operations", test_windows_file_operations),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("WINDOWS TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25s} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print(f"\n🎉 All Windows tests passed!")
        return True
    else:
        print(f"\n❌ {total - passed} Windows test(s) failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)