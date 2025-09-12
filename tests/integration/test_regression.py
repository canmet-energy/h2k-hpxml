"""
Regression test for energy data and HPXML structure validation.

This test runs the H2K workflow once per file and validates both energy data
and HPXML structure in a single pass, making it more efficient than running
separate tests.
"""

import os
import shutil
import sys
from datetime import datetime

import pytest

# Add project root to Python path so we can import tests.utils
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add src directory to path for h2k_hpxml imports
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from tests.utils import compare_energy_values  # noqa: E402
from tests.utils import compare_hpxml_files  # noqa: E402
from tests.utils import extract_annual_energy_data  # noqa: E402
from tests.utils import find_hpxml_file  # noqa: E402
from tests.utils import find_sql_file  # noqa: E402
from tests.utils import get_baseline_hpxml_summary_path  # noqa: E402
from tests.utils import get_baseline_summary_path  # noqa: E402
from tests.utils import get_comparison_hpxml_summary_path  # noqa: E402
from tests.utils import get_comparison_summary_path  # noqa: E402
from tests.utils import load_baseline_file  # noqa: E402
from tests.utils import load_baseline_summary  # noqa: E402
from tests.utils import run_h2k_workflow  # noqa: E402
from tests.utils import save_comparison_file  # noqa: E402
from tests.utils import save_comparison_summary  # noqa: E402


def get_h2k_test_files():
    """Get list of H2K files that have baseline data for testing."""
    # Use packaged examples from the h2k_hpxml.examples module
    try:
        from h2k_hpxml.examples import get_examples_directory, list_example_files
        examples_dir = get_examples_directory()
    except ImportError:
        # Fallback to hardcoded path if package not available
        examples_dir = "examples"
    
    baseline_summary = load_baseline_summary()

    if not baseline_summary or "results" not in baseline_summary:
        return []

    test_files = []
    for source_file, baseline_info in baseline_summary["results"].items():
        if isinstance(examples_dir, os.PathLike):
            input_path = examples_dir / source_file
        else:
            input_path = os.path.join(examples_dir, source_file)
        
        if os.path.exists(input_path):
            test_files.append((source_file, baseline_info))

    return test_files


@pytest.mark.regression
@pytest.mark.parametrize("test_file_info", get_h2k_test_files(), ids=lambda x: x[0])
def test_regression_parallel(test_file_info, check_openstudio_bindings):
    """
    Parallel regression test for individual H2K files.

    Tests energy data and HPXML structure validation for a single H2K file.
    This allows pytest-xdist to run tests in parallel across multiple workers.
    """
    source_file, baseline_info = test_file_info
    
    # Use packaged examples from the h2k_hpxml.examples module
    try:
        from h2k_hpxml.examples import get_examples_directory
        examples_dir = get_examples_directory()
    except ImportError:
        # Fallback to hardcoded path if package not available
        examples_dir = "examples"
        
    energy_tolerance_percent = 5.0  # 5% tolerance for energy data

    # Create unique temp directory for this test to avoid conflicts
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    temp_output_dir = f"tests/temp/regression_{unique_id}"

    # Setup output directory
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)

    try:
        if isinstance(examples_dir, os.PathLike):
            input_path = examples_dir / source_file
        else:
            input_path = os.path.join(examples_dir, source_file)
        print(f"\\n🔄 Testing Regression for {source_file}...")

        # Extract base name for file utilities
        base_name = os.path.splitext(source_file)[0]

        # Run the H2K workflow
        success, stdout, stderr = run_h2k_workflow(input_path, temp_output_dir, debug=True)

        assert success, f"CLI workflow failed for {source_file}: {stderr}"

        # Test energy data validation
        print(f"🔍 Validating energy data for {source_file}...")
        _test_energy_validation(
            source_file, base_name, baseline_info, temp_output_dir, energy_tolerance_percent
        )

        # Test HPXML structure validation
        print(f"🔍 Validating HPXML structure for {source_file}...")
        _test_hpxml_validation(source_file, base_name, temp_output_dir)

        print(f"✅ Regression PASSED for {source_file}")

    finally:
        # Cleanup temp directory
        if os.path.exists(temp_output_dir):
            shutil.rmtree(temp_output_dir)


