import json
import os

import pytest


def test_validate_baseline_summary():
    """Test that baseline energy summary file exists and contains valid data."""
    summary_file = (
        "tests/fixtures/expected_outputs/golden_files/baseline/baseline_energy_summary.json"
    )

    # Check that the summary file exists
    assert os.path.exists(summary_file), f"Baseline summary file '{summary_file}' does not exist."

    # Load and validate the summary data
    with open(summary_file) as f:
        summary_data = json.load(f)

    # Validate structure
    assert "generated_date" in summary_data, "Summary missing 'generated_date'"
    assert "results" in summary_data, "Summary missing 'results' section"
    assert len(summary_data["results"]) > 0, "No baseline results found in summary"

    # Validate each result entry
    for file_name, result_data in summary_data["results"].items():
        assert "source_file" in result_data, f"Missing 'source_file' for {file_name}"
        assert "baseline_file" in result_data, f"Missing 'baseline_file' for {file_name}"
        assert "sql_records" in result_data, f"Missing 'sql_records' for {file_name}"
        assert "processed_date" in result_data, f"Missing 'processed_date' for {file_name}"

        # Validate that sql_records has a reasonable count
        sql_records = result_data["sql_records"]
        assert isinstance(sql_records, int), f"sql_records should be an int for {file_name}"
        assert sql_records > 0, f"No SQL records found for {file_name}"

        # Check if individual baseline file exists
        baseline_file = result_data["baseline_file"]
        baseline_path = f"tests/fixtures/expected_outputs/golden_files/baseline/{baseline_file}"
        assert os.path.exists(
            baseline_path
        ), f"Individual baseline file '{baseline_path}' does not exist"

        print(f"✓ Validated {file_name}: {sql_records} SQL records, baseline file: {baseline_file}")


def test_validate_error_logs():
    """Test that error log files exist and contain no fatal errors in temp folder."""
    temp_dir = "tests/temp"

    if not os.path.exists(temp_dir):
        pytest.skip(
            f"Temp directory '{temp_dir}' does not exist - run tests first to generate simulation outputs"
        )

    # Check for error files in each simulation directory in temp folder
    found_error_files = False
    for dir_name in os.listdir(temp_dir):
        dir_path = os.path.join(temp_dir, dir_name)
        if os.path.isdir(dir_path):
            # Look for error files in subdirectories
            for subdir in os.listdir(dir_path):
                subdir_path = os.path.join(dir_path, subdir)
                if os.path.isdir(subdir_path):
                    err_path = os.path.join(subdir_path, "run", "eplusout.err")

                    if os.path.exists(err_path):
                        found_error_files = True
                        # Read and check error file content
                        with open(err_path) as f:
                            error_content = f.read()

                        # Check for fatal errors
                        fatal_keywords = ["** Fatal **", "**FATAL**", "EnergyPlus Terminated"]
                        fatal_errors = []

                        for line in error_content.split("\n"):
                            for keyword in fatal_keywords:
                                if keyword in line:
                                    fatal_errors.append(line.strip())

                        assert (
                            len(fatal_errors) == 0
                        ), f"Fatal errors found in {err_path}: {fatal_errors}"
                        print(f"✓ No fatal errors in: {err_path}")

    if not found_error_files:
        print(
            "ℹ️  No error files found in temp directory - simulation outputs may have been cleaned up"
        )
