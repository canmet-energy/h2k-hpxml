#!/usr/bin/env python3
"""
Installation Test Script for H2K-HPXML

This script tests that h2k-hpxml is properly installed and working.
Run this after installing the package with pip.
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def test_dependencies():
    """Test that dependencies are available."""
    print("\n1. Testing Dependencies")
    print("=" * 40)
    
    # Test h2k-deps command
    success, stdout, stderr = run_command(["h2k-deps", "--check-only"], check=False)
    if success:
        print("✅ Dependencies check passed")
        return True
    else:
        print("❌ Dependencies check failed:")
        print(stdout)
        print(stderr)
        print("\nTry running: h2k-deps --setup")
        print("Or: h2k-deps --auto-install")
        return False


def test_basic_conversion():
    """Test basic H2K to HPXML conversion."""
    print("\n2. Testing Basic Conversion")
    print("=" * 40)
    
    # Find a sample H2K file
    h2k_file = None
    
    # Try to use packaged examples first
    try:
        from h2k_hpxml.examples import get_wizard_house
        example_path = get_wizard_house()
        if example_path and example_path.exists():
            h2k_file = str(example_path)
    except ImportError:
        pass
    
    # Fallback to local examples if package examples not available
    if not h2k_file:
        sample_files = [
            "examples/WizardHouse.h2k",
            "tests/h2k_files/WizardHouse.h2k",
            Path(__file__).parent / "examples" / "WizardHouse.h2k"
        ]
        
        for sample in sample_files:
            if Path(sample).exists():
                h2k_file = str(sample)
                break
    
    if not h2k_file:
        print("❌ No sample H2K file found")
        print("Expected locations:")
        for sample in sample_files:
            print(f"  - {sample}")
        return False
    
    print(f"Using sample file: {h2k_file}")
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "test_output.xml")
        
        # Test conversion without simulation
        cmd = ["h2k2hpxml", h2k_file, "--output", output_file, "--do-not-sim"]
        success, stdout, stderr = run_command(cmd, check=False)
        
        if success and os.path.exists(output_file):
            print("✅ Basic conversion successful")
            print(f"   Output file created: {output_file}")
            
            # Check file size (should be reasonable for HPXML)
            file_size = os.path.getsize(output_file)
            if file_size > 1000:  # At least 1KB
                print(f"   Output file size: {file_size} bytes ✅")
                return True
            else:
                print(f"   Output file too small: {file_size} bytes ❌")
                return False
        else:
            print("❌ Conversion failed:")
            print(stdout)
            print(stderr)
            return False


def test_api():
    """Test the Python API."""
    print("\n3. Testing Python API")
    print("=" * 40)
    
    try:
        # Test imports
        from h2k_hpxml.api import convert_h2k_string, validate_dependencies
        from h2k_hpxml.config.manager import ConfigManager
        print("✅ Package imports successful")
        
        # Test configuration
        config = ConfigManager()
        print("✅ Configuration manager works")
        print(f"   OpenStudio path: {config.openstudio_binary}")
        print(f"   OpenStudio-HPXML path: {config.hpxml_os_path}")
        print(f"   EnergyPlus path: {config.energyplus_binary}")
        
        # Test dependency validation
        deps = validate_dependencies()
        if deps['valid']:
            print("✅ API dependency validation passed")
        else:
            print("❌ API dependency validation failed:")
            print(f"   Missing: {deps['missing']}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def test_with_simulation():
    """Test full conversion with simulation (optional)."""
    print("\n4. Testing Full Simulation (Optional)")
    print("=" * 40)
    
    # Find a sample H2K file
    h2k_file = None
    
    # Try to use packaged examples first
    try:
        from h2k_hpxml.examples import get_wizard_house
        example_path = get_wizard_house()
        if example_path and example_path.exists():
            h2k_file = str(example_path)
    except ImportError:
        pass
    
    # Fallback to local examples if package examples not available
    if not h2k_file:
        sample_files = [
            "examples/WizardHouse.h2k",
            "tests/h2k_files/WizardHouse.h2k",
            Path(__file__).parent / "examples" / "WizardHouse.h2k"
        ]
        
        for sample in sample_files:
            if Path(sample).exists():
                h2k_file = str(sample)
                break
    
    if not h2k_file:
        print("❌ No sample H2K file found for simulation test")
        return False
    
    print(f"Using sample file: {h2k_file}")
    print("⚠️  This may take several minutes...")
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test full conversion with simulation
        cmd = ["h2k2hpxml", h2k_file, "--output", temp_dir]
        success, stdout, stderr = run_command(cmd, check=False)
        
        if success:
            # Check for simulation outputs
            output_files = list(Path(temp_dir).rglob("*.csv"))
            if output_files:
                print("✅ Full simulation successful")
                print(f"   Found {len(output_files)} output files")
                return True
            else:
                print("⚠️  Conversion succeeded but no CSV outputs found")
                return False
        else:
            print("❌ Full simulation failed:")
            print(stdout)
            print(stderr)
            return False


def main():
    """Run all tests."""
    print("H2K-HPXML Installation Test")
    print("=" * 40)
    
    # Check if we're in the right environment
    try:
        import h2k_hpxml
        print(f"✅ h2k-hpxml package found (version: {getattr(h2k_hpxml, '__version__', 'unknown')})")
    except ImportError:
        print("❌ h2k-hpxml package not found")
        print("Install with: pip install h2k-hpxml")
        sys.exit(1)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Basic Conversion", test_basic_conversion),
        ("Python API", test_api),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Optional simulation test
    print("\n" + "=" * 50)
    try:
        run_sim = input("Run full simulation test? (slow, y/N): ").lower().strip()
    except (EOFError, KeyboardInterrupt):
        run_sim = 'n'  # Default to no in non-interactive environments
        print("Run full simulation test? (slow, y/N): n")
    
    if run_sim in ['y', 'yes']:
        try:
            results["Full Simulation"] = test_with_simulation()
        except Exception as e:
            print(f"❌ Full simulation test crashed: {e}")
            results["Full Simulation"] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! H2K-HPXML is working correctly.")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed. Check the output above.")
        print("\nTroubleshooting:")
        print("- Ensure dependencies are installed: h2k-deps --setup")
        print("- Check configuration: h2k-deps --check-only")
        print("- Verify sample files are available")
        sys.exit(1)


if __name__ == "__main__":
    main()