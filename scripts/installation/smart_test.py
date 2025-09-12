#!/usr/bin/env python3
"""
Smart H2K-HPXML Installation Test

Automatically detects whether to use uv or regular Python/pip commands.
Works with both installation methods: pip install h2k-hpxml OR uv add h2k-hpxml
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path


def detect_runner():
    """Detect whether to use uv run or direct python commands."""
    # Check if we're in a uv project (has pyproject.toml with uv config)
    if Path("pyproject.toml").exists():
        try:
            with open("pyproject.toml", "r") as f:
                content = f.read()
                if "uv" in content.lower():
                    return "uv"
        except:
            pass
    
    # Check if uv is available and h2k-hpxml is installed via uv
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            # Check if we can run h2k-hpxml with uv
            result = subprocess.run(["uv", "run", "python", "-c", "import h2k_hpxml"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return "uv"
    except FileNotFoundError:
        pass
    
    return "python"


def run_command(cmd_parts, runner="python", check=True):
    """Run a command with the appropriate runner (uv or python)."""
    if runner == "uv":
        if cmd_parts[0] in ["h2k2hpxml", "h2k-deps"]:
            # CLI commands: uv run h2k2hpxml
            cmd = ["uv", "run"] + cmd_parts
        elif cmd_parts[0] == "python":
            # Python commands: uv run python
            cmd = ["uv", "run"] + cmd_parts
        else:
            cmd = cmd_parts
    else:
        cmd = cmd_parts
    
    print(f"Running: {' '.join(cmd)}")
    try:
        # Windows compatibility: use shell=True for Windows
        import platform
        use_shell = platform.system() == "Windows"
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=check, 
                              timeout=60, shell=use_shell)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"


def test_installation(runner):
    """Test that the package is properly installed."""
    print("\n1. Testing Installation")
    print("=" * 40)
    
    # Test package import
    success, stdout, stderr = run_command(
        ["python", "-c", "import h2k_hpxml; print('✅ Package imported')"],
        runner, check=False
    )
    
    if success:
        print("✅ Package import successful")
        return True
    else:
        print("❌ Package import failed:")
        print(stderr)
        return False


def test_cli_tools(runner):
    """Test that CLI tools are working."""
    print("\n2. Testing CLI Tools")
    print("=" * 40)
    
    tools = ["h2k2hpxml", "h2k-deps"]
    results = []
    
    for tool in tools:
        success, stdout, stderr = run_command([tool, "--help"], runner, check=False)
        if success:
            print(f"✅ {tool} working")
            results.append(True)
        else:
            print(f"❌ {tool} failed:")
            print(stderr)
            results.append(False)
    
    return all(results)


def test_dependencies(runner):
    """Test that dependencies are available."""
    print("\n3. Testing Dependencies")
    print("=" * 40)
    
    success, stdout, stderr = run_command(["h2k-deps", "--check-only"], runner, check=False)
    
    if success and "All dependencies satisfied!" in stdout:
        print("✅ Dependencies check passed")
        return True
    else:
        print("❌ Dependencies check failed")
        if stdout:
            print("Output:", stdout)
        if stderr:
            print("Error:", stderr)
        print("\nTry running:")
        if runner == "uv":
            print("  uv run h2k-deps --setup")
            print("  uv run h2k-deps --auto-install")
        else:
            print("  h2k-deps --setup")
            print("  h2k-deps --auto-install")
        return False


def test_conversion(runner):
    """Test basic H2K to HPXML conversion."""
    print("\n4. Testing Basic Conversion")
    print("=" * 40)
    
    # Look for sample files
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
        print("⚠️  No sample H2K file found - skipping conversion test")
        return True  # Not a failure, just no test file
    
    print(f"Using sample file: {h2k_file}")
    
    # Test conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "test.xml")
        
        success, stdout, stderr = run_command([
            "h2k2hpxml", h2k_file, "--output", output_file, "--do-not-sim"
        ], runner, check=False)
        
        if success and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Conversion successful (output: {file_size} bytes)")
            return True
        else:
            print("❌ Conversion failed:")
            if stderr:
                print(stderr)
            return False


def main():
    """Run all tests with smart runner detection."""
    print("H2K-HPXML Smart Installation Test")
    print("=" * 40)
    
    # Detect the best runner
    runner = detect_runner()
    runner_name = "uv" if runner == "uv" else "pip/python"
    print(f"📦 Detected installation method: {runner_name}")
    
    if runner == "uv":
        print("   Using 'uv run' commands")
    else:
        print("   Using direct python/pip commands")
    
    # Run tests
    tests = [
        ("Installation", lambda: test_installation(runner)),
        ("CLI Tools", lambda: test_cli_tools(runner)),
        ("Dependencies", lambda: test_dependencies(runner)),
        ("Basic Conversion", lambda: test_conversion(runner)),
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
        print(f"\n🎉 All tests passed! H2K-HPXML is working correctly with {runner_name}.")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        print("\nNext steps:")
        if runner == "uv":
            print("- Run: uv run h2k-deps --setup")
            print("- Or try: uv add h2k-hpxml")
        else:
            print("- Run: h2k-deps --setup")
            print("- Or try: pip install --upgrade h2k-hpxml")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)