def _test_energy_validation(
    source_file, base_name, baseline_info, temp_output_dir, energy_tolerance_percent
):
    """Test energy data validation for a single file."""
    # Load baseline energy data
    baseline_energy_data = None
    try:
        baseline_data = load_baseline_file(base_name)
        if baseline_data:
            baseline_energy_data = baseline_data["energy_data"]
    except Exception as e:
        pytest.fail(f"Failed to load baseline energy data for {source_file}: {e}")

    assert baseline_energy_data, f"No baseline energy data found for {source_file}"

    # Find SQL file
    sql_path = find_sql_file(temp_output_dir, base_name)
    assert sql_path, f"SQL file not found for {source_file}"

    # Extract current energy data
    current_energy_data = extract_annual_energy_data(sql_path)
    assert current_energy_data, f"No energy data extracted for {source_file}"

    # Compare energy values
    energy_comparisons = compare_energy_values(
        baseline_energy_data, current_energy_data, energy_tolerance_percent
    )
    assert energy_comparisons, f"No valid comparisons generated for {source_file}"

    energy_passed = sum(1 for c in energy_comparisons if c.get("passed", False))
    energy_failed = len(energy_comparisons) - energy_passed

    assert (
        energy_failed == 0
    ), f"Energy validation failed for {source_file}: {energy_passed}/{len(energy_comparisons)} comparisons passed"

    # Save individual energy comparison
    energy_comparison_data = {
        "source_file": source_file,
        "baseline_file": baseline_info["baseline_file"],
        "test_date": datetime.now().isoformat(),
        "tolerance_percent": energy_tolerance_percent,
        "status": "PASS",
        "total_comparisons": len(energy_comparisons),
        "passed_comparisons": energy_passed,
        "failed_comparisons": energy_failed,
        "comparisons": energy_comparisons,
    }

    save_comparison_file(base_name, energy_comparison_data)
    print(f"✅ Energy validation PASSED: {energy_passed}/{len(energy_comparisons)} comparisons")


def _test_hpxml_validation(source_file, base_name, temp_output_dir):
    """Test HPXML structure validation for a single file."""
    # Find current HPXML file
    current_hpxml_path = find_hpxml_file(temp_output_dir, base_name)
    assert current_hpxml_path, f"Current HPXML not found for {source_file}"

    # Get baseline HPXML path
    from tests.utils import get_baseline_hpxml_path

    baseline_hpxml_path = get_baseline_hpxml_path(base_name)
    assert os.path.exists(baseline_hpxml_path), f"Baseline HPXML not found for {source_file}"

    # Compare HPXML files
    hpxml_comparison = compare_hpxml_files(baseline_hpxml_path, current_hpxml_path)

    assert hpxml_comparison.get(
        "files_match", False
    ), f"HPXML validation failed for {source_file}: {len(hpxml_comparison.get('differences', []))} differences found"

    # Save individual HPXML comparison
    from tests.utils import get_comparison_hpxml_path

    comparison_hpxml_path = get_comparison_hpxml_path(base_name)
    try:
        shutil.copy2(current_hpxml_path, comparison_hpxml_path)
    except Exception as e:
        print(f"⚠️  Could not save comparison HPXML: {e}")

    # Save comparison report
    import json

    hpxml_comparison_file = f"comparison_{base_name}_hpxml.json"
    hpxml_comparison_path = os.path.join(
        "tests/fixtures/expected_outputs/golden_files/comparison", hpxml_comparison_file
    )
    try:
        os.makedirs(os.path.dirname(hpxml_comparison_path), exist_ok=True)
        with open(hpxml_comparison_path, "w") as f:
            json.dump(hpxml_comparison, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save HPXML comparison report: {e}")

    print("✅ HPXML validation PASSED: Files match exactly")


@pytest.mark.regression
@pytest.mark.skip(
    reason="Use test_regression_parallel for better performance. This is kept for backward compatibility."
)
def test_regression_sequential(check_openstudio_bindings):
    """
    Sequential regression test for energy data and HPXML structure validation.

    DEPRECATED: Use test_regression_parallel for better performance.
    This function is kept for backward compatibility.
    """
    pass
