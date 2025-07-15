# Regression Testing using Golden Files

## Objective
Develop a regression testing framework that uses golden files to ensure the workflow continues to operate correctly when source-code changes occur in bin/h2k2hpxml.py CLI. 

This implementation combines two testing approaches:
1. **Regression Testing**: Detecting whether recent code changes have broken previously working functionality
2. **Golden File Testing**: Using pre-approved output files (golden masters) as the reference point for comparisons

The golden files serve as our "known good state" for regression testing, allowing us to detect unintended changes in the system's behavior.

## Requirements
* The testing framework should be developed using pytest.
* The tests should be contained in the `tests` folder and follow a typical folder structure for tests, fixtures, and expected_outputs.
* Usage of Python's built-in SQLite and the Python OpenStudio SDK is encouraged to reduce the complexity of test code.
* Individual JSON files per simulation for better scalability and manageability.
* Compact summary index files for quick overview of test results.
* Robust comparison logic that handles EnergyPlus optimization differences (e.g., missing zero-value components).

## Workflow

### 1. Generate Reference Files (Golden Masters)
Run the workflow using a stable, verified version of the code to generate reference files. These files (our "golden masters") are stored in `tests/fixtures/expected_outputs/` and serve two purposes:
1. **Regression Testing**: They represent the "known good state" against which we can detect unintended changes
2. **Golden Files**: They serve as approved, correct outputs that future runs should match within tolerance

The reference files are only updated when intentional changes to the system's behavior are made and verified.

### 2. Verify Workflow Consistency
Run all files in the `examples` folder. For each run, check that each step was completed:
* Convert H2K file to HPXML file.
* A weather file was assigned to the HPXML.
* An OSM file was created.
* An IDF file was created.
* The simulation was run without errors.
* Energy end-use annual values are the same within a **5% percentage difference tolerance** from the expected_output result.

### 3. Validate Simulation Outputs
* Ensure the presence of key output files (`eplusout.sql`, `eplusout.err`).
* Validate that `eplusout.err` contains no fatal errors.
* Query the SQLite database (`eplusout.sql`) to extract annual energy end-use values for validation.

### 4. OpenStudio SDK Check
* Ensure the OpenStudio Python SDK is available before running tests. Skip tests if it's not installed.

### 5. Parallel Execution
* Configure pytest to run tests in parallel using the `pytest-xdist` plugin to speed up execution.

### 6. Summary Report
* Create a summary of all the runs in a markdown document. Include:
  * Pass/Fail status for each test.
  * Detailed logs for failures.
  * Discrepancies in results (if any).

## Implementation Status

### ✅ Completed Components

#### 1. Test Structure
```
tests/
├── integration/
│   ├── test_generate_baseline.py     # Baseline generation test
│   └── test_energy_comparison.py     # Regression comparison test
├── fixtures/
│   └── expected_outputs/
│       └── golden_files/            # 🔒 PERMANENT: Golden master files (version controlled)
│           ├── baseline/           # Reference outputs from stable code
│           │   ├── baseline_energy_summary.json      # Compact index (1.2K)
│           │   ├── baseline_WizardHouse_0.26.json   # Individual baseline (19K)
│           │   ├── baseline_WizardHouse_0.325.json  # Individual baseline (19K)
│           │   ├── baseline_WizardHouse_0.13.json   # Individual baseline (19K)
│           │   ├── baseline_WizardHouse_0.195.json  # Individual baseline (19K)
│           │   └── baseline_WizardHouse.json        # Individual baseline (19K)
│           ├── comparison/         # 🗑️ TEMPORARY: Test results (gitignored)
│           │   ├── comparison_energy_summary.json   # Test results index (gitignored)
│           │   ├── comparison_WizardHouse_0.26.json # Individual results (gitignored)
│           │   ├── comparison_WizardHouse_0.325.json
│           │   ├── comparison_WizardHouse_0.13.json
│           │   ├── comparison_WizardHouse_0.195.json
│           │   └── comparison_WizardHouse.json
│           └── backup_*/           # Timestamped safety backups
├── temp/                           # 🗑️ TEMPORARY: All simulation outputs (gitignored)
│   ├── WizardHouse/                # Baseline generation simulation outputs
│   │   ├── run/                    # EnergyPlus simulation results
│   │   │   ├── eplusout.sql
│   │   │   ├── eplusout.err
│   │   │   └── [other EnergyPlus outputs]
│   │   └── *.xml                   # Generated HPXML files
│   ├── WizardHouse_0.26/           # More simulation outputs...
│   └── comparison_runs/            # Comparison test simulation outputs
│       ├── WizardHouse/
│       ├── WizardHouse_0.26/
│       └── [other comparison simulation directories]
├── unit/                           # Unit tests for validation
│   └── test_validate_eplusout_sql.py  # Golden file integrity validation
├── utils/                          # Common test utilities (reduces code duplication)
│   ├── __init__.py                 # Exports common functions
│   ├── sql_utils.py                # SQL data extraction utilities
│   ├── workflow_utils.py           # H2K workflow execution utilities
│   ├── file_utils.py               # Golden file management utilities
│   └── comparison_utils.py         # Energy data comparison utilities
└── conftest.py                     # Pytest configuration with safety controls
```

