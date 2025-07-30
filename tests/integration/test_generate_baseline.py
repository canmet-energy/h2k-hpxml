import json
import os
import shutil
import subprocess
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

from tests.utils import clean_for_baseline_generation
from tests.utils import extract_annual_energy_data


@pytest.mark.baseline_generation
@pytest.mark.skip(
    reason="Baseline generation should only be run explicitly with --run-baseline flag"
)
def test_generate_baseline(check_openstudio_bindings):
    """Test generating baseline expected outputs and energy summary.

    WARNING: This test overwrites golden master files!
    Only run when you need to update the baseline with verified stable code.
    """
    # Additional safety check
    if os.getenv("CI") != "true":  # Skip confirmation in CI environments
        response = input(
            "\n⚠️  WARNING: This will overwrite golden master files!\n"
            "Only proceed if you're updating baseline with verified stable code.\n"
            "Type 'YES' to continue: "
        )
        if response != "YES":
            pytest.skip("Baseline generation cancelled by user")

    # Clean up previous test runs for fresh baseline generation
    print("\n🧹 Cleaning previous test data for fresh baseline generation...")
    cleanup_success, cleaned_items = clean_for_baseline_generation()

    if not cleanup_success:
        pytest.fail("Failed to clean previous test data. Cannot proceed with baseline generation.")

    print(f"✅ Cleanup completed successfully. Cleaned {len(cleaned_items)} items.")

    examples_dir = "examples"
    # Use temp folder for simulation outputs, golden_files for JSON baselines
    temp_output_dir = "tests/temp"
    golden_files_dir = "tests/fixtures/expected_outputs/golden_files/baseline"
    summary_file = os.path.join(golden_files_dir, "baseline_energy_summary.json")

    # Ensure the examples directory exists
    assert os.path.exists(examples_dir), f"Examples directory '{examples_dir}' does not exist."

    # Ensure temp directory exists for simulation outputs
    os.makedirs(temp_output_dir, exist_ok=True)

    # Create backup of existing golden files
    backup_dir = f"{golden_files_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists(golden_files_dir) and os.listdir(golden_files_dir):
        print(f"📦 Creating backup of existing golden files: {backup_dir}")
        shutil.copytree(golden_files_dir, backup_dir)

    # Ensure golden files directory exists
    os.makedirs(golden_files_dir, exist_ok=True)

    results = {}
    h2k_files = [f for f in os.listdir(examples_dir) if f.endswith(".h2k") or f.endswith(".H2K")]

    for h2k_file in h2k_files:
        input_path = os.path.join(examples_dir, h2k_file)
        base_name = os.path.splitext(h2k_file)[0]
        file_name = os.path.basename(input_path)

        print(f"Processing {file_name} for detailed analysis...")

        # Run the CLI tool to generate outputs in temp directory
        result = subprocess.run(
            [
                "python",
                "-m",
                "h2k_hpxml.cli.convert",
                "run",
                "--input_path",
                input_path,
                "--output_path",
                temp_output_dir,
                "--debug",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "/workspaces/h2k_hpxml/src:/workspaces/h2k_hpxml"},
        )

        print(f"CLI stdout: {result.stdout}")
        if result.stderr:
            print(f"CLI stderr: {result.stderr}")

        # Check that the command ran successfully
        assert result.returncode == 0, f"CLI failed for {file_name}: {result.stderr}"

        # Verify that the expected output files were created in temp directory
        expected_output_path = os.path.join(temp_output_dir, base_name)
        assert os.path.exists(
            expected_output_path
        ), f"Output directory '{expected_output_path}' was not created."

        # Define explore_directory function for debugging
        def explore_directory(path, max_depth=3, current_depth=0):
            items = []
            if current_depth >= max_depth:
                return items

            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        items.append(f"{'  ' * current_depth}📁 {item}/")
                        items.extend(explore_directory(item_path, max_depth, current_depth + 1))
                    else:
                        items.append(f"{'  ' * current_depth}📄 {item}")
            except PermissionError:
                items.append(f"{'  ' * current_depth}❌ Permission denied")
            return items

        # Look for the SQL file in multiple possible locations
        sql_patterns = [
            os.path.join(expected_output_path, "run", "eplusout.sql"),
            os.path.join(expected_output_path, "eplusout.sql"),
            os.path.join(temp_output_dir, "run", "eplusout.sql"),
            os.path.join(temp_output_dir, "eplusout.sql"),
        ]

        sql_path = None
        for pattern in sql_patterns:
            if os.path.exists(pattern):
                sql_path = pattern
                print(f"Found SQL file at: {sql_path}")
                break

        if not sql_path:
            # If not found, explore the directory structure for debugging
            print(f"\n=== Directory structure of {expected_output_path} ===")
            structure = explore_directory(expected_output_path)
            for line in structure:
                print(line)

            # Also check if it might be directly in temp_output_dir
            print(f"\n=== Also checking temp_output_dir: {temp_output_dir} ===")
            sql_path_exploration = explore_directory(temp_output_dir)
            for line in sql_path_exploration:
                print(line)

        # Find SQL file using a more robust approach
        import glob

        sql_files = glob.glob(f"{expected_output_path}/**/eplusout.sql", recursive=True)
        if not sql_files:
            sql_files = glob.glob(f"{temp_output_dir}/**/eplusout.sql", recursive=True)

        if sql_files:
            sql_path = sql_files[0]
            print(f"Found SQL file via glob: {sql_path}")
        else:
            print(f"❌ No SQL file found for {file_name}")
            print(f"Checked patterns: {sql_patterns}")
            continue

        # Extract energy data from the SQL file
        print(f"Extracting energy data from: {sql_path}")
        energy_data = extract_annual_energy_data(sql_path)

        if not energy_data:
            print(f"❌ No energy data extracted for {file_name}")
            continue

        # Save individual baseline file
        baseline_filename = f"baseline_{base_name}.json"
        baseline_path = os.path.join(golden_files_dir, baseline_filename)

        baseline_data = {
            "source_file": file_name,
            "energy_data": energy_data,
            "sql_records": len(energy_data),
            "processed_date": datetime.now().isoformat(),
            "generated_by": "test_generate_baseline.py",
        }

        with open(baseline_path, "w") as f:
            json.dump(baseline_data, f, indent=2)

        # Find and save HPXML file as baseline
        from tests.utils import workflow_utils

        hpxml_file = workflow_utils.find_hpxml_file(temp_output_dir, base_name)
        hpxml_baseline_saved = False

        if hpxml_file:
            from tests.utils import file_utils

            baseline_hpxml_path = file_utils.get_baseline_hpxml_path(base_name)
            try:
                shutil.copy2(hpxml_file, baseline_hpxml_path)
                hpxml_baseline_saved = True
                print(f"✅ Saved baseline HPXML: {baseline_hpxml_path}")
            except Exception as e:
                print(f"⚠️  Warning: Could not save baseline HPXML: {e}")
        else:
            print(f"⚠️  HPXML file not found for {base_name}")

        # Store summary info
        results[file_name] = {
            "source_file": file_name,
            "baseline_file": baseline_filename,
            "hpxml_baseline": f"baseline_{base_name}.xml" if hpxml_baseline_saved else None,
            "sql_records": len(energy_data),
            "processed_date": datetime.now().isoformat(),
        }

        print(f"✅ Generated baseline for {file_name}: {len(energy_data)} energy records")

    # Generate energy summary file
    summary_data = {
        "generated_date": datetime.now().isoformat(),
        "results": results,
        "total_files": len(results),
        "generated_by": "test_generate_baseline.py",
    }

    with open(summary_file, "w") as f:
        json.dump(summary_data, f, indent=2)

    # Generate HPXML summary file
    from tests.utils import file_utils

    hpxml_summary_path = file_utils.get_baseline_hpxml_summary_path()
    hpxml_files_with_baselines = []

    for base_name, result in results.items():
        if result.get("hpxml_baseline"):
            hpxml_path = file_utils.get_baseline_hpxml_path(
                base_name.replace(".h2k", "").replace(".H2K", "")
            )
            if os.path.exists(hpxml_path):
                hpxml_files_with_baselines.append(hpxml_path)

    if hpxml_files_with_baselines:
        from tests.utils import hpxml_utils

        hpxml_summary_data = hpxml_utils.create_hpxml_summary(hpxml_files_with_baselines)
        hpxml_summary_data["generated_date"] = datetime.now().isoformat()
        hpxml_summary_data["generated_by"] = "test_generate_baseline.py"

        with open(hpxml_summary_path, "w") as f:
            json.dump(hpxml_summary_data, f, indent=2)

        print(f"✅ Generated HPXML summary: {hpxml_summary_path}")
    else:
        print("⚠️  No HPXML baseline files found for summary generation")

    print("\n🎉 Baseline generation complete!")
    print(f"📄 Summary file: {summary_file}")
    print(f"📁 Individual files: {golden_files_dir}")
    print(f"📦 Backup created: {backup_dir}")
    print(f"🗂️  Simulation outputs: {temp_output_dir}")
    print(f"📊 Total files processed: {len(results)}")

    # Validate the summary file was created
    assert os.path.exists(summary_file), f"Summary file '{summary_file}' was not created."
    assert len(results) > 0, "No results were generated."
