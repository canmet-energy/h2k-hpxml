"""
Regression test for energy data and HPXML structure validation.

This test runs the H2K workflow once per file and validates both energy data
and HPXML structure in a single pass, making it more efficient than running
separate tests.
"""

import pytest
import os
import shutil
from datetime import datetime
from tests.utils import (
    extract_annual_energy_data,
    find_sql_file,
    find_hpxml_file,
    run_h2k_workflow,
    compare_energy_values,
    compare_hpxml_files,
    get_baseline_summary_path,
    get_comparison_summary_path,
    get_baseline_hpxml_summary_path,
    get_comparison_hpxml_summary_path,
    load_baseline_summary,
    load_baseline_file,
    save_comparison_summary,
    save_comparison_file
)


@pytest.mark.regression
def test_regression(check_openstudio_bindings):
    """
    Regression test for energy data and HPXML structure validation.
    
    This test runs each H2K file through the workflow once and validates:
    1. Energy data comparison against baseline (with tolerance)
    2. HPXML structure comparison against baseline (exact match)
    
    This is more efficient than running separate tests since it avoids
    duplicate simulation runs.
    """
    examples_dir = "examples"
    energy_tolerance_percent = 5.0  # 5% tolerance for energy data
    
    # Setup output directories
    temp_output_dir = "tests/temp/regression"
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)
    
    # Load baseline data
    baseline_summary_file = get_baseline_summary_path()
    assert os.path.exists(baseline_summary_file), f"Baseline summary file not found: {baseline_summary_file}"
    
    baseline_summary = load_baseline_summary()
    assert baseline_summary, "Failed to load baseline summary"
    assert "results" in baseline_summary, "Baseline summary missing 'results' section"
    
    # Test results tracking
    combined_results = {
        "test_date": datetime.now().isoformat(),
        "energy_tolerance_percent": energy_tolerance_percent,
        "files_tested": 0,
        "files_passed": 0,
        "files_failed": 0,
        "energy_failures": 0,
        "hpxml_failures": 0,
        "details": {}
    }
    
    energy_comparison_results = {
        "test_date": datetime.now().isoformat(),
        "tolerance_percent": energy_tolerance_percent,
        "files_tested": 0,
        "files_passed": 0,
        "files_failed": 0,
        "details": {}
    }
    
    hpxml_comparison_results = {
        "test_date": datetime.now().isoformat(),
        "files_tested": 0,
        "files_passed": 0,
        "files_failed": 0,
        "details": {}
    }
    
    failed_files = []
    
    # Test each file that has baseline data
    for source_file, baseline_info in baseline_summary["results"].items():
        input_path = os.path.join(examples_dir, source_file)
        
        # Skip if source file no longer exists
        if not os.path.exists(input_path):
            print(f"Skipping {source_file}: file not found")
            continue
            
        print(f"\\n🔄 Testing Regression for {source_file}...")
        
        # Extract base name for file utilities
        base_name = os.path.splitext(source_file)[0]
        
        # Run the H2K workflow once
        success, stdout, stderr = run_h2k_workflow(input_path, temp_output_dir, debug=True)
        
        combined_results["files_tested"] += 1
        energy_comparison_results["files_tested"] += 1
        hpxml_comparison_results["files_tested"] += 1
        
        if not success:
            print(f"❌ CLI workflow failed for {source_file}")
            combined_results["files_failed"] += 1
            energy_comparison_results["files_failed"] += 1
            hpxml_comparison_results["files_failed"] += 1
            
            combined_results["details"][source_file] = {
                "status": "CLI_FAILED",
                "error": stderr,
                "energy_status": "SKIPPED",
                "hpxml_status": "SKIPPED"
            }
            
            failed_files.append(source_file)
            continue
        
        # Initialize file result tracking
        file_result = {
            "source_file": source_file,
            "status": "PASS",
            "energy_status": "UNKNOWN",
            "hpxml_status": "UNKNOWN",
            "energy_details": {},
            "hpxml_details": {}
        }
        
        # ===================
        # 1. ENERGY DATA TEST
        # ===================
        
        print(f"🔍 Validating energy data for {source_file}...")
        
        # Load baseline energy data
        baseline_energy_data = None
        try:
            baseline_data = load_baseline_file(base_name)
            if baseline_data:
                baseline_energy_data = baseline_data["energy_data"]
        except Exception as e:
            print(f"⚠️  Failed to load baseline energy data: {e}")
        
        if baseline_energy_data:
            # Find SQL file
            sql_path = find_sql_file(temp_output_dir, base_name)
            
            if sql_path:
                # Extract current energy data
                current_energy_data = extract_annual_energy_data(sql_path)
                
                if current_energy_data:
                    # Compare energy values
                    energy_comparisons = compare_energy_values(
                        baseline_energy_data, current_energy_data, energy_tolerance_percent
                    )
                    
                    if energy_comparisons:
                        energy_passed = sum(1 for c in energy_comparisons if c.get('passed', False))
                        energy_failed = len(energy_comparisons) - energy_passed
                        
                        if energy_failed == 0:
                            file_result["energy_status"] = "PASS"
                            energy_comparison_results["files_passed"] += 1
                            print(f"✅ Energy validation PASSED: {energy_passed}/{len(energy_comparisons)} comparisons")
                        else:
                            file_result["energy_status"] = "FAIL"
                            file_result["status"] = "FAIL"
                            energy_comparison_results["files_failed"] += 1
                            combined_results["energy_failures"] += 1
                            print(f"❌ Energy validation FAILED: {energy_passed}/{len(energy_comparisons)} comparisons passed")
                        
                        # Save individual energy comparison
                        energy_comparison_data = {
                            "source_file": source_file,
                            "baseline_file": baseline_info["baseline_file"],
                            "test_date": datetime.now().isoformat(),
                            "tolerance_percent": energy_tolerance_percent,
                            "status": file_result["energy_status"],
                            "total_comparisons": len(energy_comparisons),
                            "passed_comparisons": energy_passed,
                            "failed_comparisons": energy_failed,
                            "comparisons": energy_comparisons
                        }
                        
                        save_comparison_file(base_name, energy_comparison_data)
                        
                        file_result["energy_details"] = {
                            "total_comparisons": len(energy_comparisons),
                            "passed_comparisons": energy_passed,
                            "failed_comparisons": energy_failed,
                            "comparison_file": f"comparison_{base_name}.json"
                        }
                        
                        energy_comparison_results["details"][source_file] = {
                            "status": file_result["energy_status"],
                            "source_file": source_file,
                            "comparison_file": f"comparison_{base_name}.json",
                            "passed_comparisons": energy_passed,
                            "failed_comparisons": energy_failed,
                            "total_comparisons": len(energy_comparisons)
                        }
                        
                    else:
                        file_result["energy_status"] = "FAIL"
                        file_result["status"] = "FAIL"
                        energy_comparison_results["files_failed"] += 1
                        combined_results["energy_failures"] += 1
                        print(f"❌ Energy validation FAILED: No valid comparisons generated")
                else:
                    file_result["energy_status"] = "FAIL"
                    file_result["status"] = "FAIL"
                    energy_comparison_results["files_failed"] += 1
                    combined_results["energy_failures"] += 1
                    print(f"❌ Energy validation FAILED: No energy data extracted")
            else:
                file_result["energy_status"] = "FAIL"
                file_result["status"] = "FAIL"
                energy_comparison_results["files_failed"] += 1
                combined_results["energy_failures"] += 1
                print(f"❌ Energy validation FAILED: SQL file not found")
        else:
            file_result["energy_status"] = "FAIL"
            file_result["status"] = "FAIL"
            energy_comparison_results["files_failed"] += 1
            combined_results["energy_failures"] += 1
            print(f"❌ Energy validation FAILED: No baseline energy data")
        
        # ================
        # 2. HPXML TEST
        # ================
        
        print(f"🔍 Validating HPXML structure for {source_file}...")
        
        # Find current HPXML file
        current_hpxml_path = find_hpxml_file(temp_output_dir, base_name)
        
        if current_hpxml_path:
            # Get baseline HPXML path
            from tests.utils import get_baseline_hpxml_path
            baseline_hpxml_path = get_baseline_hpxml_path(base_name)
            
            if os.path.exists(baseline_hpxml_path):
                # Compare HPXML files
                hpxml_comparison = compare_hpxml_files(baseline_hpxml_path, current_hpxml_path)
                
                if hpxml_comparison.get("files_match", False):
                    file_result["hpxml_status"] = "PASS"
                    hpxml_comparison_results["files_passed"] += 1
                    print(f"✅ HPXML validation PASSED: Files match exactly")
                else:
                    file_result["hpxml_status"] = "FAIL"
                    file_result["status"] = "FAIL"
                    hpxml_comparison_results["files_failed"] += 1
                    combined_results["hpxml_failures"] += 1
                    differences = hpxml_comparison.get("differences", [])
                    print(f"❌ HPXML validation FAILED: {len(differences)} differences found")
                    if differences:
                        print(f"   First differences: {differences[:3]}")
                
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
                hpxml_comparison_path = os.path.join("tests/fixtures/expected_outputs/golden_files/comparison", hpxml_comparison_file)
                try:
                    with open(hpxml_comparison_path, 'w') as f:
                        json.dump(hpxml_comparison, f, indent=2)
                except Exception as e:
                    print(f"⚠️  Could not save HPXML comparison report: {e}")
                
                file_result["hpxml_details"] = {
                    "files_match": hpxml_comparison.get("files_match", False),
                    "total_differences": len(hpxml_comparison.get("differences", [])),
                    "comparison_file": hpxml_comparison_file
                }
                
                hpxml_comparison_results["details"][source_file] = {
                    "status": file_result["hpxml_status"],
                    "source_file": source_file,
                    "comparison_file": hpxml_comparison_file,
                    "files_match": hpxml_comparison.get("files_match", False),
                    "total_differences": len(hpxml_comparison.get("differences", []))
                }
                
            else:
                file_result["hpxml_status"] = "FAIL"
                file_result["status"] = "FAIL"
                hpxml_comparison_results["files_failed"] += 1
                combined_results["hpxml_failures"] += 1
                print(f"❌ HPXML validation FAILED: Baseline HPXML not found")
        else:
            file_result["hpxml_status"] = "FAIL"
            file_result["status"] = "FAIL"
            hpxml_comparison_results["files_failed"] += 1
            combined_results["hpxml_failures"] += 1
            print(f"❌ HPXML validation FAILED: Current HPXML not found")
        
        # Update overall results
        if file_result["status"] == "PASS":
            combined_results["files_passed"] += 1
            print(f"✅ Regression PASSED for {source_file}")
        else:
            combined_results["files_failed"] += 1
            failed_files.append(source_file)
            print(f"❌ Regression FAILED for {source_file}")
        
        combined_results["details"][source_file] = file_result
    
    # Save summary reports
    save_comparison_summary(energy_comparison_results)
    
    hpxml_summary_path = get_comparison_hpxml_summary_path()
    try:
        import json
        with open(hpxml_summary_path, 'w') as f:
            json.dump(hpxml_comparison_results, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save HPXML summary: {e}")
    
    # Save combined summary
    combined_summary_path = "tests/fixtures/expected_outputs/golden_files/comparison/comparison_combined_summary.json"
    try:
        import json
        with open(combined_summary_path, 'w') as f:
            json.dump(combined_results, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save combined summary: {e}")
    
    # Print final summary
    print(f"\\n📊 Regression Test Summary:")
    print(f"   Total files tested: {combined_results['files_tested']}")
    print(f"   Overall passed: {combined_results['files_passed']}")
    print(f"   Overall failed: {combined_results['files_failed']}")
    print(f"   Energy failures: {combined_results['energy_failures']}")
    print(f"   HPXML failures: {combined_results['hpxml_failures']}")
    
    # Assert that all tests passed
    if combined_results["files_failed"] > 0:
        pytest.fail(f"Regression failed for {combined_results['files_failed']} files: {failed_files}")