#### 2. Golden Master Generation (`test_generate_baseline.py`)
- **Purpose**: Generate golden master (baseline) energy data from H2K files
- **Scope**: Processes all 5 H2K files in `examples/` folder  
- **Output**: Individual golden JSON files per simulation + compact summary index
- **Golden File Role**: These files serve as the approved reference point against which all future changes are validated
- **Safety Measures**: 
  - Requires explicit `--run-baseline` flag to run
  - Interactive confirmation prompt (type 'YES' to proceed)
  - Automatic backup of existing golden files before overwriting
  - Skipped by default in normal test runs
- **Data Extraction**: 
  - Meter data from `ReportDataDictionary` and `ReportData` tables
  - TabularData energy reports with proper filtering
  - Hierarchical JSON structure for easy comparison
- **File Structure**: Each baseline file contains:
  ```json
  {
    "source_file": "WizardHouse_0.26.h2k",
    "energy_data": { /* detailed energy breakdown */ },
    "sql_records": 19,
    "processed_date": "2025-07-15T15:20:13.603178",
    "generated_by": "test_generate_baseline.py"
  }
  ```

#### 3. Energy Comparison Testing (`test_energy_comparison.py`)
- **Purpose**: Validate current code changes against stable baseline
- **Scope**: All 5 H2K files with individual comparison reports
- **Tolerance**: 5% percentage difference as specified in requirements
- **Results**: 96/96 comparisons passed for all files (100% success rate)
- **Features**:
  - Individual comparison files per simulation
  - Compact summary with pass/fail status
  - Robust handling of EnergyPlus optimization differences
  - Missing zero-value component tolerance

#### 4. Data Extraction and Comparison Logic
- **SQL Queries**: Synchronized between baseline generation and comparison
- **Energy Data**: Comprehensive extraction from SQLite database
  - Meter data: `Electricity:Facility`, `NaturalGas:Facility`, etc.
  - Tabular data: `AnnualBuildingUtilityPerformanceSummary`, `EnergyMeters`, etc.
- **Comparison Algorithm**:
  - Percentage difference calculation with configurable tolerance
  - Zero-value component handling (missing = acceptable if baseline is 0.0)
  - Detailed path-based comparison for precise error identification

#### 5. File Management Optimization
- **Before**: Monolithic 141K JSON files (3,903 lines)
- **After**: Individual 19-26K files + compact 1.2-1.4K summary indexes
- **Benefits**: Better scalability, navigation, maintenance, and performance

#### 6. Common Test Utilities ✅ COMPLETED
- **Purpose**: Reduce code duplication and improve maintainability across test modules
- **Achievement**: Successfully eliminated 200+ lines of duplicated SQL extraction code
- **Status**: All shared utilities working correctly and imported successfully
- **Modules**:
  - `sql_utils.py`: Standardized SQL data extraction with improved database compatibility
    - ✅ Fixed TabularData extraction with proper string table joins
    - ✅ Enhanced database inspection and structure analysis
    - ✅ Comprehensive energy data validation functions
  - `workflow_utils.py`: H2K workflow execution, output file discovery, directory exploration
  - `file_utils.py`: Golden file path management, JSON operations, backup creation
  - `comparison_utils.py`: Energy data comparison, tolerance calculations, report generation
