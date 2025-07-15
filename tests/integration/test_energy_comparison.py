import pytest
import subprocess
import os
import tempfile
import json
import shutil
from datetime import datetime
from tests.utils import (
    extract_annual_energy_data, 
    run_h2k_workflow, 
    find_sql_file,
    compare_energy_values,
    load_baseline_summary,
    load_baseline_file,
    get_baseline_summary_path,
    save_comparison_summary,
    save_comparison_file
)


def test_energy_comparison_regression(check_openstudio_bindings):
    """Test energy comparison between current outputs and golden master files.
    
    This test runs the current CLI tool and compares the energy outputs
    against previously generated baseline (golden master) files.
    """
    examples_dir = "examples"
    tolerance_percent = 5.0  # 5% tolerance as specified in requirements

    # Ensure the examples directory exists
    assert os.path.exists(examples_dir), f"Examples directory '{examples_dir}' does not exist."

    # Load baseline energy data using shared utility
    baseline_summary_file = get_baseline_summary_path()
    assert os.path.exists(baseline_summary_file), f"Baseline summary file not found: {baseline_summary_file}"
    
    baseline_summary = load_baseline_summary()
    assert baseline_summary, "Failed to load baseline summary"
    assert "results" in baseline_summary, "Baseline summary missing 'results' section"
    
    # Create temp directory for current run outputs
    temp_output_dir = "tests/temp/comparison_runs"
    # Make sure the temp directory is empty and exists
    if os.path.exists(temp_output_dir):
        # remove the temp directory if it exists
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)
    
    test_results = {
        "test_date": datetime.now().isoformat(),
        "tolerance_percent": tolerance_percent,
        "files_tested": 0,
        "files_passed": 0,
        "files_failed": 0,
        "details": {}
    }

    # Test each file that has baseline data
    for base_name, baseline_info in baseline_summary["results"].items():
        source_file = baseline_info["source_file"]
        input_path = os.path.join(examples_dir, source_file)
        
        # Skip if source file no longer exists
        if not os.path.exists(input_path):
            print(f"Skipping {source_file}: file not found")
            continue

        print(f"Testing energy comparison for {source_file}...")
        
        # Load individual baseline file using shared utility
        baseline_data = load_baseline_file(base_name)
        if not baseline_data:
            test_results["files_failed"] += 1
            test_results["details"][base_name] = {
                "status": "MISSING_BASELINE",
                "error": f"Failed to load baseline file for {base_name}",
                "comparison": None
            }
            continue
            
        baseline_energy_data = baseline_data["energy_data"]

        # Run the current CLI tool using shared utility
        success, stdout, stderr = run_h2k_workflow(input_path, temp_output_dir, debug=True)

        test_results["files_tested"] += 1

        if not success:
            test_results["files_failed"] += 1
            test_results["details"][base_name] = {
                "status": "CLI_FAILED",
                "error": stderr,
                "comparison": None
            }
            continue

        # Find the SQL file using shared utility
        sql_path = find_sql_file(temp_output_dir, base_name)
        
        if not sql_path:
            test_results["files_failed"] += 1
            test_results["details"][base_name] = {
                "status": "MISSING_SQL",
                "error": f"eplusout.sql not found for {base_name}",
                "comparison": None
            }
            continue

        # Extract current energy data using shared utility
        current_energy_data = extract_annual_energy_data(sql_path)

        # Compare energy values using shared utility
        comparisons = compare_energy_values(baseline_energy_data, current_energy_data, tolerance_percent)
        
        # Calculate statistics from comparison results
        if comparisons and len(comparisons) > 0:
            passed_count = sum(1 for c in comparisons if c.get('passed', False))
            failed_count = len(comparisons) - passed_count
            total_count = len(comparisons)
            
            if failed_count == 0:
                file_status = "PASS"
                test_results["files_passed"] += 1
            else:
                file_status = "FAIL"
                test_results["files_failed"] += 1
        else:
            file_status = "FAIL"
            test_results["files_failed"] += 1
            passed_count = 0
            failed_count = 0
            total_count = 0

        # Create individual comparison report
        individual_comparison = {
            "source_file": source_file,
            "baseline_file": baseline_info["baseline_file"],
            "test_date": datetime.now().isoformat(),
            "tolerance_percent": tolerance_percent,
            "status": file_status,
            "total_comparisons": total_count,
            "passed_comparisons": passed_count,
            "failed_comparisons": failed_count,
            "comparisons": comparisons
        }
        
        # Save individual comparison report using shared utility
        save_comparison_file(base_name, individual_comparison)

        test_results["details"][base_name] = {
            "status": file_status,
            "source_file": source_file,
            "comparison_file": f"comparison_{base_name}.json",
            "passed_comparisons": passed_count,
            "failed_comparisons": failed_count,
            "total_comparisons": total_count
        }

        print(f"✓ {source_file}: {passed_count}/{total_count} comparisons passed")

    # Generate summary report using shared utility
    save_comparison_summary(test_results)
    print(f"Summary: {test_results['files_passed']}/{test_results['files_tested']} files passed")

    # Assert that all tests passed
    if test_results["files_failed"] > 0:
        failed_files = [name for name, details in test_results["details"].items() 
                      if details["status"] != "PASS"]
        pytest.fail(f"Energy comparison failed for {test_results['files_failed']} files: {failed_files}")
