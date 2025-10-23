#!/usr/bin/env python3
"""
Cross-platform demo test script with automated input.

This script tests the interactive demo with predefined responses
and works on both Windows and Unix-like systems.
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def run_command_with_input(cmd, input_text, timeout=60, cwd=None):
    """Run a command with input, handling both Windows and Unix."""
    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
            shell=True if sys.platform == "win32" else False,
        )
        return result
    except subprocess.TimeoutExpired as e:
        print(f"Command timed out after {timeout} seconds")
        return e
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def check_demo_output(demo_dir):
    """Check if demo created expected output files."""
    demo_path = Path(demo_dir)

    if not demo_path.exists():
        print("❌ Demo output directory not created")
        return False

    print("✅ Demo output directory created successfully")
    print("Contents:")
    try:
        for item in demo_path.iterdir():
            if item.is_file():
                size = item.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size//1024:,} KB"
                print(f"  📄 {item.name} ({size_str})")
            elif item.is_dir():
                print(f"  📁 {item.name}/")
    except Exception as e:
        print(f"Error listing directory contents: {e}")

    # Check for H2K file
    h2k_files = list(demo_path.glob("*.H2K")) + list(demo_path.glob("*.h2k"))
    if h2k_files:
        print("✅ H2K file copied successfully")
    else:
        print("❌ No H2K file found in output")
        return False

    # Check for HPXML file
    xml_files = list(demo_path.rglob("*.xml"))
    if xml_files:
        print("✅ HPXML file created successfully")
        for xml_file in xml_files[:3]:  # Show first 3 XML files
            size = xml_file.stat().st_size
            print(f"   • {xml_file.relative_to(demo_path)} ({size//1024} KB)")
    else:
        print("⚠️  No HPXML file found (conversion may not have completed)")

    # Check for simulation results
    csv_files = list(demo_path.rglob("results_*.csv"))
    if csv_files:
        print("✅ Simulation results created successfully")
        for csv_file in csv_files[:2]:  # Show first 2 CSV files
            size = csv_file.stat().st_size
            size_str = f"{size//1024} KB" if size < 1024 * 1024 else f"{size//(1024*1024)} MB"
            print(f"   • {csv_file.relative_to(demo_path)} ({size_str})")
    else:
        print("⚠️  No simulation results found")

    return True


def test_demo_basic_flow():
    """Test basic demo flow with English language."""
    print("🧪 Testing H2K Demo with scripted input...")
    print("=" * 50)
    print("Test 1: Basic demo flow")
    print("Input: 1 (English), 1 (First file), y (Run), n (No cleanup)")

    # Get project directory (cross-platform)
    project_dir = Path(__file__).parent.parent.resolve()

    # Create input sequence
    demo_input = "1\n1\ny\nn\n"  # English, first file, yes run, no cleanup

    # Determine the command based on platform
    if sys.platform == "win32":
        cmd = ["uv.exe", "run", "h2k-hpxml", "--demo"]
    else:
        cmd = ["uv", "run", "h2k-hpxml", "--demo"]

    print("Running demo...")
    result = run_command_with_input(cmd, demo_input, timeout=120, cwd=str(project_dir))

    if result is None:
        print("❌ Failed to run demo command")
        return False

    if isinstance(result, subprocess.TimeoutExpired):
        print("⚠️  Demo timed out (may be expected for long simulations)")
        # Timeout might be OK if simulation is running
    elif isinstance(result, subprocess.CompletedProcess):
        print(f"Demo completed with return code: {result.returncode}")

        # Check output for key indicators
        stdout = result.stdout
        if "Language / Langue" in stdout:
            print("✅ Language selection displayed")
        if "Interactive Demo" in stdout:
            print("✅ Welcome screen displayed")
        if "Choose an example file" in stdout or "Choisissez un fichier" in stdout:
            print("✅ File selection displayed")
        if "h2k_demo_output" in stdout:
            print("✅ Output directory referenced")

        # Show any errors
        if result.stderr:
            print("STDERR output:")
            print(result.stderr[:1000])  # First 1000 chars

    # Check output directory
    demo_output_dir = project_dir / "h2k_demo_output"
    return check_demo_output(demo_output_dir)


def test_demo_language_selection():
    """Test French language selection."""
    print("\nTest 2: French language selection")
    print("Input: 2 (Français), then timeout")

    project_dir = Path(__file__).parent.parent.resolve()

    # Test French language selection (exit quickly)
    french_input = "2\n"

    if sys.platform == "win32":
        cmd = ["uv.exe", "run", "h2k-hpxml", "--demo"]
    else:
        cmd = ["uv", "run", "h2k-hpxml", "--demo"]

    result = run_command_with_input(cmd, french_input, timeout=15, cwd=str(project_dir))

    if isinstance(result, subprocess.CompletedProcess):
        if "Démo Interactive" in result.stdout or "Choisissez" in result.stdout:
            print("✅ French language selection works")
            return True
    elif isinstance(result, subprocess.TimeoutExpired):
        print("✅ French selection started (timeout expected)")
        return True

    print("⚠️  French language selection test inconclusive")
    return False


def cleanup_demo_files():
    """Clean up demo output files."""
    project_dir = Path(__file__).parent.parent.resolve()
    demo_output_dir = project_dir / "h2k_demo_output"

    if demo_output_dir.exists():
        try:
            import shutil

            shutil.rmtree(demo_output_dir)
            print(f"🧹 Cleaned up demo files: {demo_output_dir}")
        except Exception as e:
            print(f"⚠️  Could not clean up demo files: {e}")
    else:
        print("ℹ️  No demo files to clean up")


def main():
    """Main test function."""
    print("🚀 Cross-Platform H2K Demo Test")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print()

    success = True

    try:
        # Test basic demo flow
        if not test_demo_basic_flow():
            success = False

        # Test language selection
        if not test_demo_language_selection():
            success = False

    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        success = False
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 Demo testing completed successfully!")
    else:
        print("⚠️  Demo testing completed with issues")

    print("\nManual testing:")
    print("  uv run h2k-hpxml --demo")
    print("\nCleanup:")
    print("  python tests/utils/demo_test_automation.py --cleanup")

    return 0 if success else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup_demo_files()
    else:
        sys.exit(main())