- **Benefits**: Consistent behavior, easier maintenance, reduced inconsistencies between tests
- **Usage**: `from tests.utils import extract_annual_energy_data, compare_energy_values`
- **Impact**: Current extraction finds 77 energy values vs 24 with old method (220% improvement)

### ✅ Test Results Summary
```
Current Status: CODE DEDUPLICATION COMPLETED ✅ / GOLDEN FILES NEED UPDATE ⚠️

Code Structure:
├── Shared Utilities Framework: ✅ COMPLETE
│   ├── sql_utils.py: ✅ SQL extraction with improved database compatibility
│   ├── workflow_utils.py: ✅ H2K workflow execution utilities
│   ├── file_utils.py: ✅ Golden file path management
│   └── comparison_utils.py: ✅ Energy data comparison utilities
├── Code Deduplication: ✅ COMPLETE (200+ lines of duplicated code removed)
├── Import System: ✅ ALL imports working correctly
└── Syntax Validation: ✅ NO errors in refactored code

Test Status:
├── Unit Tests: ✅ PASS (2/2 tests)
│   ├── test_validate_baseline_summary: ✅ PASS
│   └── test_validate_error_logs: ✅ PASS
├── test_generate_baseline.py: ✅ PASS (Protected with safety system)
└── test_energy_comparison.py: ⚠️ NEEDS GOLDEN FILE UPDATE
    ├── SQL Extraction: ✅ IMPROVED (finding 77 values vs 24 previously)
    ├── Database Compatibility: ✅ FIXED (TabularData joins working)
    ├── Current vs Baseline: ❌ MISMATCH (old baseline vs improved extraction)
    └── Comparison Logic: ✅ WORKING (all comparisons processing correctly)

Golden File Status:
├── Current Baseline: ⚠️ OUTDATED (generated with old extraction method)
├── New Extraction: ✅ WORKING (finding comprehensive energy data)
├── Update Required: ⚠️ YES (baseline regeneration needed)
└── Safety System: ✅ FULLY OPERATIONAL

Key Achievements:
├── ✅ Code deduplication objective: FULLY ACCOMPLISHED
├── ✅ Shared utilities: ALL 4 modules working correctly
├── ✅ SQL extraction: IMPROVED and database-compatible
├── ✅ Test framework: ROBUST with safety protections
└── ⚠️ Golden files: READY for regeneration with improved data
```

### 🔧 How to Run Tests

#### Run All Tests
```bash
python -m pytest
```

#### Update Golden Files (After Code Improvements)
```bash
# 🚨 IMPORTANT: Only run this when you want to update baseline files
# This will overwrite existing golden files with improved extraction data

python -m pytest tests/integration/test_generate_baseline.py --run-baseline -v -s

# The system will:
# 1. Show safety warnings
# 2. Create automatic backups of existing files
# 3. Prompt for confirmation (type 'YES' to proceed)
# 4. Generate new baseline files with comprehensive energy data
```

#### Run Specific Tests
```bash
# Generate new baseline (only when code is stable)
python -m pytest tests/integration/test_generate_baseline.py -v -s

# Run energy comparison against baseline
python -m pytest tests/integration/test_energy_comparison.py -v -s
```

#### Run with Verbose Output
```bash
python -m pytest -v -s
```

### 📋 Pending Items
- [ ] **Directory Reorganization**: ✅ COMPLETED
  - Created `tests/temp/` for all temporary simulation outputs
  - Added temp folder to .gitignore (treat as temporary)
  - Updated tests to use centralized temp directory structure
  - Benefits: Clean repository with only golden files version controlled, reproducible outputs
- [ ] **Golden File Regeneration**: Update baseline files with improved SQL extraction
  - Current baseline files use old extraction method (finding ~24 energy values)
  - New extraction method finds comprehensive data (~77 energy values per simulation)
  - Command: `python -m pytest tests/integration/test_generate_baseline.py --run-baseline -v -s`
  - Status: Ready to run - all safety protections in place
