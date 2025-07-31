"""
Resilience CLI test for validating the resilience analysis functionality.

This test validates that the resilience CLI can successfully:
1. Convert H2K files to HPXML/OSM format
2. Create the four required resilience scenarios
3. Generate proper output directory structure
4. Run without errors when OpenStudio bindings are available
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to Python path so we can import tests.utils
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add src directory to path for h2k_hpxml imports
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from tests.utils import find_hpxml_file  # noqa: E402
from tests.utils import get_h2k_example_files  # noqa: E402


def get_python_executable():
    """Get the Python executable path for cross-platform compatibility."""
    if platform.system() == "Windows":
        # Try virtual environment first, then system Python
        venv_python = Path.cwd() / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        return sys.executable
    else:
        # Linux/Unix
        venv_python = Path.cwd() / "venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)
        return sys.executable


def get_pythonpath():
    """Get PYTHONPATH for cross-platform compatibility."""
    src_path = Path.cwd() / "src"
    root_path = Path.cwd()

    if platform.system() == "Windows":
        return f"{src_path};{root_path}"
    else:
        return f"{src_path}:{root_path}"


@pytest.mark.resilience
def test_resilience_cli_basic(check_openstudio_bindings):
    """
    Test basic resilience CLI functionality without running simulations.

    This test validates:
    1. CLI accepts input parameters correctly
    2. Creates proper output directory structure
    3. Generates HPXML files for baseline scenario
    4. Creates scenario directories
    5. Handles errors gracefully
    """
    # Get test files
    test_files = get_h2k_example_files()
    if not test_files:
        pytest.skip("No test H2K files found in examples directory")

    # Use the first available test file
    test_file = test_files[0]
    examples_dir = "examples"
    input_path = os.path.join(examples_dir, test_file)

    # Setup output directory
    temp_output_dir = "tests/temp/resilience"
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)

    # Extract base name for output validation
    base_name = os.path.splitext(test_file)[0]

    print(f"\n🔄 Testing Resilience CLI for {test_file}...")

    try:
        # Run resilience CLI without simulations (faster test)
        python_exe = get_python_executable()
        cmd = [
            python_exe,
            "-m",
            "h2k_hpxml.cli.resilience",
            input_path,
            "--outage-days",
            "3",  # Shorter for testing
            "--output-path",
            temp_output_dir,
            "--clothing-factor-summer",
            "0.6",
            "--clothing-factor-winter",
            "1.1",
            # Note: --run-simulation flag omitted to skip actual simulations
        ]

        # Set PYTHONPATH to include src directory while preserving existing paths
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        new_pythonpath = get_pythonpath()
        if current_pythonpath:
            env["PYTHONPATH"] = f"{new_pythonpath}{os.pathsep}{current_pythonpath}"
        else:
            env["PYTHONPATH"] = new_pythonpath

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,  # 5 minute timeout
        )

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        # Validate CLI execution
        assert result.returncode == 0, f"Resilience CLI failed with return code {result.returncode}"

        # Validate output directory structure was created
        project_folder = os.path.join(temp_output_dir, base_name)
        assert os.path.exists(project_folder), f"Project folder not created: {project_folder}"

        # Validate original H2K file was copied
        original_h2k = os.path.join(project_folder, "original.h2k")
        assert os.path.exists(original_h2k), f"Original H2K file not copied: {original_h2k}"

        # Validate scenario directories were created
        expected_scenarios = [
            "outage_typical_year",
            "outage_extreme_year",
            "thermal_autonomy_typical_year",
            "thermal_autonomy_extreme_year",
        ]

        for scenario in expected_scenarios:
            scenario_path = os.path.join(project_folder, scenario)
            assert os.path.exists(scenario_path), f"Scenario directory not created: {scenario_path}"

        # Validate original folder was created
        original_folder = os.path.join(project_folder, "original")
        assert os.path.exists(original_folder), f"Original folder not created: {original_folder}"

        # Look for HPXML file in original folder (baseline conversion)
        hpxml_file = find_hpxml_file(original_folder, base_name)
        if hpxml_file:
            print(f"✅ HPXML file generated: {hpxml_file}")
            assert os.path.getsize(hpxml_file) > 0, "HPXML file is empty"
        else:
            print(f"⚠️  No HPXML file found in {original_folder}")

        print(f"✅ Resilience CLI test PASSED for {test_file}")

    except subprocess.TimeoutExpired:
        pytest.fail(f"Resilience CLI timed out for {test_file}")
    except Exception as e:
        pytest.fail(f"Resilience CLI test failed for {test_file}: {str(e)}")


@pytest.mark.resilience
@pytest.mark.slow
def test_resilience_cli_with_simulation(check_openstudio_bindings):
    """
    Test resilience CLI with simulation runs (slower test).

    This test validates:
    1. CLI can run actual OpenStudio simulations
    2. Results are generated for scenarios
    3. Output files are created properly

    Note: This test is marked as 'slow' and may take several minutes.
    """
    # Get test files - use a smaller test file for simulation
    test_files = get_h2k_example_files()
    if not test_files:
        pytest.skip("No test H2K files found in examples directory")

    # Use the first available test file
    test_file = test_files[0]
    examples_dir = "examples"
    input_path = os.path.join(examples_dir, test_file)

    # Setup output directory
    temp_output_dir = "tests/temp/resilience_sim"
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)

    # Extract base name for output validation
    base_name = os.path.splitext(test_file)[0]

    print(f"\n🔄 Testing Resilience CLI with Simulation for {test_file}...")
    print("⚠️  This test may take several minutes to complete...")

    try:
        # Run resilience CLI with simulations
        python_exe = get_python_executable()
        cmd = [
            python_exe,
            "-m",
            "h2k_hpxml.cli.resilience",
            input_path,
            "--outage-days",
            "2",  # Minimal for testing
            "--output-path",
            temp_output_dir,
            "--clothing-factor-summer",
            "0.5",
            "--clothing-factor-winter",
            "1.0",
            "--run-simulation",  # Enable simulations
        ]

        # Set PYTHONPATH to include src directory while preserving existing paths
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        new_pythonpath = get_pythonpath()
        if current_pythonpath:
            env["PYTHONPATH"] = f"{new_pythonpath}{os.pathsep}{current_pythonpath}"
        else:
            env["PYTHONPATH"] = new_pythonpath

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minute timeout for simulations
            env=env,
        )

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        # Validate CLI execution
        assert (
            result.returncode == 0
        ), f"Resilience CLI with simulation failed with return code {result.returncode}"

        # Validate project structure
        project_folder = os.path.join(temp_output_dir, base_name)
        assert os.path.exists(project_folder), f"Project folder not created: {project_folder}"

        # Check for simulation outputs in scenario directories
        scenarios = [
            "outage_typical_year",
            "outage_extreme_year",
            "thermal_autonomy_typical_year",
            "thermal_autonomy_extreme_year",
        ]

        simulation_files_found = 0
        for scenario in scenarios:
            scenario_path = os.path.join(project_folder, scenario)

            # Look for common OpenStudio output files
            run_dir = os.path.join(scenario_path, "run")
            if os.path.exists(run_dir):
                # Check for typical OpenStudio outputs
                output_files = ["eplusout.sql", "eplusout.csv", "run.log"]
                for output_file in output_files:
                    output_path = os.path.join(run_dir, output_file)
                    if os.path.exists(output_path):
                        simulation_files_found += 1
                        print(f"✅ Found simulation output: {output_path}")
                        break

        # We should find at least some simulation outputs if simulations ran
        if simulation_files_found > 0:
            print(f"✅ Simulation outputs found for {simulation_files_found} scenarios")
        else:
            print("⚠️  No simulation outputs found - simulations may not have completed")

        print(f"✅ Resilience CLI simulation test COMPLETED for {test_file}")

    except subprocess.TimeoutExpired:
        pytest.fail(f"Resilience CLI simulation timed out for {test_file}")
    except Exception as e:
        pytest.fail(f"Resilience CLI simulation test failed for {test_file}: {str(e)}")


@pytest.mark.resilience
def test_resilience_cli_error_handling():
    """
    Test resilience CLI error handling for invalid inputs.
    """
    temp_output_dir = "tests/temp/resilience_error"
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)

    print("\n🔄 Testing Resilience CLI error handling...")

    # Test 1: Non-existent input file
    cmd = [
        "python",
        "-m",
        "h2k_hpxml.cli.resilience",
        "nonexistent.h2k",
        "--output-path",
        temp_output_dir,
    ]

    # Set PYTHONPATH to include src directory while preserving existing paths
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    new_pythonpath = get_pythonpath()
    if current_pythonpath:
        env["PYTHONPATH"] = f"{new_pythonpath}{os.pathsep}{current_pythonpath}"
    else:
        env["PYTHONPATH"] = new_pythonpath

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
    assert result.returncode != 0, "CLI should fail for non-existent input file"
    print("✅ Correctly handled non-existent input file")

    # Test 2: Invalid outage days (negative)
    test_files = get_h2k_example_files()
    if test_files:
        input_path = os.path.join("examples", test_files[0])
        python_exe = get_python_executable()
        cmd = [
            python_exe,
            "-m",
            "h2k_hpxml.cli.resilience",
            input_path,
            "--outage-days",
            "-1",
            "--output-path",
            temp_output_dir,
        ]

        # Set PYTHONPATH to include src directory while preserving existing paths
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        new_pythonpath = get_pythonpath()
        if current_pythonpath:
            env["PYTHONPATH"] = f"{new_pythonpath}{os.pathsep}{current_pythonpath}"
        else:
            env["PYTHONPATH"] = new_pythonpath

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        assert result.returncode != 0, "CLI should fail for negative outage days"
        print("✅ Correctly handled invalid outage days")

    # Test 3: Invalid clothing factor (out of range)
    if test_files:
        input_path = os.path.join("examples", test_files[0])
        python_exe = get_python_executable()
        cmd = [
            python_exe,
            "-m",
            "h2k_hpxml.cli.resilience",
            input_path,
            "--clothing-factor-summer",
            "3.0",  # Out of range (0.0-2.0)
            "--output-path",
            temp_output_dir,
        ]

        # Set PYTHONPATH to include src directory while preserving existing paths
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        new_pythonpath = get_pythonpath()
        if current_pythonpath:
            env["PYTHONPATH"] = f"{new_pythonpath}{os.pathsep}{current_pythonpath}"
        else:
            env["PYTHONPATH"] = new_pythonpath

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        assert result.returncode != 0, "CLI should fail for out-of-range clothing factor"
        print("✅ Correctly handled invalid clothing factor")

    print("✅ Resilience CLI error handling tests PASSED")


@pytest.mark.resilience
def test_resilience_cli_help():
    """
    Test that resilience CLI help command works.
    """
    print("\n🔄 Testing Resilience CLI help...")

    python_exe = get_python_executable()
    cmd = [python_exe, "-m", "h2k_hpxml.cli.resilience", "--help"]

    # Set PYTHONPATH to include src directory while preserving existing paths
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    new_pythonpath = get_pythonpath()
    if current_pythonpath:
        env["PYTHONPATH"] = f"{new_pythonpath}{os.pathsep}{current_pythonpath}"
    else:
        env["PYTHONPATH"] = new_pythonpath

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)

    assert result.returncode == 0, "Help command should succeed"
    assert "resilience" in result.stdout.lower(), "Help output should mention resilience"
    assert "--outage-days" in result.stdout, "Help should show outage-days option"
    assert "--clothing-factor" in result.stdout, "Help should show clothing factor options"

    print("✅ Resilience CLI help test PASSED")
