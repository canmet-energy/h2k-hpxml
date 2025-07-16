import pytest
import os
import shutil
from datetime import datetime
from tests.utils import workflow_utils, file_utils, hpxml_utils


def test_hpxml_comparison_against_baseline():
    """
    Test that generated HPXML files match baseline versions.
    
    This test runs the H2K to HPXML conversion workflow and compares
    the generated HPXML files against previously established baseline
    versions to detect any unintended changes in the conversion process.
    """
    
    # Get list of H2K files to test
    h2k_files = workflow_utils.get_h2k_example_files()
    
    if not h2k_files:
        pytest.skip("No H2K example files found in examples/ directory")
    
    # Ensure golden directories exist
    file_utils.ensure_golden_directories()
    
    results = {}
    all_passed = True
    temp_output_dir = "tests/temp/hpxml_comparison"
    
    # Clean and create temp directory
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)
    
    for h2k_file in h2k_files:
        base_name = os.path.splitext(h2k_file)[0]
        print(f"\n🔍 Testing HPXML generation for: {h2k_file}")
        
        # Run workflow to generate HPXML
        success, stdout, stderr = workflow_utils.run_h2k_workflow(
            f"examples/{h2k_file}", 
            temp_output_dir
        )
        
        if not success:
            results[base_name] = {
                "status": "FAILED",
                "error": "Workflow execution failed",
                "stderr": stderr,
                "stdout": stdout
            }
            all_passed = False
            print(f"❌ Workflow failed for {base_name}")
            continue
        
        # Find generated HPXML file
        generated_hpxml = workflow_utils.find_hpxml_file(temp_output_dir, base_name)
        if not generated_hpxml:
            results[base_name] = {
                "status": "FAILED", 
                "error": "Generated HPXML file not found",
                "directory_structure": workflow_utils.explore_output_directory(
                    os.path.join(temp_output_dir, base_name), max_depth=2
                )
            }
            all_passed = False
            print(f"❌ HPXML file not found for {base_name}")
            continue
        
        print(f"✅ Found generated HPXML: {generated_hpxml}")
        
        # Compare with baseline
        baseline_hpxml = file_utils.get_baseline_hpxml_path(base_name)
        if not os.path.exists(baseline_hpxml):
            results[base_name] = {
                "status": "FAILED",
                "error": f"Baseline HPXML not found: {baseline_hpxml}",
                "note": "Run baseline generation test to create baseline files"
            }
            all_passed = False
            print(f"❌ Baseline HPXML not found for {base_name}")
            continue
        
        # Perform comparison
        print(f"🔍 Comparing with baseline: {baseline_hpxml}")
        comparison_result = hpxml_utils.compare_hpxml_files(
            baseline_hpxml, generated_hpxml
        )
        
        # Copy generated HPXML to comparison directory for reference
        comparison_hpxml_path = file_utils.get_comparison_hpxml_path(base_name)
        try:
            shutil.copy2(generated_hpxml, comparison_hpxml_path)
            print(f"✅ Saved comparison HPXML: {comparison_hpxml_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not save comparison HPXML: {e}")
        
        # Save detailed comparison results
        detailed_comparison_path = file_utils.get_comparison_file_path(f"{base_name}_hpxml")
        file_utils.save_json_file(comparison_result, detailed_comparison_path)
        
        # Record results
        files_match = comparison_result.get("files_match", False)
        differences = comparison_result.get("differences", [])
        
        results[base_name] = {
            "status": "PASSED" if files_match else "FAILED",
            "files_match": files_match,
            "differences_count": len(differences),
            "differences": differences[:10],  # First 10 differences for summary
            "summary": comparison_result.get("summary", {}),
            "baseline_file": baseline_hpxml,
            "generated_file": generated_hpxml,
            "comparison_file": comparison_hpxml_path
        }
        
        if files_match:
            print(f"✅ HPXML comparison PASSED for {base_name}")
        else:
            print(f"❌ HPXML comparison FAILED for {base_name} - {len(differences)} differences")
            all_passed = False
            
            # Print first few differences for debugging
            if differences:
                print(f"   First differences:")
                for diff in differences[:3]:
                    print(f"     - {diff}")
                if len(differences) > 3:
                    print(f"     ... and {len(differences) - 3} more")
    
    # Create summary report
    summary_data = {
        "test_type": "hpxml_comparison",
        "test_date": datetime.now().isoformat(),
        "total_files": len(h2k_files),
        "passed": sum(1 for r in results.values() if r["status"] == "PASSED"),
        "failed": sum(1 for r in results.values() if r["status"] == "FAILED"),
        "results": results
    }
    
    # Save summary
    summary_path = file_utils.get_comparison_hpxml_summary_path()
    file_utils.save_json_file(summary_data, summary_path)
    
    print(f"\n📊 HPXML Comparison Summary:")
    print(f"   Total files tested: {summary_data['total_files']}")
    print(f"   Passed: {summary_data['passed']}")
    print(f"   Failed: {summary_data['failed']}")
    print(f"   Summary report: {summary_path}")
    
    if not all_passed:
        failed_files = [name for name, result in results.items() if result["status"] == "FAILED"]
        pytest.fail(f"HPXML comparison failed for {len(failed_files)} files: {failed_files}")