- [ ] Parallel execution configuration with `pytest-xdist`
- [ ] Markdown summary report generation
- [x] Error file validation (`eplusout.err` checking) - ✅ Implemented in unit tests
- [ ] Additional workflow step validation (HPXML, OSM, IDF file presence)
- [x] Unit tests for individual components - ✅ Implemented validation tests
- [x] Golden file safety protections - ✅ Multi-layer safety system implemented
- [x] Directory organization - ✅ golden_files structure implemented
- [x] Individual file structure - ✅ Separate JSON files per simulation
- [x] Common utilities module - ✅ Shared test utilities to reduce code duplication

### 🔒 Golden File Protection

The baseline generation test has multiple safety measures to prevent accidental overwrites:

1. **Pytest Mark**: Test is marked with `@pytest.mark.baseline_generation` and skipped by default
2. **Custom Flag**: Requires explicit `--run-baseline` command line flag
3. **Interactive Confirmation**: Prompts user to type 'yes' before proceeding
4. **Automatic Backup**: Creates timestamped backup of existing golden files
5. **Clear Warnings**: Documentation and prompts clearly indicate the danger
6. **Directory Organization**: Protected golden files in dedicated `golden_files/` structure

### 📁 Version Control Best Practices

#### Recommended .gitignore Configuration
```gitignore
# Test temporary outputs (regenerated each test run)
tests/temp/
tests/fixtures/expected_outputs/.pytest_cache/
tests/fixtures/expected_outputs/golden_files/comparison/

# Transitory report files (regenerated each test run)
tests/fixtures/expected_outputs/energy_comparison_report.json
tests/fixtures/expected_outputs/processing_results.md

# Keep only golden baseline files under version control
# All simulation outputs and comparison results are regenerated during test runs
```

#### Directory Classification
- **🔒 PERMANENT (Version Controlled)**:
  - `golden_files/baseline/*.json` - Reference energy data for regression testing
  - `golden_files/backup_*/` - Safety backups of golden files
  - `README.md` - Documentation

- **🗑️ TEMPORARY (Gitignored - Regenerated Each Test Run)**:
  - `tests/temp/` - **All simulation outputs and test runs**
    - `WizardHouse*/` - Baseline generation simulation outputs
    - `comparison_runs/` - Comparison test simulation outputs  
    - Contains `eplusout.sql`, `eplusout.err`, HPXML files
    - Regenerated during every test execution
    - No need to version control since they're derived from golden files
  - `golden_files/comparison/` - **Test comparison results**
    - `comparison_*.json` - Individual comparison reports
    - `comparison_energy_summary.json` - Comparison results index
    - Regenerated each time tests run
  - `energy_comparison_report.json` - Regenerated report files
  - `processing_results.md` - Transitory processing logs
  - `.pytest_cache/` - Pytest temporary files

#### Benefits of This Organization
- **Clean Repository**: Only essential golden files are version controlled
- **Centralized Temporary Files**: All simulation outputs in dedicated `tests/temp/` folder
- **Clear Separation**: Golden files (permanent) vs simulation outputs (temporary)
- **Reproducible**: All simulation outputs can be regenerated from stable code + golden files
- **Easy Cleanup**: Single temp folder can be deleted to clean all temporary files

**Safe Commands** (will NOT overwrite golden files):
```bash
python -m pytest                                    # Normal test run
python -m pytest tests/integration/                 # Integration tests only  
python -m pytest tests/integration/test_generate_baseline.py  # Skipped by default
```

**Dangerous Commands** (WILL overwrite golden files):
```bash
python -m pytest tests/integration/test_generate_baseline.py --run-baseline
```

**Safety Features**:
- **Multi-layer Protection**: Multiple independent safety mechanisms
- **Explicit Intent Required**: Must use `--run-baseline` flag
- **User Confirmation**: Interactive prompts prevent accidents
- **Automatic Backups**: Timestamped backups in `golden_files/backup_*/`
- **Clear Documentation**: Comprehensive safety documentation available
- **Test Validation**: Unit tests verify golden file integrity

See `docs/golden_files_safety.md` for complete safety documentation.

**Dangerous Commands** (WILL overwrite golden files):
```bash
python -m pytest tests/integration/test_generate_baseline.py --run-baseline
```

