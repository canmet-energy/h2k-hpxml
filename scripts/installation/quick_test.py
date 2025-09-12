#!/usr/bin/env python3
"""
Quick H2K-HPXML Installation Test

One-liner test script to verify H2K-HPXML installation.
Run with: python quick_test.py
"""

def quick_test():
    """Quick installation test."""
    tests = []
    
    # Test 1: Package import
    try:
        import h2k_hpxml
        tests.append(("Package Import", True, "✅"))
    except ImportError as e:
        tests.append(("Package Import", False, f"❌ {e}"))
    
    # Test 2: CLI tools
    try:
        import subprocess
        result = subprocess.run(["h2k2hpxml", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            tests.append(("CLI Tools", True, "✅"))
        else:
            tests.append(("CLI Tools", False, f"❌ Exit code {result.returncode}"))
    except Exception as e:
        tests.append(("CLI Tools", False, f"❌ {e}"))
    
    # Test 3: Dependencies
    try:
        result = subprocess.run(["h2k-deps", "--check-only"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and "All dependencies satisfied!" in result.stdout:
            tests.append(("Dependencies", True, "✅"))
        else:
            tests.append(("Dependencies", False, "❌ Missing dependencies"))
    except Exception as e:
        tests.append(("Dependencies", False, f"❌ {e}"))
    
    # Test 4: Configuration
    try:
        from h2k_hpxml.config.manager import ConfigManager
        config = ConfigManager()
        if config.openstudio_binary and config.hpxml_os_path:
            tests.append(("Configuration", True, "✅"))
        else:
            tests.append(("Configuration", False, "❌ Missing paths"))
    except Exception as e:
        tests.append(("Configuration", False, f"❌ {e}"))
    
    # Print results
    print("H2K-HPXML Quick Test")
    print("=" * 30)
    
    passed = 0
    for test_name, success, message in tests:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:15s} {status:4s} {message}")
        if success:
            passed += 1
    
    print("-" * 30)
    print(f"Result: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 Installation looks good!")
        return True
    else:
        print(f"\n❌ {len(tests) - passed} issue(s) found.")
        print("\nTroubleshooting:")
        print("- Run: h2k-deps --setup")
        print("- Check: INSTALLATION_TEST.md")
        return False

if __name__ == "__main__":
    import sys
    success = quick_test()
    sys.exit(0 if success else 1)