def test_hpxml_structure_validation():
    """
    Test that all generated HPXML files have valid structure.
    
    This test validates the structure and content of generated HPXML files
    without comparing them to baselines, ensuring they meet basic HPXML standards.
    """
    
    # Get list of H2K files to test
    h2k_files = workflow_utils.get_h2k_example_files()
    
    if not h2k_files:
        pytest.skip("No H2K example files found in examples/ directory")
    
    temp_output_dir = "tests/temp/hpxml_validation"
    
    # Clean and create temp directory
    if os.path.exists(temp_output_dir):
        shutil.rmtree(temp_output_dir)
    os.makedirs(temp_output_dir, exist_ok=True)
    
    validation_results = {}
    all_valid = True
    
    for h2k_file in h2k_files:
        base_name = os.path.splitext(h2k_file)[0]
        print(f"\n🔍 Validating HPXML structure for: {h2k_file}")
        
        # Run workflow to generate HPXML
        success, stdout, stderr = workflow_utils.run_h2k_workflow(
            f"examples/{h2k_file}", 
            temp_output_dir
        )
        
        if not success:
            validation_results[base_name] = {
                "is_valid": False,
                "error": "Workflow execution failed",
                "stderr": stderr
            }
            all_valid = False
            continue
        
        # Find generated HPXML file
        generated_hpxml = workflow_utils.find_hpxml_file(temp_output_dir, base_name)
        if not generated_hpxml:
            validation_results[base_name] = {
                "is_valid": False,
                "error": "Generated HPXML file not found"
            }
            all_valid = False
            continue
        
        # Validate HPXML structure
        validation_result = hpxml_utils.validate_hpxml_structure(generated_hpxml)
        validation_results[base_name] = validation_result
        
        if validation_result["is_valid"]:
            print(f"✅ HPXML structure valid for {base_name}")
        else:
            print(f"❌ HPXML structure invalid for {base_name}")
            all_valid = False
            
            # Print errors and warnings
            if validation_result.get("errors"):
                print(f"   Errors: {validation_result['errors']}")
            if validation_result.get("warnings"):
                print(f"   Warnings: {validation_result['warnings']}")
    
    print(f"\n📊 HPXML Structure Validation Summary:")
    valid_count = sum(1 for r in validation_results.values() if r.get("is_valid", False))
    print(f"   Total files tested: {len(h2k_files)}")
    print(f"   Valid: {valid_count}")
    print(f"   Invalid: {len(h2k_files) - valid_count}")
    
    if not all_valid:
        invalid_files = [name for name, result in validation_results.items() if not result.get("is_valid", False)]
        pytest.fail(f"HPXML structure validation failed for {len(invalid_files)} files: {invalid_files}")


if __name__ == "__main__":
    # Allow running individual tests
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "structure":
        test_hpxml_structure_validation()
    else:
        test_hpxml_comparison_against_baseline()