### 📚 Quick Reference

#### Key Files
- **Main Tests**: `tests/integration/test_generate_baseline.py`, `tests/integration/test_energy_comparison.py`
- **Unit Tests**: `tests/unit/test_validate_eplusout_sql.py` (golden file validation)
- **Common Utilities**: `tests/utils/` (shared functions to reduce code duplication)
  - `sql_utils.py`: SQL data extraction and database utilities
  - `workflow_utils.py`: H2K workflow execution and file management
  - `file_utils.py`: Golden file path management and JSON operations
  - `comparison_utils.py`: Energy data comparison and report generation
- **Safety Configuration**: `tests/conftest.py` (pytest safety controls)
- **Golden Files**: 
  - Baseline Data: `tests/fixtures/expected_outputs/golden_files/baseline/*.json`
  - Comparison Results: `tests/fixtures/expected_outputs/golden_files/comparison/*.json`
  - Safety Backups: `tests/fixtures/expected_outputs/golden_files/backup_*/`
  - Summary Files: 
    - `golden_files/baseline/baseline_energy_summary.json`
    - `golden_files/comparison/comparison_energy_summary.json`
- **Documentation**: `docs/golden_files_safety.md` (comprehensive safety guide), `docs/test_utilities.md` (common utilities documentation)

#### Test Commands
```bash
# Full test suite (excludes baseline generation)
python -m pytest

# 🔧 REGENERATE GOLDEN FILES (after code improvements)
# Only run this with verified stable code
python -m pytest tests/integration/test_generate_baseline.py --run-baseline -v -s
# ⚠️ This will prompt for confirmation and create automatic backups

# Run energy comparison against baseline (safe)
python -m pytest tests/integration/test_energy_comparison.py -v -s

# Run specific tests with markers
python -m pytest -m "not baseline_generation" -v    # Skip baseline generation
python -m pytest -m "baseline_generation" --run-baseline -v  # Run only baseline generation

# Test shared utilities import (verification)
python -c "from tests.utils import extract_annual_energy_data, compare_energy_values; print('✅ All utilities working')"
```

#### Safety Measures for Golden Files
```bash
# ⚠️  PROTECTED: These commands will NOT overwrite golden files
python -m pytest                                    # Skips baseline generation
python -m pytest tests/integration/                 # Skips baseline generation  
python -m pytest tests/integration/test_generate_baseline.py  # Skipped by default
python -m pytest tests/unit/                        # Unit tests (safe validation)

# ✅ SAFE: This only runs comparison tests
python -m pytest tests/integration/test_energy_comparison.py

# 🚨 DANGER: These commands WILL overwrite golden files
python -m pytest tests/integration/test_generate_baseline.py --run-baseline
python -m pytest --run-baseline  # Runs all tests including baseline generation

# 📚 DOCUMENTATION: Review safety measures
cat docs/golden_files_safety.md
```

#### Protection Features
- **Pytest Markers**: `@pytest.mark.baseline_generation` for identification
- **Command Flags**: `--run-baseline` required for dangerous operations
- **Interactive Prompts**: User must type 'yes' to confirm
- **Automatic Backups**: Timestamped backups before any changes
- **Directory Structure**: Protected `golden_files/` organization
- **Unit Test Validation**: Integrity checks for golden files

#### Success Metrics
- **Code Deduplication**: ✅ COMPLETED - 200+ lines of duplicated code eliminated
- **Shared Utilities**: ✅ WORKING - All 4 utility modules functional and tested
- **SQL Extraction**: ✅ IMPROVED - Enhanced database compatibility and data comprehensiveness
- **Import System**: ✅ VALIDATED - All shared utilities import correctly
- **Test Framework**: ✅ ROBUST - Full safety protections and error handling
- **Golden File Update**: ⚠️ READY - Improved extraction ready for baseline regeneration
- **Data Quality**: ✅ ENHANCED - Finding 77 energy values vs 24 previously (220% improvement)
- **File Structure**: ✅ OPTIMAL - Individual files + compact summaries for scalability
- **Safety System**: ✅ OPERATIONAL - Multi-layer protection against accidental overwrites

